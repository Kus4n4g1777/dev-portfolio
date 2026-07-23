import os
import json
import requests
from langchain_core.tools import tool
from typing import List, Dict, Optional

# ── Tool 1: Get low confidence detections ─────────────────────────────────────
# Queries the database for detections below a confidence threshold.
# Currently returns mock data — real PostgreSQL query coming next.

@tool
def get_low_confidence_detections(threshold: float = 0.5) -> List[Dict]:
    """
    Query the database for object detections with confidence score
    lower than the provided threshold. Returns a list of detections
    with their id, object type, and confidence score.
    Use this when the user asks about low confidence detections,
    uncertain detections, or wants to review detection quality.
    """
    print(f"Querying DB for detections with confidence < {threshold}")

    # Mock data — real SQLAlchemy query will replace this
    return [
        {"id": 101, "object": "person", "confidence": 0.42},
        {"id": 102, "object": "vehicle", "confidence": 0.35}
    ]


# ── Tool 2: Load sprint file and create GitHub issues ─────────────────────────
# This is the key tool for the demo — reads sprint-03.json automatically
# and creates all GitHub issues without requiring the user to paste JSON.

@tool
def load_sprint_and_create_issues(sprint_number: int = 3) -> Dict:
    """
    Load a sprint task file from disk and create all GitHub issues
    defined in it. The sprint file is loaded automatically from the
    tasks directory — no JSON payload required from the user.

    Use this when the user says things like:
    - 'Create the weekly issues for sprint 3'
    - 'Load sprint 3 and create the issues'
    - 'Set up this week's GitHub issues'

    Args:
        sprint_number: The sprint/iteration number (default: 3)

    Returns a summary of created issues with their GitHub URLs.
    """
    # Build the path to the sprint file
    # The tasks folder lives at /app/scripts/tasks/ inside the container
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sprint_file = os.path.join(base_dir, "scripts", "tasks", f"sprint-0{sprint_number}.json")

    print(f"Loading sprint file: {sprint_file}")

    # Load the sprint JSON
    if not os.path.exists(sprint_file):
        return {
            "status": "error",
            "message": f"Sprint file not found: sprint-0{sprint_number}.json. "
                       f"Available files should be in /app/scripts/tasks/"
        }

    with open(sprint_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    sprint_name = payload.get("sprint", f"Sprint {sprint_number}")
    issues_list = payload.get("issues", [])

    print(f"Loaded {len(issues_list)} issues for {sprint_name}")

    # GitHub API setup — token lives in env, never in graph state
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "Kus4n4g1777/dev-portfolio")

    if not token:
        return {
            "status": "error",
            "message": "GITHUB_TOKEN environment variable is not set. Cannot create issues."
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    url = f"https://api.github.com/repos/{repo}/issues"
    created_issues = []
    errors = []

    for issue in issues_list:
        # Build labels dynamically — same logic as the bash script
        labels = list(issue.get("labels", []))
        if sprint_name:
            labels.append(sprint_name)
        if issue.get("type"):
            labels.append(f"Type: {issue['type']}")
        if issue.get("epic"):
            labels.append(f"Epic: {issue['epic']}")
        if issue.get("storyPoints") is not None:
            labels.append(f"SP: {issue['storyPoints']}")

        data = {
            "title": issue.get("title", "Untitled Issue"),
            "body": issue.get("body", ""),
            "labels": labels,
            "assignees": issue.get("assignees", [])
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            url_created = response.json().get("html_url")
            created_issues.append(url_created)
            print(f"  ✅ Created: {data['title']}")
        else:
            error_msg = f"Failed '{data['title']}': {response.status_code}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")

    return {
        "status": "ok" if not errors else "partial_error",
        "sprint": sprint_name,
        "total_issues_in_file": len(issues_list),
        "total_created": len(created_issues),
        "issues_urls": created_issues,
        "errors": errors,
        "summary": (
            f"Successfully created {len(created_issues)} of {len(issues_list)} "
            f"issues for {sprint_name} in {repo}."
            + (f" {len(errors)} failed." if errors else "")
        )
    }


# ── Tool 3: Create issues from explicit payload (kept for flexibility) ─────────
# Used when the user provides a custom JSON payload directly.

@tool
def create_weekly_issues(payload: Dict) -> Dict:
    """
    Create GitHub issues from an explicit JSON payload provided by the user.
    Use this when the user provides specific issue details directly.
    For loading from a sprint file, use load_sprint_and_create_issues instead.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "Kus4n4g1777/dev-portfolio")

    if not token:
        return {"status": "error", "message": "GITHUB_TOKEN not set"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    url = f"https://api.github.com/repos/{repo}/issues"
    sprint = payload.get("sprint", "")
    created_issues = []
    errors = []

    for issue in payload.get("issues", []):
        labels = list(issue.get("labels", []))
        if sprint: labels.append(sprint)
        if issue.get("type"): labels.append(f"Type: {issue['type']}")
        if issue.get("epic"): labels.append(f"Epic: {issue['epic']}")
        if issue.get("storyPoints") is not None: labels.append(f"SP: {issue['storyPoints']}")

        data = {
            "title": issue.get("title", "Untitled Issue"),
            "body": issue.get("body", ""),
            "labels": labels,
            "assignees": issue.get("assignees", [])
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            created_issues.append(response.json().get("html_url"))
        else:
            errors.append(f"Failed '{data['title']}': {response.status_code} - {response.text}")

    return {
        "status": "ok" if not errors else "partial_error",
        "total_created": len(created_issues),
        "issues_urls": created_issues,
        "errors": errors
    }


# ── Register all tools ─────────────────────────────────────────────────────────
tools = [
    get_low_confidence_detections,
    load_sprint_and_create_issues,
    create_weekly_issues,
]

from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)

import os
import requests
from langchain_core.tools import tool
from typing import List, Dict

# We define our tools here. 
# Each function decorated with @tool will be automatically detected by the Agent.

@tool
def get_low_confidence_detections(threshold: float = 0.5) -> List[Dict]:
    """
    We use this tool to query the database for object detections 
    with a confidence score lower than the provided threshold.
    """
    # Here, we will implement the actual SQL/SQLAlchemy query logic later.
    # For now, we return a mock result so we can test the graph flow.
    print(f"We are querying the DB for detections with confidence < {threshold}")
    
    return [
        {"id": 101, "object": "person", "confidence": 0.42},
        {"id": 102, "object": "vehicle", "confidence": 0.35}
    ]

@tool
def create_weekly_issues(payload: Dict) -> Dict:
    """
    Create a batch of GitHub issues directly using the GitHub API
    from a JSON payload.
    """
    token = os.environ.get("GITHUB_TOKEN")
    # Add user / repo
    repo = os.environ.get("GITHUB_REPOSITORY", "Kus4n4g1777/dev-portfolio") 

    if not token:
        raise RuntimeError("GITHUB_TOKEN env var is required")

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
        # 1. Build tags dinamically as done before with bash
        labels = issue.get("labels", [])
        if sprint: labels.append(sprint)
        if issue.get("type"): labels.append(f"Type: {issue['type']}")
        if issue.get("epic"): labels.append(f"Epic: {issue['epic']}")
        if issue.get("storyPoints") is not None: labels.append(f"SP: {issue['storyPoints']}")

        # 2. Build the payload for GitHub API
        data = {
            "title": issue.get("title", "Untitled Issue"),
            "body": issue.get("body", ""),
            "labels": labels,
            "assignees": issue.get("assignees", [])
        }

        # 3. Make the POST request
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            # 201 Created
            created_issues.append(response.json().get("html_url"))
        else:
            errors.append(f"Failed on '{data['title']}': {response.status_code} - {response.text}")

    return {
        "status": "ok" if not errors else "partial_error",
        "total_created": len(created_issues),
        "issues_urls": created_issues,
        "errors": errors
    }

# We group our tools into a list to be bound to the LLM
tools = [get_low_confidence_detections, create_weekly_issues]

# We create the ToolNode that LangGraph uses to execute the tools
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)

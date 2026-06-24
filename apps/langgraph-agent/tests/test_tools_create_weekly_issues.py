import json
import pytest
from app.tools import create_weekly_issues

# We use a dummy class to simulate the response from the GitHub API.
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code
        self.text = "Mock error text"

    def json(self):
        return self._json_data

def test_create_weekly_issues_via_api(monkeypatch):
    """
    We verify that our tool correctly transforms the payload
    and makes a POST request to the GitHub API for each issue.
    """
    # We set up a minimal payload to test our tool.
    payload = {
        "sprint": "Iteration 3",
        "issues": [
            {
                "title": "HEALTH-42: Test issue",
                "body": "Test body",
                "type": "Story",
                "epic": "EPIC-HEALTH-1",
                "storyPoints": 2,
                "labels": ["HEALTH"],
                "assignees": ["Kus4n4g1777"]
            }
        ]
    }

    # We intercept the requests to capture what we are sending.
    post_calls = []

    def mock_post(url, headers, json):
        # We store the call data so we can assert on it later.
        post_calls.append({"url": url, "headers": headers, "json": json})
        # We simulate a successfully created issue.
        return MockResponse({"html_url": "https://github.com/Kus4n4g1777/dev-portfolio/issues/99"}, 201)

    # We patch the requests module inside our test scope.
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    
    # We inject our environment variables so the tool doesn't fail.
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Kus4n4g1777/test-repo")

    # We execute our tool with the mocked environment.
    result = create_weekly_issues.invoke({"payload": payload})

    # We verify that our returned status and data match our expectations.
    assert result["status"] == "ok"
    assert result["total_created"] == 1
    assert "https://github.com/Kus4n4g1777/dev-portfolio/issues/99" in result["issues_urls"]

    # We check that we actually made the exact request we expected.
    assert len(post_calls) == 1
    call_data = post_calls[0]
    
    assert call_data["url"] == "https://api.github.com/repos/Kus4n4g1777/test-repo/issues"
    assert call_data["headers"]["Authorization"] == "Bearer dummy-token"
    
    # We validate that we concatenated the labels correctly.
    sent_labels = call_data["json"]["labels"]
    assert "Iteration 3" in sent_labels
    assert "Type: Story" in sent_labels
    assert "Epic: EPIC-HEALTH-1" in sent_labels
    assert "SP: 2" in sent_labels

"""Pytest configuration and shared fixtures."""

import pytest
from datetime import datetime
from mcp_server_standup.github import GitHubActivity, GitHubEvent


@pytest.fixture
def sample_github_event():
    """Create a sample GitHub event for testing."""
    return GitHubEvent(
        event_type="PushEvent",
        created_at="2024-07-23T10:00:00Z",
        repo="test_org/repo1",
        actor="testuser",
        payload={
            "ref": "refs/heads/main",
            "size": 1,
            "commits": [
                {
                    "message": "Test commit",
                    "sha": "abc123def456",
                }
            ],
        },
        processed_info={
            "branch": "main",
            "commit_count": 1,
            "commits": [
                {
                    "message": "Test commit",
                    "sha": "abc123d",
                    "full_sha": "abc123def456",
                    "link": "https://github.com/test_org/repo1/commit/abc123def456",
                }
            ],
            "links": ["https://github.com/test_org/repo1/tree/main"],
            "details": ["Pushed 1 commits to main"],
        },
    )


@pytest.fixture
def sample_github_activity(sample_github_event):
    """Create a sample GitHub activity for testing."""
    return GitHubActivity(
        target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
        username="testuser",
        repos=["test_org/repo1"],
        events=[sample_github_event],
        summary={
            "total_events": 1,
            "event_types": {"PushEvent": 1},
            "repositories": ["test_org/repo1"],
            "commit_count": 1,
            "pr_count": 0,
        },
    )


@pytest.fixture
def sample_pr_event():
    """Create a sample pull request event for testing."""
    return GitHubEvent(
        event_type="PullRequestEvent",
        created_at="2024-07-23T11:00:00Z",
        repo="test_org/repo1",
        actor="testuser",
        payload={
            "action": "opened",
            "pull_request": {"number": 123, "title": "Add new feature"},
        },
        processed_info={
            "pr_number": 123,
            "action": "opened",
            "title": "Add new feature",
            "links": ["https://github.com/test_org/repo1/pull/123"],
            "details": ["PR #123: opened - Add new feature"],
        },
    )


@pytest.fixture
def sample_review_event():
    """Create a sample review event for testing."""
    return GitHubEvent(
        event_type="PullRequestReviewEvent",
        created_at="2024-07-23T12:00:00Z",
        repo="test_org/repo1",
        actor="testuser",
        payload={"pull_request": {"number": 456}, "review": {"state": "approved"}},
        processed_info={
            "pr_number": 456,
            "review_state": "approved",
            "links": ["https://github.com/test_org/repo1/pull/456"],
            "details": ["Reviewed PR #456: approved"],
        },
    )

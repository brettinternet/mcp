"""Tests for GitHub service module."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import subprocess

from mcp_server_standup.github import GitHubService, GitHubEvent, GitHubActivity


class TestGitHubService:
    """Test the GitHubService class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("subprocess.run") as mock_run:
            # Mock the gh --version check during initialization
            mock_run.return_value = Mock(returncode=0)
            self.service = GitHubService()
            self.service.github_org = "test_org"

    def test_init_without_env_vars(self):
        """Test initialization without environment variables."""
        with patch.dict("os.environ", {}, clear=True), patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            service = GitHubService()
            assert service.github_org is None
            assert service.github_repos is None

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(
            "os.environ", {"GITHUB_ORG": "test_org", "GITHUB_REPOS": "test_org/repo1,test_org/repo2"}
        ), patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            service = GitHubService()
            assert service.github_org == "test_org"
            assert service.github_repos == "test_org/repo1,test_org/repo2"


    def test_matches_username(self):
        """Test username matching logic."""
        assert self.service._matches_username("testuser", "testuser")
        assert self.service._matches_username("TestUser", "testuser")
        assert self.service._matches_username("testuser", "TestUser")
        assert not self.service._matches_username("testuser", "otheruser")
        assert not self.service._matches_username("", "testuser")

    @pytest.mark.asyncio
    async def test_get_activity_with_repos(self):
        """Test get_activity with specific repositories."""
        target_date = datetime(2024, 7, 23, 0, 0, 0, 0)
        repos = ["test_org/repo1", "test_org/repo2"]

        mock_events = [
            {
                "type": "PushEvent",
                "created_at": "2024-07-23T10:00:00Z",
                "actor": {"login": "testuser"},
                "payload": {
                    "ref": "refs/heads/main",
                    "size": 1,
                    "commits": [
                        {
                            "message": "Test commit",
                            "sha": "abc123def456",
                        }
                    ],
                },
            }
        ]

        with patch.object(
            self.service, "_get_repo_events", new_callable=AsyncMock
        ) as mock_get_events:
            mock_get_events.return_value = [
                GitHubEvent(
                    event_type="PushEvent",
                    created_at="2024-07-23T10:00:00Z",
                    repo="test_org/repo1",
                    actor="testuser",
                    payload=mock_events[0]["payload"],
                    processed_info={
                        "commits": [{"message": "Test commit", "sha": "abc123d"}]
                    },
                )
            ]

            activity = await self.service.get_activity(
                target_date=target_date, username="testuser", repos=repos
            )

            assert isinstance(activity, GitHubActivity)
            assert activity.target_date == target_date
            assert activity.username == "testuser"
            assert activity.repos == repos
            assert len(activity.events) == 2  # Called for each repo
            assert mock_get_events.call_count == 2

    @pytest.mark.asyncio
    async def test_get_activity_with_org_repos(self):
        """Test get_activity with organization repositories."""
        target_date = datetime(2024, 7, 23, 0, 0, 0, 0)

        with patch.object(
            self.service, "_get_org_repos", new_callable=AsyncMock
        ) as mock_get_org_repos:
            with patch.object(
                self.service, "_get_repo_events", new_callable=AsyncMock
            ) as mock_get_events:
                mock_get_org_repos.return_value = ["test_org/repo1", "test_org/repo2"]
                mock_get_events.return_value = []

                activity = await self.service.get_activity(
                    target_date=target_date, username="testuser"
                )

                assert isinstance(activity, GitHubActivity)
                mock_get_org_repos.assert_called_once()
                assert mock_get_events.call_count == 2

    @pytest.mark.asyncio
    async def test_get_activity_without_org_raises_error(self):
        """Test get_activity without org and repos raises error."""
        target_date = datetime(2024, 7, 23, 0, 0, 0, 0)
        service = GitHubService()
        service.github_org = None

        with pytest.raises(
            ValueError, match="GITHUB_ORG environment variable is required"
        ):
            await service.get_activity(target_date=target_date)

    @pytest.mark.asyncio
    async def test_get_org_repos_success(self):
        """Test successful organization repository fetching."""
        mock_response_data = [
            {"full_name": "test_org/repo1"},
            {"full_name": "test_org/repo2"},
        ]

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            repos = await self.service._get_org_repos()

            assert repos == ["test_org/repo1", "test_org/repo2"]
            mock_client.return_value.__aenter__.return_value.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_org_repos_pagination(self):
        """Test organization repository fetching with pagination."""
        # First page
        mock_response_1 = Mock()
        mock_response_1.json.return_value = [
            {"full_name": f"test_org/repo{i}"} for i in range(100)
        ]
        mock_response_1.raise_for_status.return_value = None

        # Second page (partial)
        mock_response_2 = Mock()
        mock_response_2.json.return_value = [{"full_name": "test_org/repo100"}]
        mock_response_2.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_1, mock_response_2]
            )

            repos = await self.service._get_org_repos()

            assert len(repos) == 101
            assert repos[0] == "test_org/repo0"
            assert repos[-1] == "test_org/repo100"
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_org_repos_http_error(self):
        """Test organization repository fetching with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("API Error")
            )

            repos = await self.service._get_org_repos()

            assert repos == []

    @pytest.mark.asyncio
    async def test_get_repo_events_success(self):
        """Test successful repository event fetching."""
        repo = "test_org/repo1"
        username = "testuser"
        start_time = "2024-07-23T00:00:00Z"
        end_time = "2024-07-24T07:59:59Z"

        mock_events_data = [
            {
                "type": "PushEvent",
                "created_at": "2024-07-23T10:00:00Z",
                "actor": {"login": "testuser"},
                "payload": {
                    "ref": "refs/heads/main",
                    "size": 1,
                    "commits": [
                        {
                            "message": "Test commit",
                            "sha": "abc123def456",
                        }
                    ],
                },
            }
        ]

        mock_response = Mock()
        mock_response.json.return_value = mock_events_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            events = await self.service._get_repo_events(
                repo, username, start_time, end_time
            )

            assert len(events) == 1
            assert isinstance(events[0], GitHubEvent)
            assert events[0].event_type == "PushEvent"
            assert events[0].repo == repo
            assert events[0].actor == "testuser"

    @pytest.mark.asyncio
    async def test_get_repo_events_filters_by_date(self):
        """Test repository event fetching filters by date range."""
        repo = "test_org/repo1"
        username = ""
        start_time = "2024-07-23T00:00:00Z"
        end_time = "2024-07-24T07:59:59Z"

        mock_events_data = [
            {
                "type": "PushEvent",
                "created_at": "2024-07-23T10:00:00Z",  # Within range
                "actor": {"login": "testuser"},
                "payload": {},
            },
            {
                "type": "PushEvent",
                "created_at": "2024-07-22T10:00:00Z",  # Before range
                "actor": {"login": "testuser"},
                "payload": {},
            },
            {
                "type": "PushEvent",
                "created_at": "2024-07-25T10:00:00Z",  # After range
                "actor": {"login": "testuser"},
                "payload": {},
            },
        ]

        mock_response = Mock()
        mock_response.json.return_value = mock_events_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            events = await self.service._get_repo_events(
                repo, username, start_time, end_time
            )

            assert len(events) == 1
            assert events[0].created_at == "2024-07-23T10:00:00Z"

    @pytest.mark.asyncio
    async def test_get_repo_events_filters_by_username(self):
        """Test repository event fetching filters by username."""
        repo = "test_org/repo1"
        username = "targetuser"
        start_time = "2024-07-23T00:00:00Z"
        end_time = "2024-07-24T07:59:59Z"

        mock_events_data = [
            {
                "type": "PushEvent",
                "created_at": "2024-07-23T10:00:00Z",
                "actor": {"login": "targetuser"},  # Matches
                "payload": {},
            },
            {
                "type": "PushEvent",
                "created_at": "2024-07-23T11:00:00Z",
                "actor": {"login": "otheruser"},  # Doesn't match
                "payload": {},
            },
        ]

        mock_response = Mock()
        mock_response.json.return_value = mock_events_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            events = await self.service._get_repo_events(
                repo, username, start_time, end_time
            )

            assert len(events) == 1
            assert events[0].actor == "targetuser"

    def test_process_push_event(self):
        """Test processing of push events."""
        event = GitHubEvent(
            event_type="PushEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={
                "ref": "refs/heads/main",
                "size": 2,
                "commits": [
                    {"message": "First commit", "sha": "abc123def456"},
                    {"message": "Second commit", "sha": "def456ghi789"},
                ],
            },
        )

        processed = self.service._process_push_event(event)

        assert processed["branch"] == "main"
        assert processed["commit_count"] == 2
        assert len(processed["commits"]) == 2
        assert processed["commits"][0]["message"] == "First commit"
        assert processed["commits"][0]["sha"] == "abc123d"
        assert "https://github.com/test_org/repo1/tree/main" in processed["links"]

    def test_process_pr_event(self):
        """Test processing of pull request events."""
        event = GitHubEvent(
            event_type="PullRequestEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={
                "action": "opened",
                "pull_request": {"number": 123, "title": "Add new feature"},
            },
        )

        processed = self.service._process_pr_event(event)

        assert processed["pr_number"] == 123
        assert processed["action"] == "opened"
        assert processed["title"] == "Add new feature"
        assert "https://github.com/test_org/repo1/pull/123" in processed["links"]

    def test_process_comment_event(self):
        """Test processing of comment events."""
        event = GitHubEvent(
            event_type="IssueCommentEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={
                "issue": {
                    "number": 456,
                    "pull_request": {
                        "url": "https://api.github.com/repos/test_org/repo1/pulls/456"
                    },
                }
            },
        )

        processed = self.service._process_comment_event(event)

        assert processed["issue_number"] == 456
        assert processed["is_pull_request"] is True
        assert "https://github.com/test_org/repo1/pull/456" in processed["links"]

    def test_process_review_event(self):
        """Test processing of review events."""
        event = GitHubEvent(
            event_type="PullRequestReviewEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={"pull_request": {"number": 789}, "review": {"state": "approved"}},
        )

        processed = self.service._process_review_event(event)

        assert processed["pr_number"] == 789
        assert processed["review_state"] == "approved"
        assert "https://github.com/test_org/repo1/pull/789" in processed["links"]

    def test_process_ref_event_create(self):
        """Test processing of create events."""
        event = GitHubEvent(
            event_type="CreateEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={"ref_type": "branch", "ref": "feature-branch"},
        )

        processed = self.service._process_ref_event(event)

        assert processed["ref_type"] == "branch"
        assert processed["ref"] == "feature-branch"
        assert processed["action"] == "created"

    def test_commit_deduplication(self):
        """Test that commits are deduplicated properly."""
        # Process first event
        event1 = GitHubEvent(
            event_type="PushEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={
                "ref": "refs/heads/main",
                "size": 1,
                "commits": [{"message": "Test commit", "sha": "abc123def456"}],
            },
        )

        processed1 = self.service._process_push_event(event1)

        # Process second event with same commit message (force push scenario)
        event2 = GitHubEvent(
            event_type="PushEvent",
            created_at="2024-07-23T11:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={
                "ref": "refs/heads/main",
                "size": 1,
                "commits": [{"message": "Test commit", "sha": "def456ghi789"}],
            },
        )

        processed2 = self.service._process_push_event(event2)

        # First event should have the commit
        assert len(processed1["commits"]) == 1
        # Second event should be filtered out due to deduplication
        assert len(processed2["commits"]) == 0

    def test_generate_summary(self):
        """Test summary generation."""
        events = [
            GitHubEvent(
                event_type="PushEvent",
                created_at="2024-07-23T10:00:00Z",
                repo="test_org/repo1",
                actor="testuser",
                payload={},
                processed_info={"commits": [{"message": "Test"}]},
            ),
            GitHubEvent(
                event_type="PullRequestEvent",
                created_at="2024-07-23T11:00:00Z",
                repo="test_org/repo2",
                actor="testuser",
                payload={},
                processed_info={},
            ),
        ]

        summary = self.service._generate_summary(events)

        assert summary["total_events"] == 2
        assert summary["event_types"]["PushEvent"] == 1
        assert summary["event_types"]["PullRequestEvent"] == 1
        assert "test_org/repo1" in summary["repositories"]
        assert "test_org/repo2" in summary["repositories"]
        assert summary["commit_count"] == 1
        assert summary["pr_count"] == 1

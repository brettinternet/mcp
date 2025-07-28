"""Tests for formatting module."""

import json
from datetime import datetime

from standup_server.formatting import StandupFormatter
from standup_server.github import GitHubActivity, GitHubEvent


class TestStandupFormatter:
    """Test the StandupFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = StandupFormatter()

        # Create sample GitHub activity data
        self.sample_events = [
            GitHubEvent(
                event_type="PushEvent",
                created_at="2024-07-23T10:00:00Z",
                repo="test_org/repo1",
                actor="testuser",
                payload={},
                processed_info={
                    "branch": "main",
                    "commit_count": 2,
                    "commits": [
                        {
                            "message": "Add new feature",
                            "sha": "abc123d",
                            "full_sha": "abc123def456",
                            "link": "https://github.com/test_org/repo1/commit/abc123def456",
                        },
                        {
                            "message": "Fix bug in feature",
                            "sha": "def456g",
                            "full_sha": "def456ghi789",
                            "link": "https://github.com/test_org/repo1/commit/def456ghi789",
                        },
                    ],
                    "links": ["https://github.com/test_org/repo1/tree/main"],
                    "details": ["Pushed 2 commits to main"],
                },
            ),
            GitHubEvent(
                event_type="PullRequestEvent",
                created_at="2024-07-23T11:00:00Z",
                repo="test_org/repo2",
                actor="testuser",
                payload={},
                processed_info={
                    "pr_number": 123,
                    "action": "opened",
                    "title": "Implement user authentication",
                    "links": ["https://github.com/test_org/repo2/pull/123"],
                    "details": ["PR #123: opened - Implement user authentication"],
                },
            ),
            GitHubEvent(
                event_type="PullRequestReviewEvent",
                created_at="2024-07-23T12:00:00Z",
                repo="test_org/repo3",
                actor="testuser",
                payload={},
                processed_info={
                    "pr_number": 456,
                    "review_state": "approved",
                    "links": ["https://github.com/test_org/repo3/pull/456"],
                    "details": ["Reviewed PR #456: approved"],
                },
            ),
        ]

        self.sample_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=self.sample_events,
            summary={
                "total_events": 3,
                "event_types": {
                    "PushEvent": 1,
                    "PullRequestEvent": 1,
                    "PullRequestReviewEvent": 1,
                },
                "repositories": ["test_org/repo1", "test_org/repo2", "test_org/repo3"],
                "commit_count": 2,
                "pr_count": 1,
            },
        )

    def test_format_standup_report_markdown(self):
        """Test formatting standup report in markdown format."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="markdown"
        )

        assert "# Standup Summary - July 23, 2024" in result
        assert (
            "- Made **2 commits** to [test_org/repo1](https://github.com/test_org/repo1)"
            in result
        )
        assert (
            "- Opened **[PR #123](https://github.com/test_org/repo2/pull/123)**: Implement user authentication"
            in result
        )
        assert (
            "- Reviewed **[PR #456](https://github.com/test_org/repo3/pull/456)** (approved)"
            in result
        )
        assert "## GitHub Activity Details" in result
        assert "**3 events** across **3 repositories**" in result

    def test_format_standup_report_text(self):
        """Test formatting standup report in text format."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="text"
        )

        assert "Standup Summary - July 23, 2024" in result
        assert "=" * 50 in result
        assert "Made 2 commits to test_org/repo1" in result
        assert "Opened PR #123: Implement user authentication" in result
        assert "Reviewed PR #456 (approved)" in result
        # Markdown links should be converted to plain text
        assert "[" not in result or "](" not in result

    def test_format_standup_report_json(self):
        """Test formatting standup report in JSON format."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="json"
        )

        data = json.loads(result)
        assert data["date"] == "2024-07-23T00:00:00"
        assert data["github"]["summary"]["total_events"] == 3
        assert len(data["github"]["events"]) == 3
        assert len(data["standup_items"]) > 0

        # Check event structure
        event = data["github"]["events"][0]
        assert event["type"] == "PushEvent"
        assert event["repo"] == "test_org/repo1"
        assert event["actor"] == "testuser"

    def test_format_github_activity_with_events(self):
        """Test formatting detailed GitHub activity with events."""
        result = self.formatter.format_github_activity(self.sample_activity)

        assert "# GitHub Activity for 2024-07-23" in result
        assert "**Summary:** 3 events across 3 repositories" in result
        assert "- **Commits:** 2" in result
        assert "- **Pull Requests:** 1" in result
        assert "## Detailed Activity" in result
        assert "### test_org/repo1" in result
        assert "### test_org/repo2" in result
        assert "### test_org/repo3" in result

    def test_format_github_activity_no_events(self):
        """Test formatting GitHub activity with no events."""
        empty_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        result = self.formatter.format_github_activity(empty_activity)
        assert "No GitHub activity found for 2024-07-23" in result

    def test_generate_standup_items(self):
        """Test generating standup items from activity."""
        items = self.formatter._generate_standup_items(self.sample_activity)

        # Should have items for commits, PRs, and reviews
        assert len(items) >= 3

        # Check for expected content
        commit_item = next((item for item in items if "commits" in item), None)
        assert commit_item is not None
        assert "test_org/repo1" in commit_item

        pr_item = next(
            (item for item in items if "Opened" in item and "PR #123" in item), None
        )
        assert pr_item is not None

        review_item = next(
            (item for item in items if "Reviewed" in item and "PR #456" in item), None
        )
        assert review_item is not None

    def test_group_significant_events(self):
        """Test grouping events by significance."""
        groups = self.formatter._group_significant_events(self.sample_events)

        assert "commits" in groups
        assert "pull_requests" in groups
        assert "reviews" in groups
        assert "other" in groups

        assert len(groups["commits"]) == 1
        assert len(groups["pull_requests"]) == 1
        assert len(groups["reviews"]) == 1
        assert len(groups["other"]) == 0

    def test_format_commit_items_single_commit(self):
        """Test formatting single commit item."""
        single_commit_event = GitHubEvent(
            event_type="PushEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={},
            processed_info={
                "commits": [
                    {
                        "message": "Single commit",
                        "sha": "abc123d",
                        "link": "https://github.com/test_org/repo1/commit/abc123def456",
                    }
                ]
            },
        )

        items = self.formatter._format_commit_items([single_commit_event])

        assert len(items) == 1
        assert "Committed **Single commit**" in items[0]
        assert "https://github.com/test_org/repo1/commit/abc123def456" in items[0]

    def test_format_commit_items_multiple_commits(self):
        """Test formatting multiple commit items."""
        items = self.formatter._format_commit_items([self.sample_events[0]])

        # Should summarize multiple commits
        assert any("Made **2 commits**" in item for item in items)
        assert any("Add new feature" in item for item in items)
        assert any("Fix bug in feature" in item for item in items)

    def test_format_pr_items(self):
        """Test formatting pull request items."""
        items = self.formatter._format_pr_items([self.sample_events[1]])

        assert len(items) == 1
        assert "Opened **[PR #123]" in items[0]
        assert "Implement user authentication" in items[0]
        assert "https://github.com/test_org/repo2/pull/123" in items[0]

    def test_format_review_items(self):
        """Test formatting review items."""
        items = self.formatter._format_review_items([self.sample_events[2]])

        assert len(items) == 1
        assert "Reviewed **[PR #456]" in items[0]
        assert "(approved)" in items[0]
        assert "https://github.com/test_org/repo3/pull/456" in items[0]

    def test_format_review_items_deduplication(self):
        """Test that multiple reviews for same PR are deduplicated."""
        review_events = [
            GitHubEvent(
                event_type="PullRequestReviewEvent",
                created_at="2024-07-23T10:00:00Z",
                repo="test_org/repo1",
                actor="testuser",
                payload={},
                processed_info={
                    "pr_number": 123,
                    "review_state": "commented",
                    "links": ["https://github.com/test_org/repo1/pull/123"],
                },
            ),
            GitHubEvent(
                event_type="PullRequestReviewEvent",
                created_at="2024-07-23T11:00:00Z",
                repo="test_org/repo1",
                actor="testuser",
                payload={},
                processed_info={
                    "pr_number": 123,
                    "review_state": "approved",
                    "links": ["https://github.com/test_org/repo1/pull/123"],
                },
            ),
        ]

        items = self.formatter._format_review_items(review_events)

        # Should only have one item (latest review)
        assert len(items) == 1
        assert "(approved)" in items[0]  # Should use latest state

    def test_format_other_items_comment(self):
        """Test formatting comment items."""
        comment_event = GitHubEvent(
            event_type="IssueCommentEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={},
            processed_info={
                "issue_number": 789,
                "is_pull_request": True,
                "links": ["https://github.com/test_org/repo1/pull/789"],
            },
        )

        items = self.formatter._format_other_items([comment_event])

        assert len(items) == 1
        assert "Commented on **[PR #789]" in items[0]
        assert "https://github.com/test_org/repo1/pull/789" in items[0]

    def test_format_other_items_branch_creation(self):
        """Test formatting branch creation items."""
        create_event = GitHubEvent(
            event_type="CreateEvent",
            created_at="2024-07-23T10:00:00Z",
            repo="test_org/repo1",
            actor="testuser",
            payload={},
            processed_info={
                "ref_type": "branch",
                "ref": "feature-branch",
                "action": "created",
            },
        )

        items = self.formatter._format_other_items([create_event])

        assert len(items) == 1
        assert "Created branch **feature-branch**" in items[0]
        assert "test_org/repo1" in items[0]

    def test_format_event_details(self):
        """Test formatting detailed event information."""
        event = self.sample_events[0]  # PushEvent

        lines = self.formatter._format_event_details(event)

        assert len(lines) > 0
        assert "**PushEvent** by testuser at 2024-07-23T10:00:00Z" in lines[0]

        # Should contain details, links, and commits
        detail_lines = [line for line in lines if line.startswith("- ")]
        assert len(detail_lines) > 0

    def test_empty_activity_generates_no_activity_message(self):
        """Test that empty activity generates appropriate message."""
        empty_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        result = self.formatter.format_standup_report(
            github_activity=empty_activity, format_type="markdown"
        )

        assert "No significant activity to report." in result

    def test_markdown_links_preserved_in_markdown_format(self):
        """Test that markdown links are preserved in markdown format."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="markdown"
        )

        # Should contain markdown links
        assert "[test_org/repo1](https://github.com/test_org/repo1)" in result
        assert "[PR #123](https://github.com/test_org/repo2/pull/123)" in result

    def test_markdown_links_removed_in_text_format(self):
        """Test that markdown links are converted to plain text in text format."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="text"
        )

        # Should not contain markdown link syntax
        assert "](https://" not in result
        # But should contain the text content
        assert "test_org/repo1" in result
        assert "PR #123" in result

    def test_commit_count_in_summary(self):
        """Test that commit count is properly tracked in summaries."""
        result = self.formatter.format_standup_report(
            github_activity=self.sample_activity, format_type="markdown"
        )

        # Check that the commit summary appears
        assert "Made **2 commits**" in result

    def test_multiple_repos_in_commit_summary(self):
        """Test handling of commits across multiple repositories."""
        # Create events with commits in different repos
        multi_repo_events = [
            GitHubEvent(
                event_type="PushEvent",
                created_at="2024-07-23T10:00:00Z",
                repo="test_org/repo1",
                actor="testuser",
                payload={},
                processed_info={
                    "commits": [
                        {
                            "message": "Commit in repo1",
                            "sha": "abc123d",
                            "link": "https://github.com/test_org/repo1/commit/abc123def456",
                        }
                    ]
                },
            ),
            GitHubEvent(
                event_type="PushEvent",
                created_at="2024-07-23T11:00:00Z",
                repo="test_org/repo2",
                actor="testuser",
                payload={},
                processed_info={
                    "commits": [
                        {
                            "message": "Commit in repo2",
                            "sha": "def456g",
                            "link": "https://github.com/test_org/repo2/commit/def456ghi789",
                        }
                    ]
                },
            ),
        ]

        activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=multi_repo_events,
            summary={
                "total_events": 2,
                "repositories": ["test_org/repo1", "test_org/repo2"],
                "commit_count": 2,
                "pr_count": 0,
            },
        )

        items = self.formatter._generate_standup_items(activity)

        # Should have separate items for each repo
        repo1_items = [item for item in items if "test_org/repo1" in item]
        repo2_items = [item for item in items if "test_org/repo2" in item]

        assert len(repo1_items) > 0
        assert len(repo2_items) > 0

"""GitHub API integration for fetching activity data."""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .utils import DateParser

logger = logging.getLogger(__name__)


@dataclass
class GitHubEvent:
    """Represents a GitHub event with processed information."""

    event_type: str
    created_at: str
    repo: str
    actor: str
    payload: Dict[str, Any]
    processed_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubActivity:
    """Container for GitHub activity data."""

    target_date: datetime
    username: Optional[str]
    repos: Optional[List[str]]
    events: List[GitHubEvent] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class GitHubService:
    """Service for fetching and processing GitHub activity."""

    def __init__(self):
        # Load .env file from project root
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up to project root
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded .env file from {env_path}")
        else:
            logger.debug(f"No .env file found at {env_path}")
        
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_org = os.getenv("GITHUB_ORG")
        self.date_parser = DateParser()
        self._seen_commits = set()  # For deduplication

    async def get_activity(
        self,
        target_date: datetime,
        username: Optional[str] = None,
        repos: Optional[List[str]] = None,
    ) -> GitHubActivity:
        """Get GitHub activity for the specified date and filters.

        Args:
            target_date: Date to get activity for
            username: Optional username filter
            repos: Optional list of repositories to check

        Returns:
            GitHubActivity object with all events and summary
        """
        self._seen_commits.clear()  # Reset for each request

        activity = GitHubActivity(
            target_date=target_date,
            username=username,
            repos=repos,
        )

        # Get UTC date range for API queries
        start_time, end_time = self.date_parser.get_utc_date_range(target_date)

        if repos:
            # Process specific repositories
            for repo in repos:
                repo = repo.strip()
                if repo:
                    events = await self._get_repo_events(
                        repo, username, start_time, end_time
                    )
                    activity.events.extend(events)
        else:
            # Try to get repositories from various sources
            repos_to_process = []
            
            if self.github_org:
                # Use org repositories
                repos_to_process = await self._get_org_repos()
            else:
                # Fall back to GITHUB_REPOS environment variable
                github_repos_env = os.getenv("GITHUB_REPOS")
                if github_repos_env:
                    repos_to_process = [repo.strip() for repo in github_repos_env.split(",") if repo.strip()]
                    logger.debug(f"Using repositories from GITHUB_REPOS: {repos_to_process}")
                else:
                    raise ValueError(
                        "Either GITHUB_ORG or GITHUB_REPOS environment variable is required when not specifying repos"
                    )

            for repo in repos_to_process:
                events = await self._get_repo_events(
                    repo, username, start_time, end_time
                )
                activity.events.extend(events)

        # Sort events by timestamp
        activity.events.sort(key=lambda x: x.created_at)

        # Generate summary
        activity.summary = self._generate_summary(activity.events)

        return activity

    async def _get_org_repos(self) -> List[str]:
        """Get all repositories for the configured organization."""
        repos = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.base_url}/orgs/{self.github_org}/repos"
                params = {"page": page, "per_page": per_page}
                headers = self._get_headers()

                try:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    if not data:
                        break

                    repos.extend([repo["full_name"] for repo in data])

                    if len(data) < per_page:
                        break

                    page += 1

                except httpx.HTTPError as e:
                    logger.error(f"Error fetching org repos: {e}")
                    break

        return repos

    async def _get_repo_events(
        self,
        repo: str,
        username: Optional[str],
        start_time: str,
        end_time: str,
    ) -> List[GitHubEvent]:
        """Get events for a specific repository within the date range."""
        events = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            while page <= 50:  # Safety limit
                url = f"{self.base_url}/repos/{repo}/events"
                params = {"page": page, "per_page": per_page}
                headers = self._get_headers()

                try:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    if not data:
                        break

                    # Filter events by date range and username
                    filtered_events = []
                    for event_data in data:
                        created_at = event_data.get("created_at", "")

                        # Check date range
                        if not (start_time <= created_at <= end_time):
                            # If we've gone past the start time, we can stop
                            if created_at < start_time:
                                # Add any filtered events before returning
                                events.extend(filtered_events)
                                return events
                            continue

                        # Check username filter
                        if username:
                            actor_login = event_data.get("actor", {}).get("login", "")
                            if not self._matches_username(actor_login, username):
                                continue

                        # Create GitHubEvent object
                        github_event = GitHubEvent(
                            event_type=event_data.get("type", ""),
                            created_at=created_at,
                            repo=repo,
                            actor=event_data.get("actor", {}).get("login", ""),
                            payload=event_data.get("payload", {}),
                        )

                        # Process the event for additional info
                        github_event.processed_info = self._process_event(github_event)
                        filtered_events.append(github_event)

                    events.extend(filtered_events)

                    # Check if we should continue pagination
                    if len(data) < per_page:
                        break

                    # Check if oldest event is before our range
                    if data and data[-1].get("created_at", "") < start_time:
                        break

                    page += 1

                except httpx.HTTPError as e:
                    logger.error(f"Error fetching events for {repo}: {e}")
                    break

        return events

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "mcp-standup-server/0.1.0",
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        return headers

    def _matches_username(self, actor_login: str, username: str) -> bool:
        """Check if actor login matches the username filter."""
        return actor_login.lower() == username.lower()

    def _process_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process a GitHub event to extract useful information."""
        processed = {
            "links": [],
            "details": [],
            "commits": [],
        }

        if event.event_type == "PushEvent":
            processed.update(self._process_push_event(event))
        elif event.event_type == "PullRequestEvent":
            processed.update(self._process_pr_event(event))
        elif event.event_type == "IssueCommentEvent":
            processed.update(self._process_comment_event(event))
        elif event.event_type == "PullRequestReviewEvent":
            processed.update(self._process_review_event(event))
        elif event.event_type in ["CreateEvent", "DeleteEvent"]:
            processed.update(self._process_ref_event(event))

        return processed

    def _process_push_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process a push event."""
        payload = event.payload
        ref = payload.get("ref", "")
        branch_name = ref.replace("refs/heads/", "")
        size = payload.get("size", 0)

        processed = {
            "branch": branch_name,
            "commit_count": size,
            "links": [f"https://github.com/{event.repo}/tree/{branch_name}"],
            "details": [f"Pushed {size} commits to {branch_name}"],
        }

        # Process commits with deduplication
        commits = payload.get("commits", [])
        unique_commits = []

        for commit in commits:
            message = commit.get("message", "").strip()
            sha = commit.get("sha", "")

            if not message or not sha:
                continue

            # Create deduplication key
            commit_key = message.lower().replace(" ", "_")

            if commit_key not in self._seen_commits:
                self._seen_commits.add(commit_key)
                unique_commits.append(
                    {
                        "message": message,
                        "sha": sha[:7],
                        "full_sha": sha,
                        "link": f"https://github.com/{event.repo}/commit/{sha}",
                    }
                )

        processed["commits"] = unique_commits

        return processed

    def _process_pr_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process a pull request event."""
        payload = event.payload
        pr = payload.get("pull_request", {})
        action = payload.get("action", "")
        number = pr.get("number", "")
        title = pr.get("title", "")

        processed = {
            "pr_number": number,
            "action": action,
            "title": title,
            "links": [f"https://github.com/{event.repo}/pull/{number}"],
            "details": [f"PR #{number}: {action} - {title}"],
        }

        return processed

    def _process_comment_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process an issue/PR comment event."""
        payload = event.payload
        issue = payload.get("issue", {})
        number = issue.get("number", "")
        is_pr = "pull_request" in issue

        link_type = "pull" if is_pr else "issues"
        processed = {
            "issue_number": number,
            "is_pull_request": is_pr,
            "links": [f"https://github.com/{event.repo}/{link_type}/{number}"],
            "details": [f"Commented on {'PR' if is_pr else 'issue'} #{number}"],
        }

        return processed

    def _process_review_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process a pull request review event."""
        payload = event.payload
        pr = payload.get("pull_request", {})
        review = payload.get("review", {})
        number = pr.get("number", "")
        state = review.get("state", "")

        processed = {
            "pr_number": number,
            "review_state": state,
            "links": [f"https://github.com/{event.repo}/pull/{number}"],
            "details": [f"Reviewed PR #{number}: {state}"],
        }

        return processed

    def _process_ref_event(self, event: GitHubEvent) -> Dict[str, Any]:
        """Process create/delete events."""
        payload = event.payload
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref", "")
        action = "Created" if event.event_type == "CreateEvent" else "Deleted"

        processed = {
            "ref_type": ref_type,
            "ref": ref,
            "action": action.lower(),
            "details": [f"{action} {ref_type} '{ref}'"],
        }

        return processed

    def _generate_summary(self, events: List[GitHubEvent]) -> Dict[str, Any]:
        """Generate a summary of all events."""
        summary = {
            "total_events": len(events),
            "event_types": {},
            "repositories": set(),
            "commit_count": 0,
            "pr_count": 0,
        }

        for event in events:
            # Count event types
            event_type = event.event_type
            summary["event_types"][event_type] = (
                summary["event_types"].get(event_type, 0) + 1
            )

            # Track repositories
            summary["repositories"].add(event.repo)

            # Count commits and PRs
            if event_type == "PushEvent":
                summary["commit_count"] += len(event.processed_info.get("commits", []))
            elif event_type == "PullRequestEvent":
                summary["pr_count"] += 1

        summary["repositories"] = list(summary["repositories"])

        return summary

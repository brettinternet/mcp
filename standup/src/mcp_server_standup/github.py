"""GitHub CLI integration for fetching activity data."""

import os
import json
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

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
    """Service for fetching and processing GitHub activity using GitHub CLI."""

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
        
        self.github_org = os.getenv("GITHUB_ORG")
        self.github_repos = os.getenv("GITHUB_REPOS")
        self.date_parser = DateParser()
        self._seen_commits = set()  # For deduplication
        self._current_user = None  # Cache for current user
        
        # Check if gh CLI is available
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("GitHub CLI (gh) is not installed or not in PATH. Please install it first.")

    def get_current_user(self) -> Optional[str]:
        """Get the current authenticated GitHub user."""
        if self._current_user is not None:
            return self._current_user
            
        try:
            result = subprocess.run(
                ["gh", "api", "user"],
                capture_output=True,
                text=True,
                check=True
            )
            
            user_data = json.loads(result.stdout)
            self._current_user = user_data.get("login")
            logger.debug(f"Current GitHub user: {self._current_user}")
            return self._current_user
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching current user with gh CLI: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing current user response: {e}")
            return None

    def get_activity(
        self,
        target_date: datetime,
        username: Optional[str] = None,
        repos: Optional[List[str]] = None,
    ) -> GitHubActivity:
        """Get GitHub activity for the specified date and filters.

        Args:
            target_date: Date to get activity for
            username: Optional username filter (defaults to current user if not provided)
            repos: Optional list of repositories to check

        Returns:
            GitHubActivity object with all events and summary
        """
        self._seen_commits.clear()  # Reset for each request

        # Default to current user if no username provided
        if not username:
            username = self.get_current_user()
            if not username:
                raise ValueError("Could not determine current GitHub user. Please provide a username explicitly.")

        activity = GitHubActivity(
            target_date=target_date,
            username=username,
            repos=repos,
        )

        # Get UTC date range for queries
        start_time, end_time = self.date_parser.get_utc_date_range(target_date)

        # Determine which repositories to process
        if not repos:
            # Try to get repositories from various sources
            repos_to_process = []
            
            if self.github_repos:
                repos_to_process = [repo.strip() for repo in self.github_repos.split(",") if repo.strip()]
                logger.debug(f"Using repositories from GITHUB_REPOS: {repos_to_process}")
            elif self.github_org:
                # Use org repositories
                repos_to_process = self._get_org_repos()
            elif username:
                # Only fallback to user repos if no GITHUB_REPOS or GITHUB_ORG is configured
                user_repos = self._get_user_repos(username)
                if user_repos:
                    repos_to_process = user_repos
                else:
                    # Final fallback to user events API
                    events = self._get_user_events(username, start_time, end_time)
                    activity.events.extend(events)
                    # Sort events by timestamp
                    activity.events.sort(key=lambda x: x.created_at)
                    # Generate summary
                    activity.summary = self._generate_summary(activity.events)
                    return activity
            
            if not repos_to_process:
                raise ValueError(
                    "Either GITHUB_ORG or GITHUB_REPOS environment variable is required when not specifying repos"
                )
        else:
            # Process specific repositories provided as parameter
            repos_to_process = [repo.strip() for repo in repos if repo.strip()]

        for repo in repos_to_process:
            events = self._get_repo_events(repo, username, start_time, end_time)
            activity.events.extend(events)

        # Sort events by timestamp
        activity.events.sort(key=lambda x: x.created_at)

        # Generate summary
        activity.summary = self._generate_summary(activity.events)

        return activity

    def _get_org_repos(self) -> List[str]:
        """Get all repositories for the configured organization using gh CLI."""
        if not self.github_org:
            return []
            
        try:
            result = subprocess.run(
                ["gh", "api", f"/orgs/{self.github_org}/repos", "--paginate"],
                capture_output=True,
                text=True,
                check=True
            )
            
            repos_data = json.loads(result.stdout)
            repos = [repo["full_name"] for repo in repos_data if "full_name" in repo]
            logger.debug(f"Found {len(repos)} repositories in {self.github_org}")
            return repos
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching org repos with gh CLI: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing gh CLI response: {e}")
            return []

    def _get_user_repos(self, username: str) -> List[str]:
        """Get all repositories for a specific user using gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "api", f"/users/{username}/repos?per_page=100"],
                capture_output=True,
                text=True,
                check=True
            )
            
            repos_data = json.loads(result.stdout)
            repos = [repo["full_name"] for repo in repos_data if "full_name" in repo]
            logger.debug(f"Found {len(repos)} repositories for user {username}")
            return repos
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching user repos with gh CLI: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing gh CLI response: {e}")
            return []

    def _get_repo_events(
        self,
        repo: str,
        username: Optional[str],
        start_time: str,
        end_time: str,
    ) -> List[GitHubEvent]:
        """Get events for a specific repository within the date range using gh CLI."""
        events = []
        page = 1
        per_page = 100

        while page <= 50:  # Safety limit
            try:
                result = subprocess.run(
                    ["gh", "api", f"/repos/{repo}/events?page={page}&per_page={per_page}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                data = json.loads(result.stdout)
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

            except subprocess.CalledProcessError as e:
                logger.error(f"Error fetching events for {repo} with gh CLI: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing gh CLI response for {repo}: {e}")
                break

        return events

    def _get_user_events(
        self,
        username: str,
        start_time: str,
        end_time: str,
    ) -> List[GitHubEvent]:
        """Get events for a specific user within the date range using gh CLI."""
        events = []
        page = 1
        per_page = 100

        while page <= 50:  # Safety limit
            try:
                result = subprocess.run(
                    ["gh", "api", f"/users/{username}/events/public?page={page}&per_page={per_page}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                data = json.loads(result.stdout)
                if not data:
                    break

                # Filter events by date range
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

                    # Get repo name from the event
                    repo = event_data.get("repo", {}).get("name", "")
                    if not repo:
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

            except subprocess.CalledProcessError as e:
                logger.error(f"Error fetching user events for {username} with gh CLI: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing gh CLI response for user {username}: {e}")
                break

        return events

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

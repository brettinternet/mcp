"""Report formatting utilities for standup summaries."""

import json
from typing import Dict, List

from .github import GitHubActivity, GitHubEvent


class StandupFormatter:
    """Format activity data into standup-friendly reports."""

    def format_standup_report(
        self,
        github_activity: GitHubActivity,
        format_type: str = "markdown",
    ) -> str:
        """Format a comprehensive standup report.

        Args:
            github_activity: GitHub activity data
            format_type: Output format ('markdown', 'text', 'json')

        Returns:
            Formatted standup report string
        """
        if format_type == "json":
            return self._format_json_report(github_activity)
        elif format_type == "text":
            return self._format_text_report(github_activity)
        else:
            return self._format_markdown_report(github_activity)

    def format_github_activity(self, activity: GitHubActivity) -> str:
        """Format detailed GitHub activity report."""
        if not activity.events:
            return f"No GitHub activity found for {activity.target_date.strftime('%Y-%m-%d')}"

        lines = [
            f"# GitHub Activity for {activity.target_date.strftime('%Y-%m-%d')}",
            "",
            f"**Summary:** {activity.summary['total_events']} events across {len(activity.summary['repositories'])} repositories",
            "",
        ]

        # Add summary stats
        if activity.summary.get("commit_count", 0) > 0:
            lines.append(f"- **Commits:** {activity.summary['commit_count']}")
        if activity.summary.get("pr_count", 0) > 0:
            lines.append(f"- **Pull Requests:** {activity.summary['pr_count']}")

        lines.extend(["", "## Detailed Activity", ""])

        # Group events by repository
        events_by_repo = {}
        for event in activity.events:
            if event.repo not in events_by_repo:
                events_by_repo[event.repo] = []
            events_by_repo[event.repo].append(event)

        for repo, repo_events in events_by_repo.items():
            lines.append(f"### {repo}")
            lines.append("")

            for event in repo_events:
                lines.extend(self._format_event_details(event))
                lines.append("")

        return "\n".join(lines)

    def _format_markdown_report(
        self,
        github_activity: GitHubActivity,
    ) -> str:
        """Format standup report in markdown format."""
        lines = [
            f"# Standup Summary - {github_activity.target_date.strftime('%B %d, %Y')}",
            "",
        ]

        # Generate standup bullet points
        standup_items = self._generate_standup_items(github_activity)

        if standup_items:
            lines.extend(standup_items)
        else:
            lines.append("No significant activity to report.")

        lines.extend(["", "---", ""])

        # Add detailed breakdown
        if github_activity.events:
            lines.extend(
                [
                    "## GitHub Activity Details",
                    "",
                    f"**{github_activity.summary['total_events']} events** across **{len(github_activity.summary['repositories'])} repositories**",
                    "",
                ]
            )

            # Add repository links
            for repo in sorted(github_activity.summary["repositories"]):
                lines.append(f"- [{repo}](https://github.com/{repo})")
            lines.append("")

        return "\n".join(lines)

    def _format_text_report(
        self,
        github_activity: GitHubActivity,
    ) -> str:
        """Format standup report in plain text format."""
        lines = [
            f"Standup Summary - {github_activity.target_date.strftime('%B %d, %Y')}",
            "=" * 50,
            "",
        ]

        standup_items = self._generate_standup_items(github_activity)

        if standup_items:
            # Convert markdown to plain text
            for item in standup_items:
                # Remove markdown links and formatting
                clean_item = item.replace("**", "").replace("*", "")
                # Convert markdown links to plain text
                import re

                clean_item = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_item)
                lines.append(clean_item)
        else:
            lines.append("No significant activity to report.")

        return "\n".join(lines)

    def _format_json_report(
        self,
        github_activity: GitHubActivity,
    ) -> str:
        """Format standup report in JSON format."""
        data = {
            "date": github_activity.target_date.isoformat(),
            "github": {
                "summary": github_activity.summary,
                "events": [
                    {
                        "type": event.event_type,
                        "created_at": event.created_at,
                        "repo": event.repo,
                        "actor": event.actor,
                        "processed_info": event.processed_info,
                    }
                    for event in github_activity.events
                ],
            },
            "standup_items": self._generate_standup_items(github_activity),
        }

        return json.dumps(data, indent=2)

    def _generate_standup_items(
        self,
        github_activity: GitHubActivity,
    ) -> List[str]:
        """Generate standup-friendly bullet points from activities."""
        items = []

        # Group GitHub events by type and significance
        significant_events = self._group_significant_events(github_activity.events)

        # Generate items for each significant activity
        for activity_type, events in significant_events.items():
            if activity_type == "commits":
                items.extend(self._format_commit_items(events))
            elif activity_type == "pull_requests":
                items.extend(self._format_pr_items(events))
            elif activity_type == "reviews":
                items.extend(self._format_review_items(events))
            elif activity_type == "other":
                items.extend(self._format_other_items(events))

        return items

    def _group_significant_events(
        self, events: List[GitHubEvent]
    ) -> Dict[str, List[GitHubEvent]]:
        """Group events by significance for standup reporting."""
        groups = {
            "commits": [],
            "pull_requests": [],
            "reviews": [],
            "other": [],
        }

        for event in events:
            if event.event_type == "PushEvent" and event.processed_info.get("commits"):
                groups["commits"].append(event)
            elif event.event_type == "PullRequestEvent":
                groups["pull_requests"].append(event)
            elif event.event_type in [
                "PullRequestReviewEvent",
                "PullRequestReviewCommentEvent",
            ]:
                groups["reviews"].append(event)
            elif event.event_type in ["IssueCommentEvent", "CreateEvent"]:
                groups["other"].append(event)

        return groups

    def _format_commit_items(self, events: List[GitHubEvent]) -> List[str]:
        """Format commit events into standup items."""
        items = []

        # Group commits by repository for cleaner reporting
        commits_by_repo = {}
        for event in events:
            repo = event.repo
            if repo not in commits_by_repo:
                commits_by_repo[repo] = []
            commits_by_repo[repo].extend(event.processed_info.get("commits", []))

        for repo, commits in commits_by_repo.items():
            if len(commits) == 1:
                commit = commits[0]
                items.append(
                    f"- Committed **{commit['message']}** to [{repo}]({commit['link']})"
                )
            else:
                # Multiple commits - summarize
                items.append(
                    f"- Made **{len(commits)} commits** to [{repo}](https://github.com/{repo})"
                )
                for commit in commits[:3]:  # Show first 3 commits
                    items.append(
                        f"  - {commit['message']} ([{commit['sha']}]({commit['link']}))"
                    )
                if len(commits) > 3:
                    items.append(f"  - *(and {len(commits) - 3} more)*")

        return items

    def _format_pr_items(self, events: List[GitHubEvent]) -> List[str]:
        """Format pull request events into standup items."""
        items = []

        for event in events:
            info = event.processed_info
            action = info.get("action", "")
            pr_number = info.get("pr_number", "")
            title = info.get("title", "")
            links = info.get("links", [])

            if action == "opened":
                link = (
                    links[0]
                    if links
                    else f"https://github.com/{event.repo}/pull/{pr_number}"
                )
                items.append(f"- Opened **[PR #{pr_number}]({link})**: {title}")
            elif action in ["closed", "merged"]:
                link = (
                    links[0]
                    if links
                    else f"https://github.com/{event.repo}/pull/{pr_number}"
                )
                items.append(
                    f"- {action.title()} **[PR #{pr_number}]({link})**: {title}"
                )

        return items

    def _format_review_items(self, events: List[GitHubEvent]) -> List[str]:
        """Format review events into standup items."""
        items = []

        # Group reviews by PR to avoid duplication
        reviews_by_pr = {}
        for event in events:
            if event.event_type == "PullRequestReviewEvent":
                info = event.processed_info
                pr_key = f"{event.repo}#{info.get('pr_number', '')}"
                if pr_key not in reviews_by_pr:
                    reviews_by_pr[pr_key] = []
                reviews_by_pr[pr_key].append(event)

        for pr_key, review_events in reviews_by_pr.items():
            # Take the latest review for each PR
            latest_review = review_events[-1]
            info = latest_review.processed_info
            pr_number = info.get("pr_number", "")
            state = info.get("review_state", "")
            links = info.get("links", [])

            link = (
                links[0]
                if links
                else f"https://github.com/{latest_review.repo}/pull/{pr_number}"
            )
            items.append(f"- Reviewed **[PR #{pr_number}]({link})** ({state})")

        return items

    def _format_other_items(self, events: List[GitHubEvent]) -> List[str]:
        """Format other significant events into standup items."""
        items = []

        for event in events:
            info = event.processed_info

            if event.event_type == "IssueCommentEvent":
                number = info.get("issue_number", "")
                is_pr = info.get("is_pull_request", False)
                links = info.get("links", [])
                link = links[0] if links else ""

                item_type = "PR" if is_pr else "issue"
                items.append(f"- Commented on **[{item_type} #{number}]({link})**")

            elif event.event_type == "CreateEvent":
                ref_type = info.get("ref_type", "")
                ref = info.get("ref", "")
                if ref_type == "branch":
                    items.append(f"- Created branch **{ref}** in {event.repo}")

        return items

    def _format_event_details(self, event: GitHubEvent) -> List[str]:
        """Format detailed event information."""
        lines = [
            f"**{event.event_type}** by {event.actor} at {event.created_at}",
        ]

        for detail in event.processed_info.get("details", []):
            lines.append(f"- {detail}")

        for link in event.processed_info.get("links", []):
            lines.append(f"- Link: {link}")

        for commit in event.processed_info.get("commits", []):
            lines.append(
                f"- Commit: {commit['message']} ([{commit['sha']}]({commit['link']}))"
            )

        return lines

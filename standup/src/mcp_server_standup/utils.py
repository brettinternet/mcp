"""Utility functions for date parsing and other common operations."""

from datetime import datetime, timedelta

from dateutil import parser as date_parser


class DateParser:
    """Handle date parsing and workday calculations."""

    def parse_date(self, date_expression: str) -> datetime:
        """Parse various date expressions into datetime objects.

        Args:
            date_expression: Date string like 'yesterday', 'last friday', '2024-07-22', etc.

        Returns:
            datetime object for the target date
        """
        if not date_expression:
            return self._get_last_workday()

        date_expression = date_expression.lower().strip()

        # Handle special cases
        if date_expression == "yesterday":
            return datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=1)
        elif date_expression == "today":
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Handle weekday names
        weekday_map = {
            "monday": 0,
            "mon": 0,
            "tuesday": 1,
            "tue": 1,
            "wednesday": 2,
            "wed": 2,
            "thursday": 3,
            "thu": 3,
            "friday": 4,
            "fri": 4,
            "saturday": 5,
            "sat": 5,
            "sunday": 6,
            "sun": 6,
        }

        # Handle "last {weekday}" format
        if date_expression.startswith("last "):
            weekday_name = date_expression[5:]
            if weekday_name in weekday_map:
                return self._get_last_weekday(weekday_map[weekday_name])

        # Handle plain weekday names (assumes "last" weekday)
        if date_expression in weekday_map:
            return self._get_last_weekday(weekday_map[date_expression])

        # Try to parse as ISO date or other formats
        try:
            return date_parser.parse(date_expression).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except (ValueError, TypeError):
            # If all else fails, return last workday
            return self._get_last_workday()

    def _get_last_workday(self) -> datetime:
        """Get the last workday (Friday if today is Monday, otherwise yesterday)."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dow = today.weekday()  # Monday is 0, Sunday is 6

        if dow == 0:  # Monday
            days_back = 3  # Go back to Friday
        else:
            days_back = 1  # Go back to yesterday

        return today - timedelta(days=days_back)

    def _get_last_weekday(self, target_weekday: int) -> datetime:
        """Get the most recent occurrence of the specified weekday.

        Args:
            target_weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        current_weekday = today.weekday()

        # Calculate days to subtract
        if current_weekday >= target_weekday:
            days_back = current_weekday - target_weekday
        else:
            days_back = 7 - (target_weekday - current_weekday)

        # If it's today, go back a full week
        if days_back == 0:
            days_back = 7

        return today - timedelta(days=days_back)

    def get_utc_date_range(self, target_date: datetime) -> tuple[str, str]:
        """Convert a target date to UTC date range for GitHub API.

        The GitHub API returns UTC times, but we want to match local work days.
        This method creates a range that captures the full day in most timezones.

        Args:
            target_date: Local date to convert

        Returns:
            Tuple of (start_timestamp, end_timestamp) in ISO format
        """
        # Start of target date in UTC
        start_time = target_date.strftime("%Y-%m-%dT00:00:00Z")

        # End extends into next day to catch late work in various timezones
        # This covers up to 8 hours into the next day (most US timezones)
        next_day = target_date + timedelta(days=1)
        end_time = next_day.strftime("%Y-%m-%dT07:59:59Z")

        return start_time, end_time

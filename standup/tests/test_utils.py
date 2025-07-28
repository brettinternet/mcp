"""Tests for utils module."""

from datetime import datetime
from freezegun import freeze_time

from mcp_server_standup.utils import DateParser


class TestDateParser:
    """Test the DateParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DateParser()

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_empty_date_returns_last_workday(self):
        """Test that empty date returns last workday."""
        result = self.parser.parse_date("")
        # Tuesday -> Monday
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_none_date_returns_last_workday(self):
        """Test that None date returns last workday."""
        result = self.parser.parse_date(None)
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)
        assert result == expected

    @freeze_time("2024-07-22 15:30:00")  # Monday
    def test_parse_empty_date_monday_returns_friday(self):
        """Test that empty date on Monday returns Friday."""
        result = self.parser.parse_date("")
        # Monday -> Friday (3 days back)
        expected = datetime(2024, 7, 19, 0, 0, 0, 0)
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_yesterday(self):
        """Test parsing 'yesterday'."""
        result = self.parser.parse_date("yesterday")
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_today(self):
        """Test parsing 'today'."""
        result = self.parser.parse_date("today")
        expected = datetime(2024, 7, 23, 0, 0, 0, 0)
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_weekday_names(self):
        """Test parsing weekday names."""
        # Test all weekday variations
        test_cases = [
            ("monday", datetime(2024, 7, 22, 0, 0, 0, 0)),  # Last Monday
            ("mon", datetime(2024, 7, 22, 0, 0, 0, 0)),
            ("tuesday", datetime(2024, 7, 16, 0, 0, 0, 0)),  # Last Tuesday (week ago)
            ("tue", datetime(2024, 7, 16, 0, 0, 0, 0)),
            ("friday", datetime(2024, 7, 19, 0, 0, 0, 0)),  # Last Friday
            ("fri", datetime(2024, 7, 19, 0, 0, 0, 0)),
        ]

        for date_str, expected in test_cases:
            result = self.parser.parse_date(date_str)
            assert result == expected, f"Failed for {date_str}"

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_last_weekday_format(self):
        """Test parsing 'last {weekday}' format."""
        test_cases = [
            ("last monday", datetime(2024, 7, 22, 0, 0, 0, 0)),
            ("last friday", datetime(2024, 7, 19, 0, 0, 0, 0)),
            ("last wednesday", datetime(2024, 7, 17, 0, 0, 0, 0)),
        ]

        for date_str, expected in test_cases:
            result = self.parser.parse_date(date_str)
            assert result == expected, f"Failed for {date_str}"

    def test_parse_iso_date(self):
        """Test parsing ISO date format."""
        result = self.parser.parse_date("2024-07-15")
        expected = datetime(2024, 7, 15, 0, 0, 0, 0)
        assert result == expected

    def test_parse_various_date_formats(self):
        """Test parsing various date formats."""
        test_cases = [
            ("2024-07-15", datetime(2024, 7, 15, 0, 0, 0, 0)),
            ("July 15, 2024", datetime(2024, 7, 15, 0, 0, 0, 0)),
            ("15 July 2024", datetime(2024, 7, 15, 0, 0, 0, 0)),
        ]

        for date_str, expected in test_cases:
            result = self.parser.parse_date(date_str)
            assert result == expected, f"Failed for {date_str}"

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_parse_invalid_date_returns_last_workday(self):
        """Test that invalid date returns last workday as fallback."""
        result = self.parser.parse_date("invalid-date")
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)  # Monday
        assert result == expected

    @freeze_time("2024-07-22 15:30:00")  # Monday
    def test_get_last_workday_monday(self):
        """Test _get_last_workday on Monday returns Friday."""
        result = self.parser._get_last_workday()
        expected = datetime(2024, 7, 19, 0, 0, 0, 0)  # Friday
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_get_last_workday_other_days(self):
        """Test _get_last_workday on other days returns yesterday."""
        result = self.parser._get_last_workday()
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)  # Monday
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_get_last_weekday_same_day(self):
        """Test _get_last_weekday when target is today goes back a week."""
        # Tuesday = 1, asking for Tuesday should go back a week
        result = self.parser._get_last_weekday(1)  # Tuesday
        expected = datetime(2024, 7, 16, 0, 0, 0, 0)  # Last Tuesday
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_get_last_weekday_earlier_in_week(self):
        """Test _get_last_weekday for earlier day in same week."""
        # Tuesday, asking for Monday (yesterday)
        result = self.parser._get_last_weekday(0)  # Monday
        expected = datetime(2024, 7, 22, 0, 0, 0, 0)  # Yesterday
        assert result == expected

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_get_last_weekday_later_in_week(self):
        """Test _get_last_weekday for later day goes to previous week."""
        # Tuesday, asking for Friday
        result = self.parser._get_last_weekday(4)  # Friday
        expected = datetime(2024, 7, 19, 0, 0, 0, 0)  # Last Friday
        assert result == expected

    def test_get_utc_date_range(self):
        """Test UTC date range generation."""
        target_date = datetime(2024, 7, 23, 0, 0, 0, 0)
        start_time, end_time = self.parser.get_utc_date_range(target_date)

        assert start_time == "2024-07-23T00:00:00Z"
        assert end_time == "2024-07-24T07:59:59Z"

    def test_get_utc_date_range_different_date(self):
        """Test UTC date range generation for different date."""
        target_date = datetime(2024, 12, 31, 0, 0, 0, 0)
        start_time, end_time = self.parser.get_utc_date_range(target_date)

        assert start_time == "2024-12-31T00:00:00Z"
        assert end_time == "2025-01-01T07:59:59Z"

    def test_case_insensitive_parsing(self):
        """Test that date parsing is case insensitive."""
        test_cases = [
            "YESTERDAY",
            "Yesterday",
            "MONDAY",
            "Monday",
            "LAST FRIDAY",
            "Last Friday",
        ]

        for date_str in test_cases:
            # Should not raise an exception
            result = self.parser.parse_date(date_str)
            assert isinstance(result, datetime)

    @freeze_time("2024-07-23 15:30:00")  # Tuesday
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""

        expected_yesterday = datetime(2024, 7, 22, 0, 0, 0, 0)
        expected_monday = datetime(2024, 7, 22, 0, 0, 0, 0)
        expected_friday = datetime(2024, 7, 19, 0, 0, 0, 0)

        assert self.parser.parse_date(" yesterday ") == expected_yesterday
        assert self.parser.parse_date("  monday  ") == expected_monday
        assert self.parser.parse_date(" last friday ") == expected_friday
        assert self.parser.parse_date("\tyesterday\n") == expected_yesterday

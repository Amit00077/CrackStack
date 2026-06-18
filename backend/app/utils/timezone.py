from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

from fastapi import Request

UTC = timezone.utc


def get_user_timezone(request: Request | None = None, user_timezone: str | None = None) -> ZoneInfo:
    tz_str = "UTC"

    if request:
        header_tz = request.headers.get("X-User-Timezone")
        if header_tz and header_tz in available_timezones():
            tz_str = header_tz

    if tz_str == "UTC" and user_timezone and user_timezone in available_timezones():
        tz_str = user_timezone

    return ZoneInfo(tz_str)


def get_today_in_timezone(tz: ZoneInfo) -> date:
    return datetime.now(tz).date()


def get_current_week_start(today: date | None = None, tz: ZoneInfo | None = None) -> date:
    if today is None:
        if tz:
            today = get_today_in_timezone(tz)
        else:
            today = datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


def get_week_start_from_goal(goal_start_date: date, week_number: int) -> date:
    week_start = goal_start_date + timedelta(weeks=week_number - 1)
    week_start = week_start - timedelta(days=week_start.weekday())
    return week_start

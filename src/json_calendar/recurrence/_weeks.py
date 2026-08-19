"""Week-based year arithmetic (Section 3.3.3.1).

Both "byWeekNo" and the start of a weekly period are numbered relative to
the rule's "firstDayOfWeek" (``wkst``, a date.weekday() value): week number
one is the first week with at least four of its days in the year.
"""

from __future__ import annotations

from datetime import date, timedelta


def week_start(day: date, wkst: int) -> date:
    return day - timedelta(days=(day.weekday() - wkst) % 7)


def _first_week_start(year: int, wkst: int) -> date:
    """The start of week number one: the first week with >= 4 days in the year."""
    january_first = date(year, 1, 1)
    days_before = (january_first.weekday() - wkst) % 7
    start = january_first - timedelta(days=days_before)
    if 7 - days_before < 4:
        start += timedelta(days=7)
    return start


def week_number(day: date, wkst: int) -> tuple[int, int]:
    """The (week-based year, week number) of ``day``, per Section 3.3.3.1."""
    start = week_start(day, wkst)
    for year in (day.year + 1, day.year, day.year - 1):
        first = _first_week_start(year, wkst)
        if start >= first:
            return year, (start - first).days // 7 + 1
    raise AssertionError("unreachable: every date belongs to a week-based year")


def weeks_in_year(year: int, wkst: int) -> int:
    return (_first_week_start(year + 1, wkst) - _first_week_start(year, wkst)).days // 7

"""Matching dates against the byX date properties of a rule (Section 3.3.3.1).

The date properties select the candidate dates within a period: within a
month by generation (step 2, where a "skip" may also adjust an invalid
date), and within the other periods by filtering the days they span.
"""

from __future__ import annotations

from calendar import isleap, monthrange
from datetime import date, timedelta

from json_calendar.recurrence._parts import Parts
from json_calendar.recurrence._weeks import week_number, weeks_in_year

# "The maximum number of days any month may have" (Section 3.3.3.1)
# in the Gregorian calendar, presumed when generating candidates with
# a "skip" in effect.
_MAX_MONTH_DAYS = 31


def month_dates(parts: Parts, year: int, month: int) -> list[date]:
    """The candidate dates within one month, filtered and skip-adjusted.

    With a "skip" in effect and a "byMonthDay" property, the month is
    presumed to have the maximum number of days any month may have, and
    matching invalid dates are adjusted per Section 3.3.3.1, step 2.2.
    """
    days_in_month = monthrange(year, month)[1]
    virtual = parts.skip != "omit" and parts.month_days is not None
    result = []
    for day in range(1, (_MAX_MONTH_DAYS if virtual else days_in_month) + 1):
        candidate = date(year, month, day) if day <= days_in_month else None
        # An invalid date is always eliminated by byWeekNo and byYearDay.
        if parts.week_nos is not None and (
            candidate is None or not _matches_week_no(parts, candidate)
        ):
            continue
        if parts.year_days is not None and (
            candidate is None or not _matches_year_day(parts, candidate)
        ):
            continue
        if parts.month_days is not None:
            if not _matches_month_day(parts, day, days_in_month):
                continue
            if candidate is None:  # adjust the invalid date (step 2.2)
                if parts.skip == "forward":
                    candidate = date(year, month, days_in_month) + timedelta(days=1)
                else:
                    candidate = date(year, month, days_in_month)
        elif candidate is None:
            continue
        if parts.n_days is not None and not _matches_day(parts, candidate):
            continue
        result.append(candidate)
    return result


def passes_date_filters(parts: Parts, day: date) -> bool:
    """Whether a (valid) date matches every byX date property of the rule."""
    if parts.months is not None and day.month not in parts.months:
        return False
    if parts.week_nos is not None and not _matches_week_no(parts, day):
        return False
    if parts.year_days is not None and not _matches_year_day(parts, day):
        return False
    if parts.month_days is not None and not _matches_month_day(
        parts, day.day, monthrange(day.year, day.month)[1]
    ):
        return False
    return parts.n_days is None or _matches_day(parts, day)


def _matches_month_day(parts: Parts, day: int, days_in_month: int) -> bool:
    assert parts.month_days is not None
    # A virtual day beyond the real month length matches positive values only.
    return any(
        day == value if value > 0 else day <= days_in_month and day == days_in_month + value + 1
        for value in parts.month_days
    )


def _matches_year_day(parts: Parts, day: date) -> bool:
    assert parts.year_days is not None
    day_of_year = day.timetuple().tm_yday
    days_in_year = 366 if isleap(day.year) else 365
    return any(
        day_of_year == (value if value > 0 else days_in_year + value + 1)
        for value in parts.year_days
    )


def _matches_week_no(parts: Parts, day: date) -> bool:
    assert parts.week_nos is not None
    year, number = week_number(day, parts.wkst)
    total = weeks_in_year(year, parts.wkst)
    return any(number == (value if value > 0 else total + value + 1) for value in parts.week_nos)


def _matches_day(parts: Parts, day: date) -> bool:
    assert parts.n_days is not None
    for weekday, nth in parts.n_days:
        if day.weekday() != weekday:
            continue
        if nth is None:
            return True
        if parts.nth_in_year:
            day_number = day.timetuple().tm_yday
            days_in_period = 366 if isleap(day.year) else 365
        else:
            day_number = day.day
            days_in_period = monthrange(day.year, day.month)[1]
        if nth > 0:
            if (day_number - 1) // 7 + 1 == nth:
                return True
        elif (days_in_period - day_number) // 7 + 1 == -nth:
            return True
    return False

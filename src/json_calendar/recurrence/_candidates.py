"""The candidate date-times of each recurrence period (Section 3.3.3.1).

Periods are stepped through by "frequency" and "interval" without end; each
one yields the candidates it holds, in order, with "bySetPosition" already
applied. An empty list is a period that holds no candidate at all, which
the caller counts toward its emptiness guard.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, time, timedelta

from json_calendar.recurrence._dates import month_dates, passes_date_filters
from json_calendar.recurrence._parts import Parts
from json_calendar.recurrence._weeks import week_start

_SUB_DAILY_UNIT = {
    "hourly": timedelta(hours=1),
    "minutely": timedelta(minutes=1),
    "secondly": timedelta(seconds=1),
}


def period_candidates(parts: Parts, dtstart: datetime) -> Iterator[list[datetime]]:
    """The per-period candidate lists, "bySetPosition" already applied."""
    frequency = parts.frequency
    if frequency == "yearly":
        year = dtstart.year
        while True:
            dates = [
                candidate
                for month in range(1, 13)
                if parts.months is None or month in parts.months
                for candidate in month_dates(parts, year, month)
            ]
            yield _combine(parts, dates)
            year += parts.interval
    elif frequency == "monthly":
        index = dtstart.year * 12 + dtstart.month - 1
        while True:
            year, month = divmod(index, 12)
            month += 1
            in_months = parts.months is None or month in parts.months
            yield _combine(parts, month_dates(parts, year, month) if in_months else [])
            index += parts.interval
    elif frequency == "weekly":
        start = week_start(dtstart.date(), parts.wkst)
        while True:
            week = (start + timedelta(days=offset) for offset in range(7))
            yield _combine(parts, [day for day in week if passes_date_filters(parts, day)])
            start += timedelta(days=7 * parts.interval)
    elif frequency == "daily":
        day = dtstart.date()
        while True:
            yield _combine(parts, [day] if passes_date_filters(parts, day) else [])
            day += timedelta(days=parts.interval)
    else:
        yield from _sub_daily_candidates(parts, dtstart)


def _combine(parts: Parts, dates: list[date]) -> list[datetime]:
    """Cross the period's dates with its times, sorted and deduplicated."""
    assert parts.times is not None
    candidates = sorted(
        {
            datetime(day.year, day.month, day.day, hour, minute, second)
            for day in dates
            for hour, minute, second in parts.times
        }
    )
    return _select_positions(parts, candidates)


def _select_positions(parts: Parts, candidates: list[datetime]) -> list[datetime]:
    if parts.set_positions is None:
        return candidates
    total = len(candidates)
    indexes = {p - 1 if p > 0 else total + p for p in parts.set_positions}
    return [candidates[i] for i in sorted(i for i in indexes if 0 <= i < total)]


def _sub_daily_candidates(parts: Parts, dtstart: datetime) -> Iterator[list[datetime]]:
    frequency = parts.frequency
    if frequency == "hourly":
        current = dtstart.replace(minute=0, second=0)
    elif frequency == "minutely":
        current = dtstart.replace(second=0)
    else:
        current = dtstart
    step = _SUB_DAILY_UNIT[frequency] * parts.interval
    while True:
        if not passes_date_filters(parts, current.date()):
            # Jump to the next day, staying aligned to the interval, and
            # report one empty period per skipped day for the emptiness guard.
            next_day = datetime.combine(current.date() + timedelta(days=1), time())
            previous = current.date()
            current += step * -((current - next_day) // step)
            for _ in range((current.date() - previous).days):
                yield []
            continue
        if parts.hours is not None and current.hour not in parts.hours:
            yield []
        elif frequency == "hourly":
            assert parts.minutes is not None and parts.seconds is not None
            yield _select_positions(
                parts,
                [
                    current.replace(minute=minute, second=second)
                    for minute in parts.minutes
                    for second in parts.seconds
                ],
            )
        elif parts.minutes is not None and current.minute not in parts.minutes:
            yield []
        elif frequency == "minutely":
            assert parts.seconds is not None
            yield _select_positions(
                parts, [current.replace(second=second) for second in parts.seconds]
            )
        elif parts.seconds is not None and current.second not in parts.seconds:
            yield []
        else:
            yield _select_positions(parts, [current])
        current += step

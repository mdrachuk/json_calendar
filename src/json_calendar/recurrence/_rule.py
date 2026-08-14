"""Applying a RecurrenceRule to an initial date-time (Section 3.3.3.1).

Implements the candidate-generation algorithm of Section 3.3.3.1: periods
are stepped through by "frequency" and "interval", candidates within each
period are matched against the byX properties (with the implicit properties
added), invalid dates are adjusted according to "skip", "bySetPosition"
selects within each period, and the stream is bounded by "count"/"until".
Only the Gregorian calendar systems are supported; other "rscale" values
raise UnsupportedCalendarError.
"""

from __future__ import annotations

from calendar import isleap, monthrange
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from json_calendar.models import NDay, RecurrenceRule

# CLDR calendar systems that share the Gregorian months, days, and leap
# years, which is all that recurrence expansion observes.
_GREGORIAN_RSCALES = frozenset({"gregorian", "gregory", "iso8601"})

# In date.weekday() order, Monday first.
_WEEKDAYS = ("mo", "tu", "we", "th", "fr", "sa", "su")

# "The maximum number of days any month may have" (Section 3.3.3.1)
# in the Gregorian calendar, presumed when generating candidates with
# a "skip" in effect.
_MAX_MONTH_DAYS = 31

# 400 Gregorian years are exactly 146097 days and exactly 20871 weeks, so
# leap years, weekdays, and week numbering all repeat with this cycle. A
# rule whose examined periods stay empty for a full cycle therefore never
# produces anything again, and iteration stops. For the sub-daily
# frequencies (where skipped days each count as one empty period) the
# bound on time-of-day patterns is a best-effort cap instead.
_EMPTY_PERIOD_GUARD = {
    "yearly": 400,
    "monthly": 4800,
    "weekly": 20871,
    "daily": 146097,
    "hourly": 200_000,
    "minutely": 200_000,
    "secondly": 200_000,
}

_SUB_DAILY_UNIT = {
    "hourly": timedelta(hours=1),
    "minutely": timedelta(minutes=1),
    "secondly": timedelta(seconds=1),
}


class UnsupportedCalendarError(ValueError):
    """The rule's "rscale" calendar system is not supported by this engine."""


def iterate(rule: RecurrenceRule, dtstart: datetime) -> Iterator[datetime]:
    """Yield the date-times of ``rule`` applied to ``dtstart``, in order.

    The stream starts with ``dtstart`` itself (Section 3.3.3.1: the initial
    date-time is always the first occurrence and counts toward "count") and
    is infinite unless bounded by "count"/"until" or provably exhausted.
    """
    if rule.rscale not in _GREGORIAN_RSCALES:
        raise UnsupportedCalendarError(
            f"the {rule.rscale!r} calendar system is not supported by the recurrence "
            f"engine; supported values: {sorted(_GREGORIAN_RSCALES)}"
        )
    return _occurrences(_resolve(rule, dtstart), dtstart, rule.count, rule.until)


@dataclass(frozen=True)
class _Parts:
    """A RecurrenceRule with the implicit properties of Section 3.3.3.1 added."""

    frequency: str
    interval: int
    skip: str
    wkst: int  # a date.weekday() value
    months: frozenset[int] | None
    month_days: tuple[int, ...] | None
    year_days: tuple[int, ...] | None
    week_nos: tuple[int, ...] | None
    n_days: tuple[tuple[int, int | None], ...] | None  # (weekday, nthOfPeriod)
    hours: tuple[int, ...] | None
    minutes: tuple[int, ...] | None
    seconds: tuple[int, ...] | None
    set_positions: tuple[int, ...] | None
    nth_in_year: bool  # byDay nthOfPeriod counts within the year, not the month
    times: tuple[tuple[int, int, int], ...] | None  # for the daily+ frequencies


def _resolve(rule: RecurrenceRule, dtstart: datetime) -> _Parts:
    frequency = rule.frequency
    seconds = rule.bySecond
    minutes = rule.byMinute
    hours = rule.byHour
    n_days = rule.byDay
    month_days = rule.byMonthDay
    months = rule.byMonth
    # The implicit properties (Section 3.3.3.1); each condition tests the
    # properties of the rule as given, not the ones added here.
    if frequency != "secondly" and seconds is None:
        seconds = [dtstart.second]
    if frequency not in ("secondly", "minutely") and minutes is None:
        minutes = [dtstart.minute]
    if frequency not in ("secondly", "minutely", "hourly") and hours is None:
        hours = [dtstart.hour]
    if frequency == "weekly" and n_days is None:
        n_days = [_dtstart_day(dtstart)]
    if frequency == "monthly" and rule.byDay is None and rule.byMonthDay is None:
        month_days = [dtstart.day]
    if frequency == "yearly" and rule.byYearDay is None:
        no_position = rule.byMonthDay is None and rule.byWeekNo is None
        if (
            rule.byMonth is None
            and rule.byWeekNo is None
            and (rule.byMonthDay is not None or rule.byDay is None)
        ):
            months = [str(dtstart.month)]
        if no_position and rule.byDay is None:
            month_days = [dtstart.day]
        if rule.byWeekNo is not None and rule.byMonthDay is None and rule.byDay is None:
            n_days = [_dtstart_day(dtstart)]
    month_set = None if months is None else frozenset(int(m.rstrip("L")) for m in months)
    # Sorted and deduplicated: the times of a period are a set of candidates,
    # which "bySetPosition" then selects within by position.
    hour_tuple = None if hours is None else tuple(sorted(set(hours)))
    minute_tuple = None if minutes is None else tuple(sorted(set(minutes)))
    # Second 60 is allowed by the model (Section 3.3.3) but corresponds to
    # no representable date-time, so such candidates are never generated.
    second_tuple = None if seconds is None else tuple(sorted({s for s in seconds if s < 60}))
    times = None
    if frequency in ("yearly", "monthly", "weekly", "daily"):
        assert hour_tuple is not None and minute_tuple is not None and second_tuple is not None
        times = tuple((h, m, s) for h in hour_tuple for m in minute_tuple for s in second_tuple)
    return _Parts(
        frequency=frequency,
        interval=rule.interval,
        skip=rule.skip,
        wkst=_WEEKDAYS.index(rule.firstDayOfWeek),
        months=month_set,
        month_days=None if month_days is None else tuple(month_days),
        year_days=None if rule.byYearDay is None else tuple(rule.byYearDay),
        week_nos=None if rule.byWeekNo is None else tuple(rule.byWeekNo),
        n_days=None
        if n_days is None
        else tuple((_WEEKDAYS.index(n.day), n.nthOfPeriod) for n in n_days),
        hours=hour_tuple,
        minutes=minute_tuple,
        seconds=second_tuple,
        set_positions=None if rule.bySetPosition is None else tuple(rule.bySetPosition),
        nth_in_year=frequency == "yearly" and month_set is None,
        times=times,
    )


def _dtstart_day(dtstart: datetime) -> NDay:
    return NDay(day=_WEEKDAYS[dtstart.weekday()])


def _occurrences(
    parts: _Parts, dtstart: datetime, count: int | None, until: datetime | None
) -> Iterator[datetime]:
    if count is not None and count < 1:
        return
    yield dtstart
    remaining = None if count is None else count - 1
    if remaining == 0:
        return
    last = dtstart  # yields are strictly increasing: dedupes and drops pre-start candidates
    empty_streak = 0
    guard = _EMPTY_PERIOD_GUARD[parts.frequency]
    for candidates in _period_candidates(parts, dtstart):
        yielded = False
        for candidate in candidates:
            if candidate <= last:
                continue
            if until is not None and candidate > until:
                return
            yield candidate
            yielded = True
            last = candidate
            if remaining is not None:
                remaining -= 1
                if remaining == 0:
                    return
        if yielded:
            empty_streak = 0
        else:
            empty_streak += 1
            if empty_streak >= guard:
                return


def _period_candidates(parts: _Parts, dtstart: datetime) -> Iterator[list[datetime]]:
    """The per-period candidate lists, "bySetPosition" already applied."""
    frequency = parts.frequency
    if frequency == "yearly":
        year = dtstart.year
        while True:
            dates = [
                candidate
                for month in range(1, 13)
                if parts.months is None or month in parts.months
                for candidate in _month_dates(parts, year, month)
            ]
            yield _combine(parts, dates)
            year += parts.interval
    elif frequency == "monthly":
        index = dtstart.year * 12 + dtstart.month - 1
        while True:
            year, month = divmod(index, 12)
            month += 1
            in_months = parts.months is None or month in parts.months
            yield _combine(parts, _month_dates(parts, year, month) if in_months else [])
            index += parts.interval
    elif frequency == "weekly":
        start = _week_start(dtstart.date(), parts.wkst)
        while True:
            week = (start + timedelta(days=offset) for offset in range(7))
            yield _combine(parts, [day for day in week if _passes_date_filters(parts, day)])
            start += timedelta(days=7 * parts.interval)
    elif frequency == "daily":
        day = dtstart.date()
        while True:
            yield _combine(parts, [day] if _passes_date_filters(parts, day) else [])
            day += timedelta(days=parts.interval)
    else:
        yield from _sub_daily_candidates(parts, dtstart)


def _combine(parts: _Parts, dates: list[date]) -> list[datetime]:
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


def _select_positions(parts: _Parts, candidates: list[datetime]) -> list[datetime]:
    if parts.set_positions is None:
        return candidates
    total = len(candidates)
    indexes = {p - 1 if p > 0 else total + p for p in parts.set_positions}
    return [candidates[i] for i in sorted(i for i in indexes if 0 <= i < total)]


def _sub_daily_candidates(parts: _Parts, dtstart: datetime) -> Iterator[list[datetime]]:
    frequency = parts.frequency
    if frequency == "hourly":
        current = dtstart.replace(minute=0, second=0)
    elif frequency == "minutely":
        current = dtstart.replace(second=0)
    else:
        current = dtstart
    step = _SUB_DAILY_UNIT[frequency] * parts.interval
    while True:
        if not _passes_date_filters(parts, current.date()):
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


def _month_dates(parts: _Parts, year: int, month: int) -> list[date]:
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


def _passes_date_filters(parts: _Parts, day: date) -> bool:
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


def _matches_month_day(parts: _Parts, day: int, days_in_month: int) -> bool:
    assert parts.month_days is not None
    # A virtual day beyond the real month length matches positive values only.
    return any(
        day == value if value > 0 else day <= days_in_month and day == days_in_month + value + 1
        for value in parts.month_days
    )


def _matches_year_day(parts: _Parts, day: date) -> bool:
    assert parts.year_days is not None
    day_of_year = day.timetuple().tm_yday
    days_in_year = 366 if isleap(day.year) else 365
    return any(
        day_of_year == (value if value > 0 else days_in_year + value + 1)
        for value in parts.year_days
    )


def _matches_week_no(parts: _Parts, day: date) -> bool:
    assert parts.week_nos is not None
    year, number = _week_number(day, parts.wkst)
    total = _weeks_in_year(year, parts.wkst)
    return any(number == (value if value > 0 else total + value + 1) for value in parts.week_nos)


def _matches_day(parts: _Parts, day: date) -> bool:
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


def _week_start(day: date, wkst: int) -> date:
    return day - timedelta(days=(day.weekday() - wkst) % 7)


def _first_week_start(year: int, wkst: int) -> date:
    """The start of week number one: the first week with >= 4 days in the year."""
    january_first = date(year, 1, 1)
    days_before = (january_first.weekday() - wkst) % 7
    start = january_first - timedelta(days=days_before)
    if 7 - days_before < 4:
        start += timedelta(days=7)
    return start


def _week_number(day: date, wkst: int) -> tuple[int, int]:
    """The (week-based year, week number) of ``day``, per Section 3.3.3.1."""
    start = _week_start(day, wkst)
    for year in (day.year + 1, day.year, day.year - 1):
        first = _first_week_start(year, wkst)
        if start >= first:
            return year, (start - first).days // 7 + 1
    raise AssertionError("unreachable: every date belongs to a week-based year")


def _weeks_in_year(year: int, wkst: int) -> int:
    return (_first_week_start(year + 1, wkst) - _first_week_start(year, wkst)).days // 7

"""Resolving a RecurrenceRule against its initial date-time (Section 3.3.3.1).

The candidate algorithm reads a rule with the implicit byX properties
already added — the ones the initial date-time supplies when the rule
leaves them out — and with the remaining properties normalized to the
forms the generation and matching steps want.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from json_calendar.models import NDay, RecurrenceRule

# In date.weekday() order, Monday first.
_WEEKDAYS = ("mo", "tu", "we", "th", "fr", "sa", "su")


@dataclass(frozen=True)
class Parts:
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


def resolve(rule: RecurrenceRule, dtstart: datetime) -> Parts:
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
    return Parts(
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

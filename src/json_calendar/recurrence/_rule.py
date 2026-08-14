"""Applying a RecurrenceRule to an initial date-time (Section 3.3.3.1).

The date-times of a rule are the candidates of its periods, in order,
bounded by "count"/"until": :mod:`._parts` resolves the rule against the
initial date-time, :mod:`._candidates` generates the candidates of each
period, and this module streams them. Only the Gregorian calendar systems
are supported; other "rscale" values raise UnsupportedCalendarError.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from json_calendar.models import RecurrenceRule
from json_calendar.recurrence._candidates import period_candidates
from json_calendar.recurrence._parts import Parts, resolve

# CLDR calendar systems that share the Gregorian months, days, and leap
# years, which is all that recurrence expansion observes.
_GREGORIAN_RSCALES = frozenset({"gregorian", "gregory", "iso8601"})

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
    return _occurrences(resolve(rule, dtstart), dtstart, rule.count, rule.until)


def _occurrences(
    parts: Parts, dtstart: datetime, count: int | None, until: datetime | None
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
    for candidates in period_candidates(parts, dtstart):
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

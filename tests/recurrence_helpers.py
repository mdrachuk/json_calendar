"""Builders and shorthands shared by the recurrence engine's tests.

The date-times follow the RRULE examples of RFC 5545, Section 3.8.5.3,
whose initial date-time is 1997-09-02T09:00:00.
"""

from datetime import datetime
from itertools import islice

from json_calendar.models import Event, Task
from json_calendar.recurrence import expand


def event(start="1997-09-02T09:00:00", rule=None, overrides=None, **props):
    data = {
        "@type": "Event",
        "version": "2.0",
        "uid": "recurrence-test",
        "updated": "2020-01-01T00:00:00Z",
        "start": start,
    }
    if rule is not None:
        data["recurrenceRule"] = rule
    if overrides is not None:
        data["recurrenceOverrides"] = overrides
    data.update(props)
    return Event.model_validate(data)


def task(**props):
    data = {
        "@type": "Task",
        "version": "2.0",
        "uid": "recurrence-test",
        "updated": "2020-01-01T00:00:00Z",
    }
    data.update(props)
    return Task.model_validate(data)


def ids(obj, n=None, **window):
    """The recurrence ids of ``obj`` as ISO strings, the first ``n`` if given."""
    occurrences = expand(obj, **window)
    if n is not None:
        occurrences = islice(occurrences, n)
    return [occurrence.recurrence_id.isoformat() for occurrence in occurrences]


def at(*dates, time="09:00:00"):
    """Expand 'YYYY-MM-DD' date strings into ISO date-times at ``time``."""
    return [f"{date}T{time}" for date in dates]


def dt(value):
    return datetime.fromisoformat(value)


def days(day_by_day):
    """[('mo', 1), 'fr'] -> NDay JSON objects."""
    return [
        {"day": entry} if isinstance(entry, str) else {"day": entry[0], "nthOfPeriod": entry[1]}
        for entry in day_by_day
    ]

"""Recurrence engine for JSCalendar 2.0.

Expands recurrence rules (Section 4.3 of draft-ietf-calext-jscalendarbis-18)
into concrete occurrence instances, applying recurrenceRules,
excludedRecurrenceRules, and recurrenceOverrides.
"""

from collections.abc import Iterator
from datetime import datetime

from json_calendar.models import Event, Task


def expand(obj: Event | Task, *, start: datetime, end: datetime) -> Iterator[datetime]:
    """Yield the occurrence start times of ``obj`` within ``[start, end)``.

    Not implemented yet.
    """
    raise NotImplementedError("Recurrence expansion is not implemented yet.")

"""Converter between JSCalendar 2.0 and iCalendar (RFC 5545).

Follows the translation guidance referenced by
draft-ietf-calext-jscalendarbis-18 for mapping JSCalendar objects to and from
iCalendar components.
"""

from json_calendar.models import Event, Group, Task


def from_ical(text: str) -> Group | Event | Task:
    """Parse an iCalendar stream into JSCalendar objects.

    Not implemented yet.
    """
    raise NotImplementedError("iCalendar conversion is not implemented yet.")


def to_ical(obj: Group | Event | Task) -> str:
    """Serialize JSCalendar objects to an iCalendar stream.

    Not implemented yet.
    """
    raise NotImplementedError("iCalendar conversion is not implemented yet.")

"""JSCalendar 2.0 for Python.

A library for working with the JSCalendar 2.0 standard
(draft-ietf-calext-jscalendarbis): a data model and validator built on
pydantic, a recurrence engine, and a converter to/from iCalendar.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from json_calendar._types import (
    Duration,
    Id,
    Int,
    LocalDateTime,
    PatchObject,
    SignedDuration,
    TimeZoneId,
    UnsignedInt,
    UTCDateTime,
)
from json_calendar.models import (
    AbsoluteTrigger,
    Alert,
    CalendarObject,
    Event,
    Group,
    JSCalendarObject,
    Link,
    Location,
    NDay,
    OffsetTrigger,
    Participant,
    RecurrenceRule,
    Relation,
    Task,
    UnknownCalendarObject,
    UnknownTrigger,
    VirtualLocation,
)

__version__ = "0.1.0"

__all__ = [
    "AbsoluteTrigger",
    "Alert",
    "CalendarObject",
    "Duration",
    "Event",
    "Group",
    "Id",
    "Int",
    "JSCalendarObject",
    "Link",
    "LocalDateTime",
    "Location",
    "NDay",
    "OffsetTrigger",
    "Participant",
    "PatchObject",
    "RecurrenceRule",
    "Relation",
    "SignedDuration",
    "Task",
    "TimeZoneId",
    "UTCDateTime",
    "UnknownCalendarObject",
    "UnknownTrigger",
    "UnsignedInt",
    "VirtualLocation",
    "__version__",
]

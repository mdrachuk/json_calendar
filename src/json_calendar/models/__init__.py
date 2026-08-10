"""Data model and validation for JSCalendar 2.0 objects.

Implements the object types of draft-ietf-calext-jscalendarbis-18: the
Event (Section 2.1), Task (Section 2.2), and Group (Section 2.3) calendar
object types, the component objects they are built from (Sections 1.5 and 3),
and the validation rules the spec attaches to them.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from json_calendar.models._base import JSCalendarObject
from json_calendar.models.alert import (
    AbsoluteTrigger,
    Alert,
    OffsetTrigger,
    Trigger,
    UnknownTrigger,
)
from json_calendar.models.calendar_object import CalendarObject
from json_calendar.models.event import Event
from json_calendar.models.group import Group, GroupEntry, UnknownCalendarObject
from json_calendar.models.link import Link
from json_calendar.models.location import Location, VirtualLocation
from json_calendar.models.participant import Participant
from json_calendar.models.recurrence_rule import NDay, RecurrenceRule
from json_calendar.models.relation import Relation
from json_calendar.models.task import Task

__all__ = [
    "AbsoluteTrigger",
    "Alert",
    "CalendarObject",
    "Event",
    "Group",
    "GroupEntry",
    "JSCalendarObject",
    "Link",
    "Location",
    "NDay",
    "OffsetTrigger",
    "Participant",
    "RecurrenceRule",
    "Relation",
    "Task",
    "Trigger",
    "UnknownCalendarObject",
    "UnknownTrigger",
    "VirtualLocation",
]

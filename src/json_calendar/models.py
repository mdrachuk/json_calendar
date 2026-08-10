"""Data model and validation for JSCalendar 2.0 objects.

Implements the object types defined in draft-ietf-calext-jscalendarbis-18:
Event (Section 2.1), Task (Section 2.2), and Group (Section 2.3), along with
their properties and value types.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JSCalendarObject(BaseModel):
    """Base class for all JSCalendar objects.

    JSCalendar objects are JSON objects whose type is identified by the
    "@type" property. Unknown properties are preserved to keep vendor
    extensions (Section 3.3) intact through a parse/serialize round trip.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
        extra="allow",
    )


class Event(JSCalendarObject):
    """A scheduled amount of time on a calendar (Section 2.1)."""

    type: Literal["Event"] = Field(default="Event", alias="@type")
    uid: str


class Task(JSCalendarObject):
    """An action item, assignment, to-do, or work item (Section 2.2)."""

    type: Literal["Task"] = Field(default="Task", alias="@type")
    uid: str


class Group(JSCalendarObject):
    """A collection of Event and/or Task objects (Section 2.3)."""

    type: Literal["Group"] = Field(default="Group", alias="@type")
    uid: str
    entries: list[Event | Task] = Field(default_factory=list)

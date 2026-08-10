"""The Group object (Sections 2.3 and 4.3)."""

from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field, model_validator

from json_calendar._types import Id, LanguageTag, Uri, UTCDateTime
from json_calendar.models._base import (
    Color,
    JSCalendarObject,
    JSCalendarVersion,
    TextContentType,
)
from json_calendar.models.calendar_object import CalendarObject
from json_calendar.models.event import Event
from json_calendar.models.link import Link
from json_calendar.models.task import Task


class UnknownCalendarObject(JSCalendarObject):
    """A Group entry whose "@type" is not recognized; preserved as-is."""

    type: str = Field(alias="@type")


def _dispatch_entry(value: Any) -> Any:
    if isinstance(value, dict):
        entry_type = value.get("@type")
        if entry_type is None:
            raise ValueError('Group entries must set the "@type" property')
        if entry_type == "Event":
            return Event.model_validate(value)
        if entry_type == "Task":
            return Task.model_validate(value)
        return UnknownCalendarObject.model_validate(value)
    return value


GroupEntry = Annotated[Event | Task | UnknownCalendarObject, BeforeValidator(_dispatch_entry)]


class Group(JSCalendarObject):
    """A collection of Event and/or Task objects (Sections 2.3 and 4.3)."""

    type: Literal["Group"] = Field(default="Group", alias="@type")
    uid: str = Field(min_length=1)
    version: JSCalendarVersion | None = None
    prodId: str | None = None
    created: UTCDateTime | None = None
    updated: UTCDateTime
    title: str = ""
    description: str = ""
    descriptionContentType: TextContentType = "text/plain"
    keywords: dict[str, Literal[True]] | None = None
    categories: dict[Uri, Literal[True]] | None = None
    color: Color | None = None
    links: dict[Id, Link] | None = None
    locale: LanguageTag | None = None
    entries: list[GroupEntry]
    source: Uri | None = None

    @model_validator(mode="after")
    def _entries_must_not_set_version(self) -> "Group":
        for entry in self.entries:
            if isinstance(entry, CalendarObject) and "version" in entry.model_fields_set:
                raise ValueError(
                    'Event and Task objects in the "entries" of a Group must not '
                    'set the "version" property'
                )
        return self

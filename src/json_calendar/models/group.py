"""The Group object (Sections 2.3 and 4.3)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, ValidatorFunctionWrapHandler, WrapValidator
from pydantic.json_schema import SkipJsonSchema

from json_calendar._spec import cites
from json_calendar._types import Id, LanguageTag, Uri, UTCDateTime
from json_calendar.models._base import (
    Color,
    JSCalendarObject,
    JSCalendarVersion,
    TextContentType,
)
from json_calendar.models.event import Event
from json_calendar.models.link import Link
from json_calendar.models.task import Task


class Group(JSCalendarObject):
    """A collection of Event and/or Task objects (Sections 2.3 and 4.3)."""

    type: Literal["Group"] = Field(alias="@type")
    uid: Annotated[str, Field(min_length=1), cites("Section 3.1.1")]
    version: JSCalendarVersion
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


class UnknownCalendarObject(JSCalendarObject):
    """A Group entry whose "@type" is not recognized; preserved as-is."""

    type: str = Field(alias="@type")


class _EventEntry(Event):
    """An Event in the "entries" of a Group; must not set "version" (Section 3.1.2)."""

    version: SkipJsonSchema[None] = Field(default=None, exclude=True)


class _TaskEntry(Task):
    """A Task in the "entries" of a Group; must not set "version" (Section 3.1.2)."""

    version: SkipJsonSchema[None] = Field(default=None, exclude=True)


def _dispatch_entry(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    # A wrap validator so that already-validated entries pass through as-is
    # instead of being re-validated by the union, and so that standalone Event
    # and Task instances (which must set "version") are rejected outright.
    if isinstance(value, (Event, Task)):
        if "version" in value.model_fields_set:
            raise ValueError(
                'Event and Task objects in the "entries" of a Group must not '
                'set the "version" property (Section 3.1.2)'
            )
        return value
    if isinstance(value, dict):
        entry_type = value.get("@type")
        if entry_type is None:
            raise ValueError('Group entries must set the "@type" property (Section 4.3.1)')
        if entry_type in ("Event", "Task") and "version" in value:
            raise ValueError(
                'Event and Task objects in the "entries" of a Group must not '
                'set the "version" property (Section 3.1.2)'
            )
        if entry_type == "Event":
            return _EventEntry.model_validate(value)
        if entry_type == "Task":
            return _TaskEntry.model_validate(value)
        return UnknownCalendarObject.model_validate(value)
    return handler(value)


GroupEntry = Annotated[
    _EventEntry | _TaskEntry | UnknownCalendarObject, WrapValidator(_dispatch_entry)
]

Group.model_rebuild()

"""The Group object (Sections 2.3 and 4.3)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, ValidatorFunctionWrapHandler, WrapValidator, model_validator
from pydantic.json_schema import SkipJsonSchema

from json_calendar._spec import cites
from json_calendar._types import Id, LanguageTag, Uri, UTCDateTime
from json_calendar.models._base import (
    _KNOWN_TYPE_NAMES,
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

    type: Annotated[Literal["Group"], cites("Section 2.3")] = Field(alias="@type")
    uid: Annotated[str, Field(min_length=1), cites("Section 3.1.1")]
    version: JSCalendarVersion
    prodId: Annotated[str, cites("Section 3.1.4")] | None = None
    created: UTCDateTime | None = None
    updated: Annotated[UTCDateTime, cites("Section 3.1.6")]
    title: Annotated[str, cites("Section 3.2.1")] = ""
    description: Annotated[str, cites("Section 3.2.2")] = ""
    descriptionContentType: TextContentType = "text/plain"
    keywords: dict[str, Annotated[Literal[True], cites("Section 3.2.10")]] | None = None
    categories: dict[Uri, Annotated[Literal[True], cites("Section 3.2.11")]] | None = None
    color: Color | None = None
    links: dict[Id, Link] | None = None
    locale: LanguageTag | None = None
    entries: Annotated[list[GroupEntry], cites("Section 4.3.1")]
    source: Uri | None = None


class UnknownCalendarObject(JSCalendarObject):
    """A Group entry whose "@type" is not recognized; preserved as-is."""

    type: str = Field(alias="@type")

    @model_validator(mode="after")
    def _type_is_unknown(self) -> UnknownCalendarObject:
        # Case variants of known names are left to the Section 1.7.1 rule.
        if _KNOWN_TYPE_NAMES.get(self.type.lower()) == self.type:
            raise ValueError(
                f'{self.type!r} is a known type, and the "entries" of a Group '
                f"may only hold Event and Task objects (Section 4.3.1)"
            )
        return self


class _EventEntry(Event):
    """An Event in the "entries" of a Group; must not set "version" (Section 3.1.2)."""

    version: SkipJsonSchema[None] = Field(default=None, exclude=True)


class _TaskEntry(Task):
    """A Task in the "entries" of a Group; must not set "version" (Section 3.1.2)."""

    version: SkipJsonSchema[None] = Field(default=None, exclude=True)


def _dispatch_entry(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    # A wrap validator so that already-validated entries pass through as-is
    # instead of being re-validated by the union, and so that standalone Event
    # and Task instances (whose required "version" property a Group entry must
    # not carry, Section 3.1.2) are converted to their entry forms.
    if isinstance(value, (_EventEntry, _TaskEntry)):
        return value
    if isinstance(value, (Event, Task)):
        entry_class = _EventEntry if isinstance(value, Event) else _TaskEntry
        return entry_class.model_validate(
            value.model_dump(by_alias=True, exclude_unset=True, exclude={"version"})
        )
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

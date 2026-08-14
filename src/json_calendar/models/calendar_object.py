"""The properties common to Event and Task objects (Section 3)."""

from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field, ValidationError, model_validator

from json_calendar._patch import apply_patch
from json_calendar._spec import cites
from json_calendar._types import (
    Email,
    Id,
    LanguageTag,
    LocalDateTime,
    PatchObject,
    TimeZoneId,
    UnsignedInt,
    Uri,
    UTCDateTime,
    format_local_date_time,
    open_enum,
)
from json_calendar.models._base import (
    Color,
    JSCalendarObject,
    JSCalendarVersion,
    TextContentType,
)
from json_calendar.models.alert import Alert
from json_calendar.models.link import Link
from json_calendar.models.location import Location, VirtualLocation
from json_calendar.models.participant import Participant
from json_calendar.models.recurrence_rule import RecurrenceRule
from json_calendar.models.relation import Relation

_IGNORED_OVERRIDE_POINTERS = frozenset(
    {
        ("@type",),
        ("method",),
        ("organizerCalendarAddress",),
        ("privacy",),
        ("prodId",),
        ("recurrenceId",),
        ("recurrenceIdTimeZone",),
        ("sentBy",),
        ("uid",),
    }
)
_IGNORED_OVERRIDE_FIRST_TOKENS = frozenset({"recurrenceOverrides", "recurrenceRule", "relatedTo"})


def _ignored_in_override(tokens: list[str]) -> bool:
    """Whether a recurrence override pointer MUST be ignored (Section 3.3.4)."""
    return (
        tuple(tokens) in _IGNORED_OVERRIDE_POINTERS
        or tokens[0] in _IGNORED_OVERRIDE_FIRST_TOKENS
        or (len(tokens) == 3 and tokens[0] == "participants" and tokens[2] == "calendarAddress")
    )


FreeBusyStatus = Annotated[str, open_enum("free", "busy"), cites("Section 3.4.2")]
Privacy = Annotated[str, open_enum("public", "private", "secret"), cites("Section 3.4.3")]
ItipMethod = Annotated[
    Literal["publish", "request", "reply", "add", "cancel", "refresh", "counter", "declinecounter"],
    cites("Section 3.1.8"),
]


class CalendarObject(JSCalendarObject):
    """The properties common to Event and Task objects (Section 3)."""

    uid: Annotated[str, Field(min_length=1), cites("Section 3.1.1")]
    # Mandatory for standalone objects; the Group entry subclasses override
    # this field because entries must not set it (Section 3.1.2).
    version: JSCalendarVersion
    relatedTo: dict[str, Relation] | None = None
    prodId: Annotated[str, cites("Section 3.1.4")] | None = None
    created: UTCDateTime | None = None
    updated: Annotated[UTCDateTime, cites("Section 3.1.6")]
    sequence: UnsignedInt = 0
    method: ItipMethod | None = None
    title: Annotated[str, cites("Section 3.2.1")] = ""
    description: Annotated[str, cites("Section 3.2.2")] = ""
    descriptionContentType: TextContentType = "text/plain"
    showWithoutTime: Annotated[bool, Field(strict=True), cites("Section 3.2.4")] = False
    locations: dict[Id, Location] | None = None
    mainLocationId: Annotated[str, cites("Section 3.2.6")] | None = None
    virtualLocations: dict[Id, VirtualLocation] | None = None
    links: dict[Id, Link] | None = None
    locale: LanguageTag | None = None
    keywords: dict[str, Annotated[Literal[True], cites("Section 3.2.10")]] | None = None
    categories: dict[Uri, Annotated[Literal[True], cites("Section 3.2.11")]] | None = None
    color: Color | None = None
    recurrenceId: LocalDateTime | None = None
    recurrenceIdTimeZone: TimeZoneId | None = None
    recurrenceRule: RecurrenceRule | None = None
    recurrenceOverrides: dict[LocalDateTime, PatchObject] | None = None
    priority: Annotated[int, Field(strict=True, ge=0, le=9), cites("Section 3.4.1")] = 0
    freeBusyStatus: FreeBusyStatus = "busy"
    privacy: Privacy = "public"
    organizerCalendarAddress: Uri | None = None
    sentBy: Email | None = None
    participants: dict[Id, Participant] | None = None
    alerts: dict[Id, Alert] | None = None
    timeZone: TimeZoneId | None = None

    @model_validator(mode="after")
    def _validate_common(self) -> "CalendarObject":
        if self.mainLocationId is not None:
            location = (self.locations or {}).get(self.mainLocationId)
            if location is None:
                raise ValueError(
                    '"mainLocationId" must match a key in the "locations" property (Section 3.2.6)'
                )
            if location.name is None:
                raise ValueError(
                    'the main Location must have its "name" property set (Section 3.2.6)'
                )
        if self.recurrenceId is not None:
            if self.recurrenceRule is not None or self.recurrenceOverrides is not None:
                raise ValueError(
                    'if "recurrenceId" is set, the "recurrenceRule" and '
                    '"recurrenceOverrides" properties must not be set (Section 3.3.1)'
                )
        elif self.recurrenceIdTimeZone is not None:
            raise ValueError(
                '"recurrenceIdTimeZone" must not be set if "recurrenceId" '
                "is not set (Section 3.3.2)"
            )
        for recurrence_id, patch in (self.recurrenceOverrides or {}).items():
            if "excluded" in patch:
                if patch != {"excluded": True}:
                    raise ValueError(
                        "an override excluding an occurrence must be exactly "
                        '{"excluded": true} (Section 3.3.4)'
                    )
                continue
            occurrence = occurrence_json(self, recurrence_id, patch)
            try:
                type(self).model_validate(occurrence)
            except ValidationError as error:
                raise ValueError(
                    f"the {recurrence_id.isoformat()} override patches the occurrence "
                    f"into an invalid object (Section 3.3.4): {error}"
                ) from error
        has_scheduled_participant = any(
            participant.calendarAddress is not None
            for participant in (self.participants or {}).values()
        )
        if has_scheduled_participant and self.organizerCalendarAddress is None:
            raise ValueError(
                'if any participant has "calendarAddress" set, the '
                '"organizerCalendarAddress" property must be set (Section 3.4.4)'
            )
        if self.organizerCalendarAddress is not None and not has_scheduled_participant:
            raise ValueError(
                'if "organizerCalendarAddress" is set, at least one participant '
                'must have the "calendarAddress" property set (Section 3.4.4)'
            )
        if self.sentBy is not None and self.organizerCalendarAddress is None:
            raise ValueError(
                'if "sentBy" is set, the "organizerCalendarAddress" property '
                "must be set (Section 3.4.5)"
            )
        return self


def occurrence_json(
    obj: CalendarObject, recurrence_id: datetime, patch: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """The JSON of the occurrence of ``obj`` at ``recurrence_id`` (Section 3.3.4).

    The occurrence inherits every property except the start (or, for a Task
    with no start, the due) date-time, which is shifted to match the
    recurrence id, and then has ``patch`` applied to it.
    """
    occurrence = obj.model_dump(
        mode="json",
        exclude_unset=True,
        exclude_none=True,
        exclude={"recurrenceRule", "recurrenceOverrides"},
    )
    occurrence["recurrenceId"] = format_local_date_time(recurrence_id)
    if obj.timeZone is not None:
        occurrence["recurrenceIdTimeZone"] = obj.timeZone
    shifted = "due" if "due" in occurrence and "start" not in occurrence else "start"
    occurrence[shifted] = occurrence["recurrenceId"]
    if patch:
        apply_patch(occurrence, patch, ignore=_ignored_in_override)
    return occurrence

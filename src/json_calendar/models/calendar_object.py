"""The properties common to Event and Task objects (Section 3)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar.models.alert import Alert
from json_calendar.models.base import (
    Color,
    JSCalendarObject,
    JSCalendarVersion,
    TextContentType,
)
from json_calendar.models.link import Link
from json_calendar.models.location import Location, VirtualLocation
from json_calendar.models.participant import Participant
from json_calendar.models.recurrence_rule import RecurrenceRule
from json_calendar.models.relation import Relation
from json_calendar.types import (
    Email,
    Id,
    LanguageTag,
    LocalDateTime,
    PatchObject,
    TimeZoneId,
    UnsignedInt,
    Uri,
    UTCDateTime,
    open_enum,
)

FreeBusyStatus = Annotated[str, open_enum("free", "busy")]
Privacy = Annotated[str, open_enum("public", "private", "secret")]
ItipMethod = Literal[
    "publish", "request", "reply", "add", "cancel", "refresh", "counter", "declinecounter"
]


class CalendarObject(JSCalendarObject):
    """The properties common to Event and Task objects (Section 3)."""

    uid: str = Field(min_length=1)
    version: JSCalendarVersion | None = None
    relatedTo: dict[str, Relation] | None = None
    prodId: str | None = None
    created: UTCDateTime | None = None
    updated: UTCDateTime
    sequence: UnsignedInt = 0
    method: ItipMethod | None = None
    title: str = ""
    description: str = ""
    descriptionContentType: TextContentType = "text/plain"
    showWithoutTime: bool = False
    locations: dict[Id, Location] | None = None
    mainLocationId: str | None = None
    virtualLocations: dict[Id, VirtualLocation] | None = None
    links: dict[Id, Link] | None = None
    locale: LanguageTag | None = None
    keywords: dict[str, Literal[True]] | None = None
    categories: dict[Uri, Literal[True]] | None = None
    color: Color | None = None
    recurrenceId: LocalDateTime | None = None
    recurrenceIdTimeZone: TimeZoneId | None = None
    recurrenceRule: RecurrenceRule | None = None
    recurrenceOverrides: dict[LocalDateTime, PatchObject] | None = None
    priority: Annotated[int, Field(strict=True, ge=0, le=9)] = 0
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
                raise ValueError('"mainLocationId" must match a key in the "locations" property')
            if location.name is None:
                raise ValueError('the main Location must have its "name" property set')
        if self.recurrenceId is not None:
            if self.recurrenceRule is not None or self.recurrenceOverrides is not None:
                raise ValueError(
                    'if "recurrenceId" is set, the "recurrenceRule" and '
                    '"recurrenceOverrides" properties must not be set'
                )
        elif self.recurrenceIdTimeZone is not None:
            raise ValueError('"recurrenceIdTimeZone" must not be set if "recurrenceId" is not set')
        for patch in (self.recurrenceOverrides or {}).values():
            if "excluded" in patch and patch != {"excluded": True}:
                raise ValueError(
                    'an override excluding an occurrence must be exactly {"excluded": true}'
                )
        has_scheduled_participant = any(
            participant.calendarAddress is not None
            for participant in (self.participants or {}).values()
        )
        if has_scheduled_participant and self.organizerCalendarAddress is None:
            raise ValueError(
                'if any participant has "calendarAddress" set, the '
                '"organizerCalendarAddress" property must be set'
            )
        if self.organizerCalendarAddress is not None and not has_scheduled_participant:
            raise ValueError(
                'if "organizerCalendarAddress" is set, at least one participant '
                'must have the "calendarAddress" property set'
            )
        if self.sentBy is not None and self.organizerCalendarAddress is None:
            raise ValueError(
                'if "sentBy" is set, the "organizerCalendarAddress" property must be set'
            )
        return self

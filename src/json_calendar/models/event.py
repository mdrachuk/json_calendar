"""The Event object (Sections 2.1 and 4.1)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import Duration, LocalDateTime, TimeZoneId, open_enum
from json_calendar.models.calendar_object import CalendarObject

EventStatus = Annotated[
    str, open_enum("confirmed", "cancelled", "tentative"), cites("Section 4.1.4")
]


class Event(CalendarObject):
    """A scheduled amount of time on a calendar (Sections 2.1 and 4.1)."""

    type: Annotated[Literal["Event"], cites("Section 2.1")] = Field(alias="@type")
    start: LocalDateTime
    duration: Duration = "PT0S"
    endTimeZone: TimeZoneId | None = None
    status: EventStatus = "confirmed"

    @model_validator(mode="after")
    def _validate_event(self) -> "Event":
        if self.endTimeZone is not None and self.timeZone is None:
            raise ValueError(
                '"endTimeZone" must not be set if the "timeZone" property '
                "is not set (Section 4.1.3)"
            )
        for participant in (self.participants or {}).values():
            for name in ("progress", "percentComplete"):
                if name in participant.model_fields_set:
                    raise ValueError(
                        f'the participant "{name}" property is only allowed '
                        f"for participants of a Task (Section 3.4.6)"
                    )
        return self

"""The Event object (Sections 2.1 and 4.1)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar._types import Duration, LocalDateTime, TimeZoneId, open_enum
from json_calendar.models.calendar_object import CalendarObject

EventStatus = Annotated[str, open_enum("confirmed", "cancelled", "tentative")]


class Event(CalendarObject):
    """A scheduled amount of time on a calendar (Sections 2.1 and 4.1)."""

    type: Literal["Event"] = Field(default="Event", alias="@type")
    start: LocalDateTime
    duration: Duration = "PT0S"
    endTimeZone: TimeZoneId | None = None
    status: EventStatus = "confirmed"

    @model_validator(mode="after")
    def _validate_event(self) -> "Event":
        if self.endTimeZone is not None and self.timeZone is None:
            raise ValueError('"endTimeZone" must not be set if the "timeZone" property is not set')
        for participant in (self.participants or {}).values():
            for name in ("progress", "percentComplete"):
                if name in participant.model_fields_set:
                    raise ValueError(
                        f'the participant "{name}" property is only allowed '
                        f"for participants of a Task"
                    )
        return self

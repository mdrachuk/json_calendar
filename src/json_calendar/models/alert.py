"""The Alert object and its triggers (Section 3.5.1)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import SignedDuration, UTCDateTime, open_enum
from json_calendar.models._base import JSCalendarObject
from json_calendar.models.relation import Relation

AlertAction = Annotated[str, open_enum("display", "email"), cites("Section 3.5.1")]


class Alert(JSCalendarObject):
    """An alert/reminder for a calendar object (Section 3.5.1)."""

    type: Annotated[Literal["Alert"], cites("Section 3.5.1")] = Field(
        default="Alert", alias="@type"
    )
    trigger: Trigger
    acknowledged: UTCDateTime | None = None
    relatedTo: dict[str, Relation] | None = None
    action: AlertAction = "display"


class OffsetTrigger(JSCalendarObject):
    """Triggers an alert relative to the object's time (Section 3.5.1)."""

    type: Annotated[Literal["OffsetTrigger"], cites("Section 3.5.1")] = Field(
        default="OffsetTrigger", alias="@type"
    )
    offset: SignedDuration
    relativeTo: Annotated[Literal["start", "end"], cites("Section 3.5.1")] = "start"


class AbsoluteTrigger(JSCalendarObject):
    """Triggers an alert at a specific UTC date-time (Section 3.5.1)."""

    type: Annotated[Literal["AbsoluteTrigger"], cites("Section 3.5.1")] = Field(
        default="AbsoluteTrigger", alias="@type"
    )
    when: UTCDateTime


class UnknownTrigger(JSCalendarObject):
    """A trigger whose "@type" is not recognized; preserved as-is (Section 3.5.1)."""

    type: str = Field(alias="@type")

    @model_validator(mode="after")
    def _type_is_unknown(self) -> UnknownTrigger:
        if self.type in ("OffsetTrigger", "AbsoluteTrigger"):
            raise ValueError(f"{self.type!r} is a known trigger type (Section 3.5.1)")
        return self


def _dispatch_trigger(value: Any) -> Any:
    if isinstance(value, dict):
        trigger_type = value.get("@type", "OffsetTrigger")
        if trigger_type == "OffsetTrigger":
            return OffsetTrigger.model_validate(value)
        if trigger_type == "AbsoluteTrigger":
            return AbsoluteTrigger.model_validate(value)
        return UnknownTrigger.model_validate(value)
    return value


Trigger = Annotated[
    OffsetTrigger | AbsoluteTrigger | UnknownTrigger, BeforeValidator(_dispatch_trigger)
]

Alert.model_rebuild()

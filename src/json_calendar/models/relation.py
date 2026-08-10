"""The Relation object (Section 1.5.10)."""

from typing import Annotated, Literal

from pydantic import Field

from json_calendar._types import open_enum
from json_calendar.models._base import JSCalendarObject

# "snooze" is IANA-registered for relations between Alert objects (Section
# 3.5.1); it is accepted everywhere since Relation carries no context here.
RelationValue = Annotated[str, open_enum("first", "next", "child", "parent", "snooze")]


class Relation(JSCalendarObject):
    """How a linked object is related to the linking object (Section 1.5.10)."""

    type: Literal["Relation"] = Field(default="Relation", alias="@type")
    relation: dict[RelationValue, Literal[True]] = Field(default_factory=dict)

"""The Link object (Section 1.5.11)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import UnsignedInt, Uri, open_enum
from json_calendar.models._base import JSCalendarObject

DisplayValue = Annotated[
    str, open_enum("badge", "graphic", "fullsize", "thumbnail"), cites("Section 1.5.11")
]


class Link(JSCalendarObject):
    """An external resource associated with the linking object (Section 1.5.11)."""

    type: Literal["Link"] = Field(default="Link", alias="@type")
    href: Uri
    contentType: str | None = None
    size: UnsignedInt | None = None
    rel: str = "enclosure"
    display: dict[DisplayValue, Literal[True]] | None = Field(default=None, min_length=1)
    title: str | None = None

    @model_validator(mode="after")
    def _display_requires_icon_rel(self) -> "Link":
        if self.display is not None and self.rel != "icon":
            raise ValueError(
                'if "display" is set, the "rel" property must be set to "icon" (Section 1.5.11)'
            )
        return self

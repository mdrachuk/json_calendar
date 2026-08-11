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

    type: Annotated[Literal["Link"], cites("Section 1.5.11")] = Field(default="Link", alias="@type")
    href: Uri
    contentType: Annotated[str, cites("Section 1.5.11")] | None = None
    size: UnsignedInt | None = None
    rel: Annotated[str, cites("Section 1.5.11")] = "enclosure"
    display: dict[DisplayValue, Annotated[Literal[True], cites("Section 1.5.11")]] | None = Field(
        default=None, min_length=1
    )
    title: Annotated[str, cites("Section 1.5.11")] | None = None

    @model_validator(mode="after")
    def _display_requires_icon_rel(self) -> "Link":
        if self.display is not None and self.rel != "icon":
            raise ValueError(
                'if "display" is set, the "rel" property must be set to "icon" (Section 1.5.11)'
            )
        return self

"""The Link object (Section 1.5.11)."""

import re
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import MediaType, UnsignedInt, Uri, is_uri, open_enum
from json_calendar.models._base import JSCalendarObject

DisplayValue = Annotated[
    str, open_enum("badge", "graphic", "fullsize", "thumbnail"), cites("Section 1.5.11")
]

# The "relation-type" rule of RFC 8288, Section 2.1: a registered relation
# name ("reg-rel-type") or an extension relation type, which is a URI.
_REG_REL_TYPE = re.compile(r"[a-z][a-z0-9.\-]*")


def _check_link_relation(value: str) -> str:
    if _REG_REL_TYPE.fullmatch(value) is None and not is_uri(value):
        raise ValueError(f"{value!r} is not a link relation type (RFC 8288, Section 2.1)")
    return value


LinkRelation = Annotated[
    str, AfterValidator(_check_link_relation), cites("Section 1.5.11; RFC 8288")
]


class Link(JSCalendarObject):
    """An external resource associated with the linking object (Section 1.5.11)."""

    type: Annotated[Literal["Link"], cites("Section 1.5.11")] = Field(default="Link", alias="@type")
    href: Annotated[Uri, cites("Section 1.5.11")]
    contentType: Annotated[MediaType, cites("Section 1.5.11")] | None = None
    size: UnsignedInt | None = None
    rel: LinkRelation = "enclosure"
    display: Annotated[
        dict[DisplayValue, Annotated[Literal[True], cites("Section 1.5.11")]] | None,
        cites("Section 1.5.11"),
    ] = Field(default=None, min_length=1)
    title: Annotated[str, cites("Section 1.5.11")] | None = None

    @model_validator(mode="after")
    def _display_requires_icon_rel(self) -> "Link":
        if self.display is not None and self.rel != "icon":
            raise ValueError(
                'if "display" is set, the "rel" property must be set to "icon" (Section 1.5.11)'
            )
        return self

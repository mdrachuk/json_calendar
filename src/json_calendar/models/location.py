"""The Location and VirtualLocation objects (Sections 3.2.5 and 3.2.7)."""

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import Id, Uri, open_enum
from json_calendar.models._base import JSCalendarObject
from json_calendar.models.link import Link


def _check_geo_uri(value: str) -> str:
    if not value.startswith("geo:"):
        raise ValueError(f"{value!r} is not a 'geo:' URI")
    return value


GeoUri = Annotated[str, AfterValidator(_check_geo_uri), cites("RFC 5870")]
FeatureValue = Annotated[
    str,
    open_enum("audio", "chat", "feed", "moderator", "phone", "screen", "video"),
    cites("Section 3.2.7"),
]


class Location(JSCalendarObject):
    """A physical location associated with a calendar object (Section 3.2.5)."""

    type: Annotated[Literal["Location"], cites("Section 3.2.5")] = Field(
        default="Location", alias="@type"
    )
    name: Annotated[str, cites("Section 3.2.5")] | None = None
    locationTypes: Annotated[
        dict[str, Annotated[Literal[True], cites("Section 3.2.5")]] | None,
        cites("Section 3.2.5"),
    ] = Field(default=None, min_length=1)
    coordinates: GeoUri | None = None
    links: Annotated[dict[Id, Link] | None, cites("Section 3.2.5")] = Field(
        default=None, min_length=1
    )

    @model_validator(mode="after")
    def _requires_a_property(self) -> "Location":
        set_fields = self.model_fields_set - {"type"}
        if not set_fields and not self.__pydantic_extra__:
            raise ValueError(
                'a Location must have at least one property other than "@type" (Section 3.2.5)'
            )
        return self


class VirtualLocation(JSCalendarObject):
    """A virtual location, such as a video conference (Section 3.2.7)."""

    type: Annotated[Literal["VirtualLocation"], cites("Section 3.2.7")] = Field(
        default="VirtualLocation", alias="@type"
    )
    name: Annotated[str, cites("Section 3.2.7")] = ""
    uri: Annotated[Uri, cites("Section 3.2.7")]
    features: Annotated[
        dict[FeatureValue, Annotated[Literal[True], cites("Section 3.2.7")]] | None,
        cites("Section 3.2.7"),
    ] = Field(default=None, min_length=1)

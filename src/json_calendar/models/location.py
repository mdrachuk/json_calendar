"""The Location and VirtualLocation objects (Sections 3.2.5 and 3.2.7)."""

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar.models.base import JSCalendarObject
from json_calendar.models.link import Link
from json_calendar.types import Id, Uri, open_enum


def _check_geo_uri(value: str) -> str:
    if not value.startswith("geo:"):
        raise ValueError(f"{value!r} is not a 'geo:' URI")
    return value


GeoUri = Annotated[str, AfterValidator(_check_geo_uri)]
FeatureValue = Annotated[
    str, open_enum("audio", "chat", "feed", "moderator", "phone", "screen", "video")
]


class Location(JSCalendarObject):
    """A physical location associated with a calendar object (Section 3.2.5)."""

    type: Literal["Location"] = Field(default="Location", alias="@type")
    name: str | None = None
    locationTypes: dict[str, Literal[True]] | None = Field(default=None, min_length=1)
    coordinates: GeoUri | None = None
    links: dict[Id, Link] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _requires_a_property(self) -> "Location":
        set_fields = self.model_fields_set - {"type"}
        if not set_fields and not self.__pydantic_extra__:
            raise ValueError('a Location must have at least one property other than "@type"')
        return self


class VirtualLocation(JSCalendarObject):
    """A virtual location, such as a video conference (Section 3.2.7)."""

    type: Literal["VirtualLocation"] = Field(default="VirtualLocation", alias="@type")
    name: str = ""
    uri: Uri
    features: dict[FeatureValue, Literal[True]] | None = Field(default=None, min_length=1)

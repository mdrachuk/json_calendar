"""The Location and VirtualLocation objects (Sections 3.2.5 and 3.2.7)."""

import re
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import Id, Uri, open_enum
from json_calendar.models._base import JSCalendarObject
from json_calendar.models.link import Link

# The "geo-URI" rule of RFC 5870, Section 3.3. The scheme, parameter names,
# and the "crs" value are case-insensitive (Section 3.4).
_GEO_PNUM = r"[0-9]+(?:\.[0-9]+)?"
_GEO_NUM = rf"-?{_GEO_PNUM}"
_GEO_LABEL = r"[A-Za-z0-9\-]+"
_GEO_PARAM_CHAR = r"(?:[A-Za-z0-9\-_.!~*'()\[\]:&+$]|%[0-9A-Fa-f]{2})"
_GEO_URI = re.compile(
    rf"geo:(?P<a>{_GEO_NUM}),(?P<b>{_GEO_NUM})(?:,{_GEO_NUM})?"
    rf"(?:;crs=(?P<crs>{_GEO_LABEL}))?"
    rf"(?:;u={_GEO_PNUM})?"
    # "crs" and "u" never re-match as generic parameters: they may appear
    # only once, in the order above, with the value forms above. The
    # lookahead spans a whole <pname>, so that extension parameters whose
    # names merely start with those letters, such as "crs-x", still match.
    rf"(?:;(?!(?:crs|u)(?:[=;]|$)){_GEO_LABEL}(?:={_GEO_PARAM_CHAR}+)?)*",
    re.IGNORECASE,
)

# In the default CRS of WGS-84, <coord-a> and <coord-b> are the narrower
# <latitude> and <longitude> rules of Section 3.3; <coord-c> becomes
# <altitude>, which is <num> itself and so needs no further check.
_GEO_LATITUDE = re.compile(r"-?[0-9]{1,2}(?:\.[0-9]+)?")
_GEO_LONGITUDE = re.compile(r"-?[0-9]{1,3}(?:\.[0-9]+)?")


def _check_geo_uri(value: str) -> str:
    match = _GEO_URI.fullmatch(value)
    if match is None:
        raise ValueError(f"{value!r} is not a 'geo:' URI (RFC 5870, Section 3.3)")
    if (match.group("crs") or "wgs84").lower() == "wgs84":
        latitude, longitude = match.group("a"), match.group("b")
        if not _GEO_LATITUDE.fullmatch(latitude) or not _GEO_LONGITUDE.fullmatch(longitude):
            raise ValueError(
                f"{value!r} coordinates are not a WGS-84 <latitude>,<longitude> "
                f"pair of at most two and three integer digits "
                f"(RFC 5870, Section 3.3)"
            )
        if abs(float(latitude)) > 90 or abs(float(longitude)) > 180:
            raise ValueError(
                f"{value!r} coordinates are outside the WGS-84 ranges of "
                f"±90 latitude and ±180 longitude (RFC 5870, Section 3.4.2)"
            )
    return value


GeoUri = Annotated[str, AfterValidator(_check_geo_uri), cites("RFC 5870")]

# The tokens of the IANA "Location Types Registry"
# (https://www.iana.org/assignments/location-type-registry), which
# "locationTypes" keys MUST be from (Section 3.2.5); the registry collects
# the RFC 4589 values and later registrations.
_LOCATION_TYPES = frozenset(
    {
        "aircraft",
        "airport",
        "arena",
        "automobile",
        "bank",
        "bar",
        "bicycle",
        "bus",
        "bus-station",
        "cafe",
        "campground",
        "care-facility",
        "classroom",
        "club",
        "construction",
        "convention-center",
        "detached-unit",
        "fire-station",
        "government",
        "hospital",
        "hotel",
        "industrial",
        "landmark-address",
        "library",
        "motorcycle",
        "municipal-garage",
        "museum",
        "office",
        "other",
        "outdoors",
        "parking",
        "phone-box",
        "place-of-worship",
        "post-office",
        "prison",
        "public",
        "public-transport",
        "residence",
        "restaurant",
        "school",
        "shopping-area",
        "stadium",
        "store",
        "street",
        "theater",
        "toll-booth",
        "town-hall",
        "train",
        "train-station",
        "truck",
        "underway",
        "unknown",
        "utilitybox",
        "warehouse",
        "waste-transfer-facility",
        "water",
        "water-facility",
        "watercraft",
        "youth-camp",
    }
)


def _check_location_type(value: str) -> str:
    if value not in _LOCATION_TYPES:
        raise ValueError(
            f"{value!r} is not in the IANA Location Types Registry (Section 3.2.5; RFC 4589)"
        )
    return value


LocationType = Annotated[
    str, AfterValidator(_check_location_type), cites("Section 3.2.5; RFC 4589")
]
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
        dict[LocationType, Annotated[Literal[True], cites("Section 3.2.5")]] | None,
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

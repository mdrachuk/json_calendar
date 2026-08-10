"""Scalar value types for JSCalendar 2.0 (Section 1.5 and 1.8).

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

import re
from datetime import UTC, datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    PlainSerializer,
    StringConstraints,
)

MAX_INT = 2**53 - 1

Id = Annotated[str, StringConstraints(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9\-_]+$")]
Int = Annotated[int, Field(strict=True, ge=-MAX_INT, le=MAX_INT)]
UnsignedInt = Annotated[int, Field(strict=True, ge=0, le=MAX_INT)]

_UTC_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_LOCAL_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _parse_utc_date_time(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.utcoffset() != UTC.utcoffset(None):
            raise ValueError("UTCDateTime must be an aware datetime in UTC")
        if value.microsecond:
            raise ValueError("UTCDateTime must not include fractional seconds")
        return value
    if isinstance(value, str):
        if not _UTC_DATE_TIME.match(value):
            raise ValueError(
                "UTCDateTime must be formatted as 'YYYY-MM-DDTHH:MM:SSZ' with no fractional seconds"
            )
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return parsed.replace(tzinfo=UTC)
    raise ValueError("UTCDateTime must be a string or datetime")


def _parse_local_date_time(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            raise ValueError("LocalDateTime must be a naive datetime")
        if value.microsecond:
            raise ValueError("LocalDateTime must not include fractional seconds")
        return value
    if isinstance(value, str):
        if not _LOCAL_DATE_TIME.match(value):
            raise ValueError(
                "LocalDateTime must be formatted as 'YYYY-MM-DDTHH:MM:SS' "
                "with no zone offset and no fractional seconds"
            )
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    raise ValueError("LocalDateTime must be a string or datetime")


UTCDateTime = Annotated[
    datetime,
    BeforeValidator(_parse_utc_date_time),
    PlainSerializer(
        lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ"), return_type=str, when_used="json"
    ),
]
"""RFC 3339 "date-time" restricted to uppercase letters and a "Z" offset."""

LocalDateTime = Annotated[
    datetime,
    BeforeValidator(_parse_local_date_time),
    PlainSerializer(lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S"), return_type=str, when_used="json"),
]
"""A date-time without zone/offset information, naive on the Python side."""

_DUR_TIME = r"T(?:\d+H(?:\d+M(?:\d+S)?)?|\d+M(?:\d+S)?|\d+S)"
_DURATION = rf"P(?:(?:\d+W(?:\d+D)?|\d+D)(?:{_DUR_TIME})?|{_DUR_TIME})"

Duration = Annotated[str, StringConstraints(pattern=rf"^{_DURATION}$")]
SignedDuration = Annotated[str, StringConstraints(pattern=rf"^[+-]?{_DURATION}$")]


def _check_time_zone_id(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"{value!r} is not an IANA Time Zone Database name") from None
    return value


TimeZoneId = Annotated[str, AfterValidator(_check_time_zone_id)]

PatchObject = dict[str, Any]
"""An unordered set of patches on a JSON object (Section 1.5.9)."""

_URI = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:\S+$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+$")
_LANGUAGE_TAG = re.compile(r"^[A-Za-z]{1,8}(-[A-Za-z0-9]{1,8})*$")

# A pragmatic subset of the "v-extension" ABNF of Section 1.8.1: a dot-separated
# domain-like prefix, a colon, and a name without CTLs, DQUOTE, SOLIDUS, TILDE.
_VENDOR_VALUE = re.compile(r"^[^\W_][\w\-]*(\.[^\W_][\w\-]*)*:[^\x00-\x1f\x7f\"/~]+$", re.UNICODE)
# IANA-registered names: ALPHA / DIGIT / "@", notated in lower camel case.
_IANA_NAME = re.compile(r"^@?[a-z][A-Za-z0-9]*$")


def is_vendor_extension(value: str) -> bool:
    """Return whether ``value`` is a vendor-specific name (Section 1.8.1)."""
    return _VENDOR_VALUE.match(value) is not None


def is_valid_property_name(name: str) -> bool:
    """Return whether ``name`` is a valid IANA-style or vendor property name."""
    return _IANA_NAME.match(name) is not None or is_vendor_extension(name)


def _check_uri(value: str) -> str:
    if not _URI.match(value):
        raise ValueError(f"{value!r} is not a URI")
    return value


def _check_email(value: str) -> str:
    if not _EMAIL.match(value):
        raise ValueError(f"{value!r} is not an email address")
    return value


def _check_language_tag(value: str) -> str:
    if not _LANGUAGE_TAG.match(value):
        raise ValueError(f"{value!r} is not an RFC 5646 language tag")
    return value


Uri = Annotated[str, AfterValidator(_check_uri)]
Email = Annotated[str, AfterValidator(_check_email)]
LanguageTag = Annotated[str, AfterValidator(_check_language_tag)]


def open_enum(*known: str) -> AfterValidator:
    """An enum limited to ``known`` values plus vendor-specific values."""

    def check(value: str) -> str:
        if value in known or is_vendor_extension(value):
            return value
        raise ValueError(f"{value!r} is not one of {sorted(known)} or a vendor-specific value")

    return AfterValidator(check)

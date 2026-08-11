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

from json_calendar._patch import check_no_prefix_collisions, parse_pointer
from json_calendar._spec import cites

MAX_INT = 2**53 - 1

Id = Annotated[
    str,
    StringConstraints(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9\-_]+$"),
    cites("Section 1.5.1"),
]
Int = Annotated[int, Field(strict=True, ge=-MAX_INT, le=MAX_INT), cites("Section 1.5.2")]
UnsignedInt = Annotated[int, Field(strict=True, ge=0, le=MAX_INT), cites("Section 1.5.3")]

_UTC_DATE_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_LOCAL_DATE_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}")


def _parse_utc_date_time(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.utcoffset() != UTC.utcoffset(None):
            raise ValueError("UTCDateTime must be an aware datetime in UTC")
        if value.microsecond:
            raise ValueError("UTCDateTime must not include fractional seconds")
        return value
    if isinstance(value, str):
        if not _UTC_DATE_TIME.fullmatch(value):
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
        if not _LOCAL_DATE_TIME.fullmatch(value):
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
    cites("Section 1.5.4"),
]
"""RFC 3339 "date-time" restricted to uppercase letters and a "Z" offset."""

LocalDateTime = Annotated[
    datetime,
    BeforeValidator(_parse_local_date_time),
    PlainSerializer(lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S"), return_type=str, when_used="json"),
    cites("Section 1.5.5"),
]
"""A date-time without zone/offset information, naive on the Python side."""

_DUR_TIME = r"T(?:[0-9]+H(?:[0-9]+M(?:[0-9]+S)?)?|[0-9]+M(?:[0-9]+S)?|[0-9]+S)"
_DURATION = rf"P(?:(?:[0-9]+W(?:[0-9]+D)?|[0-9]+D)(?:{_DUR_TIME})?|{_DUR_TIME})"

Duration = Annotated[str, StringConstraints(pattern=rf"^{_DURATION}$"), cites("Section 1.5.6")]
SignedDuration = Annotated[
    str, StringConstraints(pattern=rf"^[+-]?{_DURATION}$"), cites("Section 1.5.7")
]


def _check_time_zone_id(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"{value!r} is not an IANA Time Zone Database name") from None
    return value


TimeZoneId = Annotated[str, AfterValidator(_check_time_zone_id), cites("Section 1.5.8")]


def _check_patch_object(patch: dict[str, Any]) -> dict[str, Any]:
    check_no_prefix_collisions({key: parse_pointer(key) for key in patch})
    return patch


PatchObject = Annotated[dict[str, Any], AfterValidator(_check_patch_object), cites("Section 1.5.9")]
"""An unordered set of patches on a JSON object (Section 1.5.9).

Each key is a JSON Pointer with an implicit leading "/". The type checks
the pointer syntax and that no pointer is a prefix of another; the rules
that depend on the object being patched are checked where the patch is
applied (e.g. "recurrenceOverrides", Section 3.3.4).
"""

# The "URI" rule of RFC 3986, transcribed from the collected ABNF of Appendix A.
_UNRESERVED = r"A-Za-z0-9\-._~"
_SUB_DELIMS = r"!$&'()*+,;="
_PCT_ENCODED = r"%[0-9A-Fa-f]{2}"
_PCHAR = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}:@]|{_PCT_ENCODED})"
_DEC_OCTET = r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])"
_IPV4_ADDRESS = rf"{_DEC_OCTET}(?:\.{_DEC_OCTET}){{3}}"
_H16 = r"[0-9A-Fa-f]{1,4}"
_LS32 = rf"(?:{_H16}:{_H16}|{_IPV4_ADDRESS})"
_IPV6_ADDRESS = (
    rf"(?:(?:{_H16}:){{6}}{_LS32}"
    rf"|::(?:{_H16}:){{5}}{_LS32}"
    rf"|{_H16}?::(?:{_H16}:){{4}}{_LS32}"
    rf"|(?:(?:{_H16}:){{0,1}}{_H16})?::(?:{_H16}:){{3}}{_LS32}"
    rf"|(?:(?:{_H16}:){{0,2}}{_H16})?::(?:{_H16}:){{2}}{_LS32}"
    rf"|(?:(?:{_H16}:){{0,3}}{_H16})?::{_H16}:{_LS32}"
    rf"|(?:(?:{_H16}:){{0,4}}{_H16})?::{_LS32}"
    rf"|(?:(?:{_H16}:){{0,5}}{_H16})?::{_H16}"
    rf"|(?:(?:{_H16}:){{0,6}}{_H16})?::)"
)
_IP_LITERAL = rf"\[(?:{_IPV6_ADDRESS}|[vV][0-9A-Fa-f]+\.[{_UNRESERVED}{_SUB_DELIMS}:]+)\]"
_REG_NAME = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}]|{_PCT_ENCODED})*"
_HOST = rf"(?:{_IP_LITERAL}|{_IPV4_ADDRESS}|{_REG_NAME})"
_USERINFO = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}:]|{_PCT_ENCODED})*"
_AUTHORITY = rf"(?:{_USERINFO}@)?{_HOST}(?::[0-9]*)?"
_HIER_PART = (
    rf"(?://{_AUTHORITY}(?:/{_PCHAR}*)*"  # authority + path-abempty
    rf"|/(?:{_PCHAR}+(?:/{_PCHAR}*)*)?"  # path-absolute
    rf"|{_PCHAR}+(?:/{_PCHAR}*)*"  # path-rootless
    rf")?"  # path-empty
)
_QUERY_OR_FRAGMENT = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}:@/?]|{_PCT_ENCODED})*"
_URI = re.compile(
    rf"[A-Za-z][A-Za-z0-9+.\-]*:{_HIER_PART}"
    rf"(?:\?{_QUERY_OR_FRAGMENT})?(?:#{_QUERY_OR_FRAGMENT})?"
)

# The "addr-spec" rule of RFC 5322, Section 3.4.1, without the comments,
# folding, and obsolete alternatives: dot-atom-text or a quoted-string, an
# "@", and a dot-atom-text or a domain-literal.
_ATEXT = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~\-]"
_DOT_ATOM_TEXT = rf"{_ATEXT}+(?:\.{_ATEXT}+)*"
_QUOTED_STRING = r'"(?:[\t \x21\x23-\x5b\x5d-\x7e]|\\[\x20-\x7e\t])*"'
_DOMAIN_LITERAL = r"\[[\x21-\x5a\x5e-\x7e]*\]"
_EMAIL = re.compile(
    rf"(?:{_DOT_ATOM_TEXT}|{_QUOTED_STRING})@(?:{_DOT_ATOM_TEXT}|{_DOMAIN_LITERAL})"
)

# The "Language-Tag" rule of RFC 5646, Section 2.1: a well-formed (though not
# necessarily registered) language tag, or one of the irregular grandfathered
# tags; the regular grandfathered tags already match the "langtag" rule.
_EXTLANG = r"[A-Za-z]{3}(?:-[A-Za-z]{3}){0,2}"
_LANGUAGE = rf"[A-Za-z]{{2,3}}(?:-{_EXTLANG})?|[A-Za-z]{{4,8}}"
_SCRIPT = r"[A-Za-z]{4}"
_REGION = r"[A-Za-z]{2}|[0-9]{3}"
_VARIANT = r"[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}"
_EXTENSION = r"[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+"
_PRIVATE_USE = r"x(?:-[A-Za-z0-9]{1,8})+"
_IRREGULAR = (
    "en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo"
    "|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE"
)
_LANGTAG = (
    rf"(?:{_LANGUAGE})(?:-{_SCRIPT})?(?:-(?:{_REGION}))?"
    rf"(?:-(?:{_VARIANT}))*(?:-{_EXTENSION})*(?:-{_PRIVATE_USE})?"
)
_LANGUAGE_TAG = re.compile(rf"{_LANGTAG}|{_PRIVATE_USE}|{_IRREGULAR}", re.IGNORECASE)

# The "v-extension" rule of Section 1.8.1: a dot-separated prefix of labels
# (alphanumeric or non-ASCII, with non-leading/trailing hyphens), a colon,
# and a name without CTLs, DQUOTE, SOLIDUS, and TILDE.
_ALNUM_INT = r"A-Za-z0-9\u0080-\U0010ffff"
_V_LABEL = rf"[{_ALNUM_INT}](?:[{_ALNUM_INT}\-]*[{_ALNUM_INT}])?"
_V_NAME = r"[ \t!\x23-\x2e\x30-\x7d\u0080-\U0010ffff]+"
_VENDOR_VALUE = re.compile(rf"{_V_LABEL}(?:\.{_V_LABEL})*:{_V_NAME}")
# IANA-registered names: ALPHA / DIGIT / "@", notated in lower camel case.
_IANA_NAME = re.compile(r"@?[a-z][A-Za-z0-9]*")


def is_vendor_extension(value: str) -> bool:
    """Return whether ``value`` is a vendor-specific name (Section 1.8.1)."""
    return _VENDOR_VALUE.fullmatch(value) is not None


def is_valid_property_name(name: str) -> bool:
    """Return whether ``name`` is a valid IANA-style or vendor property name."""
    return _IANA_NAME.fullmatch(name) is not None or is_vendor_extension(name)


def _check_uri(value: str) -> str:
    if not _URI.fullmatch(value):
        raise ValueError(f"{value!r} is not a URI")
    return value


def _check_email(value: str) -> str:
    if not _EMAIL.fullmatch(value):
        raise ValueError(f"{value!r} is not an 'addr-spec' email address")
    return value


def _check_language_tag(value: str) -> str:
    if not _LANGUAGE_TAG.fullmatch(value):
        raise ValueError(f"{value!r} is not a language tag")
    return value


Uri = Annotated[str, AfterValidator(_check_uri), cites("RFC 3986")]
Email = Annotated[str, AfterValidator(_check_email), cites("RFC 5322, Section 3.4.1")]
LanguageTag = Annotated[str, AfterValidator(_check_language_tag), cites("RFC 5646")]


def open_enum(*known: str) -> AfterValidator:
    """An enum limited to ``known`` values plus vendor-specific values."""

    def check(value: str) -> str:
        if value in known or is_vendor_extension(value):
            return value
        raise ValueError(f"{value!r} is not one of {sorted(known)} or a vendor-specific value")

    return AfterValidator(check)

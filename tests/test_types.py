"""Tests for the scalar value types of Section 1.5."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from json_calendar._types import (
    Duration,
    Email,
    Id,
    Int,
    LanguageTag,
    LocalDateTime,
    SignedDuration,
    TimeZoneId,
    UnsignedInt,
    Uri,
    UTCDateTime,
    is_vendor_extension,
)
from json_calendar.models._base import Color

ids = TypeAdapter(Id)
ints = TypeAdapter(Int)
unsigned = TypeAdapter(UnsignedInt)
utc = TypeAdapter(UTCDateTime)
local = TypeAdapter(LocalDateTime)
durations = TypeAdapter(Duration)
signed_durations = TypeAdapter(SignedDuration)
tzids = TypeAdapter(TimeZoneId)
uris = TypeAdapter(Uri)
emails = TypeAdapter(Email)
language_tags = TypeAdapter(LanguageTag)
colors = TypeAdapter(Color)


class TestId:
    @pytest.mark.parametrize("value", ["a", "A-b_9", "x" * 255, "0"])
    def test_valid(self, value):
        assert ids.validate_python(value) == value

    @pytest.mark.parametrize("value", ["", "x" * 256, "a=b", "a b", "é", "a/b", "a:b"])
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            ids.validate_python(value)


class TestInt:
    def test_bounds(self):
        assert ints.validate_python(2**53 - 1) == 2**53 - 1
        assert ints.validate_python(-(2**53) + 1) == -(2**53) + 1
        with pytest.raises(ValidationError):
            ints.validate_python(2**53)
        with pytest.raises(ValidationError):
            ints.validate_python(-(2**53))

    def test_rejects_bool_and_string(self):
        with pytest.raises(ValidationError):
            ints.validate_python(True)
        with pytest.raises(ValidationError):
            ints.validate_python("5")

    def test_unsigned(self):
        assert unsigned.validate_python(0) == 0
        with pytest.raises(ValidationError):
            unsigned.validate_python(-1)


class TestUTCDateTime:
    def test_parses_to_aware_datetime(self):
        parsed = utc.validate_python("2020-01-02T18:23:04Z")
        assert parsed == datetime(2020, 1, 2, 18, 23, 4, tzinfo=UTC)

    @pytest.mark.parametrize(
        "value",
        [
            "2010-10-10T10:10:10.0Z",
            "2010-10-10T10:10:10.123Z",
            "2010-10-10t10:10:10Z",
            "2010-10-10T10:10:10z",
            "2010-10-10T10:10:10+00:00",
            "2010-10-10T10:10:10",
            "2010-13-10T10:10:10Z",
            "2010-10-32T10:10:10Z",
            "2010-10-10T24:10:10Z",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            utc.validate_python(value)

    def test_serializes_to_spec_format(self):
        parsed = utc.validate_python("2020-01-02T18:23:04Z")
        assert utc.dump_python(parsed, mode="json") == "2020-01-02T18:23:04Z"

    def test_serializes_years_below_1000_zero_padded(self):
        parsed = utc.validate_python("0001-01-01T00:00:00Z")
        assert utc.dump_python(parsed, mode="json") == "0001-01-01T00:00:00Z"

    def test_accepts_utc_datetime_instance(self):
        value = datetime(2020, 1, 2, 18, 23, 4, tzinfo=UTC)
        assert utc.validate_python(value) == value

    def test_rejects_naive_datetime_instance(self):
        with pytest.raises(ValidationError):
            utc.validate_python(datetime(2020, 1, 2, 18, 23, 4))


class TestLocalDateTime:
    def test_parses_to_naive_datetime(self):
        parsed = local.validate_python("2006-01-02T15:04:05")
        assert parsed == datetime(2006, 1, 2, 15, 4, 5)
        assert parsed.tzinfo is None

    @pytest.mark.parametrize(
        "value",
        [
            "2006-01-02T15:04:05Z",
            "2006-01-02T15:04:05.123",
            "2006-01-02T15:04:05+02:00",
            "2006-01-02 15:04:05",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            local.validate_python(value)

    def test_serializes_to_spec_format(self):
        parsed = local.validate_python("2006-01-02T15:04:05")
        assert local.dump_python(parsed, mode="json") == "2006-01-02T15:04:05"

    def test_serializes_years_below_1000_zero_padded(self):
        parsed = local.validate_python("0099-01-02T15:04:05")
        assert local.dump_python(parsed, mode="json") == "0099-01-02T15:04:05"

    def test_rejects_aware_datetime_instance(self):
        with pytest.raises(ValidationError):
            local.validate_python(datetime(2006, 1, 2, tzinfo=UTC))


class TestDuration:
    @pytest.mark.parametrize(
        "value",
        ["PT1H", "P1D", "P1W", "P2W1D", "P2W1DT3H4M5S", "PT0S", "PT10H30M", "P15DT5H0M20S"],
    )
    def test_valid(self, value):
        assert durations.validate_python(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            "P",
            "PT",
            "P1H",
            "1D",
            "PT1H2S",
            "P1DT",
            "-PT1H",
            "+PT1H",
            "P1D2W",
            "pt1h",
            "PT1.5H",
            "P\uff11D",
            "PT1\u06605S",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            durations.validate_python(value)

    @pytest.mark.parametrize("value", ["-PT5M", "+P1D", "PT5M", "-P2W1DT3H4M5S"])
    def test_signed_valid(self, value):
        assert signed_durations.validate_python(value) == value

    @pytest.mark.parametrize("value", ["--PT5M", "-", "-P"])
    def test_signed_invalid(self, value):
        with pytest.raises(ValidationError):
            signed_durations.validate_python(value)


class TestUri:
    @pytest.mark.parametrize(
        "value",
        [
            "https://example.com/foo?bar=baz#frag",
            "mailto:cyrus@example.com",
            "urn:ietf:rfc:3986",
            "data:text/plain;charset=utf-8,hello%20world",
            "http://example.com/a%2Fb",
            "http://user@example.com:8080/path",
            "http://[2001:db8::1]/",
            "http://[v1.a]/",
            "http://[V1F.future]/",
            "file:///etc/hosts",
            "foo:",
        ],
    )
    def test_valid(self, value):
        assert uris.validate_python(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            "example.com/no-scheme",
            "http://exa mple.com",
            "http://example.com/%zz",
            "http://example.com/%2",
            "http://example.com/café",
            "http://example.com/{braces}",
            "https://example.com/#one#two",
            "http://[not-ipv6]/",
            "http://example.com:abc/",
            "https://example.com\n",
            "http://example.com:\uff18\uff10/",
            "http://\uff11.0.0.1/",
            "",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            uris.validate_python(value)


class TestEmail:
    @pytest.mark.parametrize(
        "value",
        [
            "tom@foobar.example.com",
            "a+tag@example.com",
            "o'brien@example.com",
            '"quoted string"@example.com',
            '"with\\"escape"@example.com',
            "tom@[192.0.2.1]",
        ],
    )
    def test_valid(self, value):
        assert emails.validate_python(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            "a..b@example.com",
            ".a@example.com",
            "a.@example.com",
            "a@b..c",
            "a@.b",
            "a@b.",
            "a@",
            "@example.com",
            "a b@example.com",
            "a@exa mple.com",
            '"unclosed@example.com',
            "a@b@c",
            "café@example.com",
            "",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            emails.validate_python(value)


class TestLanguageTag:
    @pytest.mark.parametrize(
        "value",
        [
            "en",
            "en-US",
            "zh-Hant-TW",
            "de-DE-1901",
            "es-419",
            "zh-min-nan",
            "i-klingon",
            "x-private",
            "en-a-bbb-x-a-ccc",
            "en-US-x-twain",
        ],
    )
    def test_valid(self, value):
        assert language_tags.validate_python(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            "x",
            "i",
            "en-",
            "-en",
            "abcdefghi",
            "abcd-efg",
            "a-b-c-d",
            "en-US-",
            "de-419-DE",
            "en--US",
            "",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            language_tags.validate_python(value)


class TestVendorExtension:
    @pytest.mark.parametrize(
        "value",
        [
            "example.com:lunar",
            "a:b",
            "foo:name with spaces!",
            "sub.example.com:x",
            "3m.com:tape",
            "bücher.example:straße",
        ],
    )
    def test_valid(self, value):
        assert is_vendor_extension(value)

    @pytest.mark.parametrize(
        "value",
        [
            "foo-:bar",
            "-foo:bar",
            "foo_bar:baz",
            "foo.:bar",
            ".foo:bar",
            "foo..bar:baz",
            "foo:",
            "foo:with/solidus",
            "foo:with~tilde",
            'foo:with"quote',
            "foo:with\x01control",
            "nocolon",
        ],
    )
    def test_invalid(self, value):
        assert not is_vendor_extension(value)


class TestColor:
    @pytest.mark.parametrize("value", ["turquoise", "DarkSlateGray", "#deb887", "#00FF00"])
    def test_valid(self, value):
        assert colors.validate_python(value) == value

    @pytest.mark.parametrize(
        "value",
        ["notacolor", "rebeccapurple", "#abc", "#12345", "#1234567", "#00ff0g", "rgb(0,0,0)", ""],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            colors.validate_python(value)


class TestTimeZoneId:
    @pytest.mark.parametrize("value", ["America/New_York", "Europe/Vienna", "Etc/UTC"])
    def test_valid(self, value):
        assert tzids.validate_python(value) == value

    @pytest.mark.parametrize("value", ["Mars/Olympus_Mons", "America/NewYork", ""])
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            tzids.validate_python(value)

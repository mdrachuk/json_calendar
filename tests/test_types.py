"""Tests for the scalar value types of Section 1.5."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from json_calendar._types import (
    Duration,
    Id,
    Int,
    LocalDateTime,
    SignedDuration,
    TimeZoneId,
    UnsignedInt,
    UTCDateTime,
)

ids = TypeAdapter(Id)
ints = TypeAdapter(Int)
unsigned = TypeAdapter(UnsignedInt)
utc = TypeAdapter(UTCDateTime)
local = TypeAdapter(LocalDateTime)
durations = TypeAdapter(Duration)
signed_durations = TypeAdapter(SignedDuration)
tzids = TypeAdapter(TimeZoneId)


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
        ["P", "PT", "P1H", "1D", "PT1H2S", "P1DT", "-PT1H", "+PT1H", "P1D2W", "pt1h", "PT1.5H"],
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


class TestTimeZoneId:
    @pytest.mark.parametrize("value", ["America/New_York", "Europe/Vienna", "Etc/UTC"])
    def test_valid(self, value):
        assert tzids.validate_python(value) == value

    @pytest.mark.parametrize("value", ["Mars/Olympus_Mons", "America/NewYork", ""])
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            tzids.validate_python(value)

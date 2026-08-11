"""Tests for RecurrenceRule and NDay (Section 3.3.3)."""

import pytest
from pydantic import ValidationError

from json_calendar.models import NDay, RecurrenceRule


def rule(**props):
    return RecurrenceRule.model_validate({"frequency": "daily", **props})


class TestFrequency:
    @pytest.mark.parametrize(
        "value", ["yearly", "monthly", "weekly", "daily", "hourly", "minutely", "secondly"]
    )
    def test_valid(self, value):
        assert RecurrenceRule.model_validate({"frequency": value}).frequency == value

    def test_mandatory(self):
        with pytest.raises(ValidationError):
            RecurrenceRule.model_validate({})

    @pytest.mark.parametrize("value", ["DAILY", "Daily", "fortnightly"])
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            RecurrenceRule.model_validate({"frequency": value})


class TestParts:
    def test_defaults(self):
        r = rule()
        assert r.interval == 1
        assert r.rscale == "gregorian"
        assert r.skip == "omit"
        assert r.firstDayOfWeek == "mo"

    def test_interval_must_be_positive(self):
        assert rule(interval=2).interval == 2
        with pytest.raises(ValidationError):
            rule(interval=0)

    def test_interval_is_an_unsigned_int(self):
        assert rule(interval=2**53 - 1).interval == 2**53 - 1
        with pytest.raises(ValidationError):
            rule(interval=2**53)

    @pytest.mark.parametrize(
        "value",
        [
            "gregorian",
            "gregory",
            "chinese",
            "hebrew",
            "islamic-umalqura",
            "ethiopic-amete-alem",
            "islamicc",
        ],
    )
    def test_rscale_accepts_cldr_calendar_systems_and_aliases(self, value):
        assert rule(rscale=value).rscale == value

    def test_rscale_accepts_vendor_specific_values(self):
        assert rule(rscale="example.com:lunar").rscale == "example.com:lunar"

    @pytest.mark.parametrize(
        "value",
        ["GREGORIAN", "Chinese", "not a calendar", "klingon", "", "foo-:bar", "foo_bar:baz"],
    )
    def test_rscale_rejects_unregistered_values(self, value):
        with pytest.raises(ValidationError):
            rule(rscale=value)

    def test_skip_values(self):
        assert rule(skip="backward").skip == "backward"
        with pytest.raises(ValidationError):
            rule(skip="OMIT")

    def test_first_day_of_week(self):
        assert rule(firstDayOfWeek="su").firstDayOfWeek == "su"
        with pytest.raises(ValidationError):
            rule(firstDayOfWeek="MO")
        with pytest.raises(ValidationError):
            rule(firstDayOfWeek="monday")

    def test_by_day(self):
        r = rule(byDay=[{"day": "mo"}, {"day": "fr", "nthOfPeriod": -1}])
        assert r.byDay == [NDay(day="mo"), NDay(day="fr", nthOfPeriod=-1)]

    def test_nth_of_period_must_not_be_zero(self):
        with pytest.raises(ValidationError):
            rule(byDay=[{"day": "mo", "nthOfPeriod": 0}])

    def test_by_month_day(self):
        assert rule(byMonthDay=[1, 15, -1]).byMonthDay == [1, 15, -1]
        with pytest.raises(ValidationError):
            rule(byMonthDay=[0])
        with pytest.raises(ValidationError):
            rule(byMonthDay=[32])
        with pytest.raises(ValidationError):
            rule(byMonthDay=[])

    def test_by_month(self):
        assert rule(byMonth=["1", "12"]).byMonth == ["1", "12"]
        assert rule(rscale="chinese", byMonth=["3L"]).byMonth == ["3L"]
        with pytest.raises(ValidationError):
            rule(byMonth=["3l"])
        with pytest.raises(ValidationError):
            rule(byMonth=[3])

    @pytest.mark.parametrize("value", ["0", "00", "123", "999L", "", "\uff11\uff12", "1\uff12"])
    def test_by_month_rejects_malformed_numbers_in_any_calendar(self, value):
        with pytest.raises(ValidationError):
            rule(rscale="chinese", byMonth=[value])

    def test_by_month_allows_a_leading_zero(self):
        assert rule(byMonth=["07"]).byMonth == ["07"]

    @pytest.mark.parametrize("value", ["0", "13", "3L"])
    def test_by_month_gregorian_bounds(self, value):
        with pytest.raises(ValidationError):
            rule(byMonth=[value])

    def test_by_month_13_is_valid_outside_gregorian(self):
        assert rule(rscale="ethiopic", byMonth=["13"]).byMonth == ["13"]

    @pytest.mark.parametrize("rscale", ["gregory", "iso8601"])
    def test_by_month_bounds_apply_to_gregorian_aliases(self, rscale):
        with pytest.raises(ValidationError):
            rule(rscale=rscale, byMonth=["13"])

    def test_by_year_day(self):
        assert rule(byYearDay=[100, -366]).byYearDay == [100, -366]
        with pytest.raises(ValidationError):
            rule(byYearDay=[0])
        with pytest.raises(ValidationError):
            rule(byYearDay=[367])

    def test_by_week_no(self):
        assert rule(byWeekNo=[1, -53]).byWeekNo == [1, -53]
        with pytest.raises(ValidationError):
            rule(byWeekNo=[0])
        with pytest.raises(ValidationError):
            rule(byWeekNo=[54])

    def test_by_time_parts(self):
        r = rule(byHour=[0, 23], byMinute=[0, 59], bySecond=[0, 60])
        assert r.byHour == [0, 23]
        with pytest.raises(ValidationError):
            rule(byHour=[24])
        with pytest.raises(ValidationError):
            rule(byMinute=[60])
        with pytest.raises(ValidationError):
            rule(bySecond=[61])

    def test_by_set_position(self):
        assert rule(bySetPosition=[1, -2]).bySetPosition == [1, -2]
        with pytest.raises(ValidationError):
            rule(bySetPosition=[])


class TestBounds:
    def test_count(self):
        assert rule(count=10).count == 10

    def test_until(self):
        r = rule(until="2020-06-24T09:00:00")
        assert r.until.year == 2020

    def test_count_and_until_are_mutually_exclusive(self):
        with pytest.raises(ValidationError):
            rule(count=10, until="2020-06-24T09:00:00")


class TestRoundTrip:
    def test_json_round_trip(self):
        data = {
            "@type": "RecurrenceRule",
            "frequency": "monthly",
            "interval": 2,
            "byDay": [{"day": "we", "nthOfPeriod": 3}],
            "until": "2021-01-31T09:00:00",
        }
        assert (
            RecurrenceRule.model_validate(data).model_dump(mode="json", exclude_unset=True) == data
        )

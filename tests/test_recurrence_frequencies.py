"""Tests for expanding each "frequency" of a rule (Section 3.3.3.1).

The expected occurrence lists are ported from the RRULE examples of
RFC 5545, Section 3.8.5.3, which draft-ietf-calext-jscalendarbis-18
declares semantically equivalent (Section 3.3.3), adapted to JSCalendar:
"until" is a LocalDateTime, and the initial date-time is always the
first occurrence of the recurrence set (Section 3.3.3.1).
"""

from recurrence_helpers import at, days, event, ids


class TestDaily:
    def test_count(self):
        # RFC 5545: daily for 10 occurrences.
        assert ids(event(rule={"frequency": "daily", "count": 10})) == at(
            *[f"1997-09-{day:02d}" for day in range(2, 12)]
        )

    def test_until_is_inclusive(self):
        rule = {"frequency": "daily", "until": "1997-09-05T09:00:00"}
        assert ids(event(rule=rule)) == at("1997-09-02", "1997-09-03", "1997-09-04", "1997-09-05")

    def test_until_between_occurrences(self):
        rule = {"frequency": "daily", "until": "1997-09-05T08:59:59"}
        assert ids(event(rule=rule)) == at("1997-09-02", "1997-09-03", "1997-09-04")

    def test_interval(self):
        # RFC 5545: every other day, forever.
        assert ids(event(rule={"frequency": "daily", "interval": 2}), n=5) == at(
            "1997-09-02", "1997-09-04", "1997-09-06", "1997-09-08", "1997-09-10"
        )

    def test_interval_with_count(self):
        # RFC 5545: every 10 days, 5 occurrences.
        rule = {"frequency": "daily", "interval": 10, "count": 5}
        assert ids(event(rule=rule)) == at(
            "1997-09-02", "1997-09-12", "1997-09-22", "1997-10-02", "1997-10-12"
        )

    def test_by_month_limits(self):
        # RFC 5545: every day in January, for 3 years (daily form).
        rule = {"frequency": "daily", "byMonth": ["1"], "until": "2000-01-31T09:00:00"}
        result = ids(event(start="1998-01-01T09:00:00", rule=rule))
        assert len(result) == 93  # 31 days in January in each of 1998, 1999, 2000
        assert result[0] == "1998-01-01T09:00:00"
        assert result[31] == "1999-01-01T09:00:00"
        assert result[-1] == "2000-01-31T09:00:00"

    def test_yearly_form_of_every_january_day_is_equivalent(self):
        # RFC 5545 gives the same expansion for the yearly byDay form.
        daily = {"frequency": "daily", "byMonth": ["1"], "until": "2000-01-31T09:00:00"}
        yearly = {
            "frequency": "yearly",
            "byMonth": ["1"],
            "byDay": days(["mo", "tu", "we", "th", "fr", "sa", "su"]),
            "until": "2000-01-31T09:00:00",
        }
        start = "1998-01-01T09:00:00"
        assert ids(event(start=start, rule=daily)) == ids(event(start=start, rule=yearly))


class TestWeekly:
    def test_count(self):
        # RFC 5545: weekly for 10 occurrences.
        assert ids(event(rule={"frequency": "weekly", "count": 10})) == at(
            "1997-09-02", "1997-09-09", "1997-09-16", "1997-09-23", "1997-09-30",
            "1997-10-07", "1997-10-14", "1997-10-21", "1997-10-28", "1997-11-04",
        )  # fmt: skip

    def test_interval(self):
        # RFC 5545: every other week, forever (WKST=SU).
        rule = {"frequency": "weekly", "interval": 2, "firstDayOfWeek": "su"}
        assert ids(event(rule=rule), n=6) == at(
            "1997-09-02", "1997-09-16", "1997-09-30", "1997-10-14", "1997-10-28", "1997-11-11"
        )

    def test_by_day(self):
        # RFC 5545: weekly on Tuesday and Thursday for five weeks.
        rule = {"frequency": "weekly", "count": 10, "byDay": days(["tu", "th"])}
        assert ids(event(rule=rule)) == at(
            "1997-09-02", "1997-09-04", "1997-09-09", "1997-09-11", "1997-09-16",
            "1997-09-18", "1997-09-23", "1997-09-25", "1997-09-30", "1997-10-02",
        )  # fmt: skip

    def test_interval_with_by_day_and_week_start(self):
        # RFC 5545: every other week on Monday, Wednesday, and Friday
        # until December 24, 1997, starting on Monday, September 1, 1997.
        rule = {
            "frequency": "weekly",
            "interval": 2,
            "firstDayOfWeek": "su",
            "byDay": days(["mo", "we", "fr"]),
            "until": "1997-12-24T00:00:00",
        }
        assert ids(event(start="1997-09-01T09:00:00", rule=rule)) == at(
            "1997-09-01", "1997-09-03", "1997-09-05", "1997-09-15", "1997-09-17",
            "1997-09-19", "1997-09-29", "1997-10-01", "1997-10-03", "1997-10-13",
            "1997-10-15", "1997-10-17", "1997-10-27", "1997-10-29", "1997-10-31",
            "1997-11-10", "1997-11-12", "1997-11-14", "1997-11-24", "1997-11-26",
            "1997-11-28", "1997-12-08", "1997-12-10", "1997-12-12", "1997-12-22",
        )  # fmt: skip

    def test_interval_with_by_day_and_count(self):
        # RFC 5545: every other week on Tuesday and Thursday, for 8 occurrences.
        rule = {
            "frequency": "weekly",
            "interval": 2,
            "firstDayOfWeek": "su",
            "count": 8,
            "byDay": days(["tu", "th"]),
        }
        assert ids(event(rule=rule)) == at(
            "1997-09-02", "1997-09-04", "1997-09-16", "1997-09-18",
            "1997-09-30", "1997-10-02", "1997-10-14", "1997-10-16",
        )  # fmt: skip

    def test_week_start_changes_the_expansion(self):
        # RFC 5545: the WKST example pair (August 1997, Tuesday the 5th).
        base = {"frequency": "weekly", "interval": 2, "count": 4, "byDay": days(["tu", "su"])}
        monday = ids(event(start="1997-08-05T09:00:00", rule={**base, "firstDayOfWeek": "mo"}))
        sunday = ids(event(start="1997-08-05T09:00:00", rule={**base, "firstDayOfWeek": "su"}))
        assert monday == at("1997-08-05", "1997-08-10", "1997-08-19", "1997-08-24")
        assert sunday == at("1997-08-05", "1997-08-17", "1997-08-19", "1997-08-31")


class TestMonthly:
    def test_nth_week_day(self):
        # RFC 5545: monthly on the first Friday for 10 occurrences.
        rule = {"frequency": "monthly", "count": 10, "byDay": days([("fr", 1)])}
        assert ids(event(start="1997-09-05T09:00:00", rule=rule)) == at(
            "1997-09-05", "1997-10-03", "1997-11-07", "1997-12-05", "1998-01-02",
            "1998-02-06", "1998-03-06", "1998-04-03", "1998-05-01", "1998-06-05",
        )  # fmt: skip

    def test_first_and_last_sunday(self):
        # RFC 5545: every other month on the first and last Sunday, 10 occurrences.
        rule = {
            "frequency": "monthly",
            "interval": 2,
            "count": 10,
            "byDay": days([("su", 1), ("su", -1)]),
        }
        assert ids(event(start="1997-09-07T09:00:00", rule=rule)) == at(
            "1997-09-07", "1997-09-28", "1997-11-02", "1997-11-30", "1998-01-04",
            "1998-01-25", "1998-03-01", "1998-03-29", "1998-05-03", "1998-05-31",
        )  # fmt: skip

    def test_negative_nth_week_day(self):
        # RFC 5545: monthly on the second-to-last Monday, 6 occurrences.
        rule = {"frequency": "monthly", "count": 6, "byDay": days([("mo", -2)])}
        assert ids(event(start="1997-09-22T09:00:00", rule=rule)) == at(
            "1997-09-22", "1997-10-20", "1997-11-17", "1997-12-22", "1998-01-19", "1998-02-16"
        )

    def test_negative_month_day(self):
        # RFC 5545: monthly on the third-to-last day of the month.
        rule = {"frequency": "monthly", "count": 6, "byMonthDay": [-3]}
        assert ids(event(start="1997-09-28T09:00:00", rule=rule)) == at(
            "1997-09-28", "1997-10-29", "1997-11-28", "1997-12-29", "1998-01-29", "1998-02-26"
        )

    def test_month_days(self):
        # RFC 5545: monthly on the 2nd and 15th, 10 occurrences.
        rule = {"frequency": "monthly", "count": 10, "byMonthDay": [2, 15]}
        assert ids(event(rule=rule)) == at(
            "1997-09-02", "1997-09-15", "1997-10-02", "1997-10-15", "1997-11-02",
            "1997-11-15", "1997-12-02", "1997-12-15", "1998-01-02", "1998-01-15",
        )  # fmt: skip

    def test_first_and_last_day(self):
        # RFC 5545: monthly on the first and last day, 10 occurrences.
        rule = {"frequency": "monthly", "count": 10, "byMonthDay": [1, -1]}
        assert ids(event(start="1997-09-30T09:00:00", rule=rule)) == at(
            "1997-09-30", "1997-10-01", "1997-10-31", "1997-11-01", "1997-11-30",
            "1997-12-01", "1997-12-31", "1998-01-01", "1998-01-31", "1998-02-01",
        )  # fmt: skip

    def test_long_interval(self):
        # RFC 5545: every 18 months on the 10th thru 15th, 10 occurrences.
        rule = {
            "frequency": "monthly",
            "interval": 18,
            "count": 10,
            "byMonthDay": [10, 11, 12, 13, 14, 15],
        }
        assert ids(event(start="1997-09-10T09:00:00", rule=rule)) == at(
            "1997-09-10", "1997-09-11", "1997-09-12", "1997-09-13", "1997-09-14",
            "1997-09-15", "1999-03-10", "1999-03-11", "1999-03-12", "1999-03-13",
        )  # fmt: skip

    def test_every_week_day_of_month(self):
        # RFC 5545: every Tuesday, every other month.
        rule = {"frequency": "monthly", "interval": 2, "byDay": days(["tu"])}
        assert ids(event(rule=rule), n=10) == at(
            "1997-09-02", "1997-09-09", "1997-09-16", "1997-09-23", "1997-09-30",
            "1997-11-04", "1997-11-11", "1997-11-18", "1997-11-25", "1998-01-06",
        )  # fmt: skip

    def test_friday_the_13th(self):
        # RFC 5545: every Friday the 13th (the initial date-time is kept
        # as the first occurrence, where iCalendar used an EXDATE).
        rule = {"frequency": "monthly", "byDay": days(["fr"]), "byMonthDay": [13]}
        assert ids(event(rule=rule), n=6) == at(
            "1997-09-02", "1998-02-13", "1998-03-13", "1998-11-13", "1999-08-13", "2000-10-13"
        )

    def test_saturday_following_first_sunday(self):
        # RFC 5545: the first Saturday that follows the first Sunday.
        rule = {
            "frequency": "monthly",
            "count": 10,
            "byDay": days(["sa"]),
            "byMonthDay": [7, 8, 9, 10, 11, 12, 13],
        }
        assert ids(event(start="1997-09-13T09:00:00", rule=rule)) == at(
            "1997-09-13", "1997-10-11", "1997-11-08", "1997-12-13", "1998-01-10",
            "1998-02-07", "1998-03-07", "1998-04-11", "1998-05-09", "1998-06-13",
        )  # fmt: skip


class TestYearly:
    def test_by_month(self):
        # RFC 5545: yearly in June and July for 10 occurrences.
        rule = {"frequency": "yearly", "count": 10, "byMonth": ["6", "7"]}
        assert ids(event(start="1997-06-10T09:00:00", rule=rule)) == at(
            "1997-06-10", "1997-07-10", "1998-06-10", "1998-07-10", "1999-06-10",
            "1999-07-10", "2000-06-10", "2000-07-10", "2001-06-10", "2001-07-10",
        )  # fmt: skip

    def test_by_month_with_interval(self):
        # RFC 5545: every other year in January, February, and March, 10 times.
        rule = {"frequency": "yearly", "interval": 2, "count": 10, "byMonth": ["1", "2", "3"]}
        assert ids(event(start="1997-03-10T09:00:00", rule=rule)) == at(
            "1997-03-10", "1999-01-10", "1999-02-10", "1999-03-10", "2001-01-10",
            "2001-02-10", "2001-03-10", "2003-01-10", "2003-02-10", "2003-03-10",
        )  # fmt: skip

    def test_by_year_day(self):
        # RFC 5545: every third year on the 1st, 100th, and 200th day, 10 times.
        rule = {"frequency": "yearly", "interval": 3, "count": 10, "byYearDay": [1, 100, 200]}
        assert ids(event(start="1997-01-01T09:00:00", rule=rule)) == at(
            "1997-01-01", "1997-04-10", "1997-07-19", "2000-01-01", "2000-04-09",
            "2000-07-18", "2003-01-01", "2003-04-10", "2003-07-19", "2006-01-01",
        )  # fmt: skip

    def test_nth_week_day_of_year(self):
        # RFC 5545: the 20th Monday of the year, forever.
        rule = {"frequency": "yearly", "byDay": days([("mo", 20)])}
        assert ids(event(start="1997-05-19T09:00:00", rule=rule), n=3) == at(
            "1997-05-19", "1998-05-18", "1999-05-17"
        )

    def test_by_week_number(self):
        # RFC 5545: Monday of week number 20, forever.
        rule = {"frequency": "yearly", "byWeekNo": [20], "byDay": days(["mo"])}
        assert ids(event(start="1997-05-12T09:00:00", rule=rule), n=3) == at(
            "1997-05-12", "1998-05-11", "1999-05-17"
        )

    def test_week_day_of_month(self):
        # RFC 5545: every Thursday in March, forever.
        rule = {"frequency": "yearly", "byMonth": ["3"], "byDay": days(["th"])}
        assert ids(event(start="1997-03-13T09:00:00", rule=rule), n=11) == at(
            "1997-03-13", "1997-03-20", "1997-03-27", "1998-03-05", "1998-03-12",
            "1998-03-19", "1998-03-26", "1999-03-04", "1999-03-11", "1999-03-18",
            "1999-03-25",
        )  # fmt: skip

    def test_week_day_of_months(self):
        # RFC 5545: every Thursday in June, July, and August, forever.
        rule = {"frequency": "yearly", "byDay": days(["th"]), "byMonth": ["6", "7", "8"]}
        assert ids(event(start="1997-06-05T09:00:00", rule=rule), n=14) == at(
            "1997-06-05", "1997-06-12", "1997-06-19", "1997-06-26", "1997-07-03",
            "1997-07-10", "1997-07-17", "1997-07-24", "1997-07-31", "1997-08-07",
            "1997-08-14", "1997-08-21", "1997-08-28", "1998-06-04",
        )  # fmt: skip

    def test_election_day(self):
        # RFC 5545: US Presidential Election day, every 4 years.
        rule = {
            "frequency": "yearly",
            "interval": 4,
            "byMonth": ["11"],
            "byDay": days(["tu"]),
            "byMonthDay": [2, 3, 4, 5, 6, 7, 8],
        }
        assert ids(event(start="1996-11-05T09:00:00", rule=rule), n=3) == at(
            "1996-11-05", "2000-11-07", "2004-11-02"
        )


class TestTimeFrequencies:
    def test_hourly(self):
        # RFC 5545: every 3 hours from 9:00 to 17:00 on a specific day.
        rule = {"frequency": "hourly", "interval": 3, "until": "1997-09-02T17:00:00"}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T12:00:00", "1997-09-02T15:00:00",
        ]  # fmt: skip

    def test_minutely(self):
        # RFC 5545: every 15 minutes for 6 occurrences.
        rule = {"frequency": "minutely", "interval": 15, "count": 6}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T09:15:00", "1997-09-02T09:30:00",
            "1997-09-02T09:45:00", "1997-09-02T10:00:00", "1997-09-02T10:15:00",
        ]  # fmt: skip

    def test_minutely_long_interval(self):
        # RFC 5545: every hour and a half for 4 occurrences.
        rule = {"frequency": "minutely", "interval": 90, "count": 4}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T10:30:00",
            "1997-09-02T12:00:00", "1997-09-02T13:30:00",
        ]  # fmt: skip

    def test_daily_with_by_hour_and_by_minute(self):
        # RFC 5545: every 20 minutes from 9:00 to 16:40 every day.
        rule = {
            "frequency": "daily",
            "byHour": [9, 10, 11, 12, 13, 14, 15, 16],
            "byMinute": [0, 20, 40],
        }
        result = ids(event(rule=rule), n=25)
        assert result[:5] == [
            "1997-09-02T09:00:00", "1997-09-02T09:20:00", "1997-09-02T09:40:00",
            "1997-09-02T10:00:00", "1997-09-02T10:20:00",
        ]  # fmt: skip
        assert result[23] == "1997-09-02T16:40:00"
        assert result[24] == "1997-09-03T09:00:00"

    def test_minutely_form_is_equivalent(self):
        # RFC 5545 gives the same expansion for the minutely form.
        daily = {
            "frequency": "daily",
            "byHour": [9, 10, 11, 12, 13, 14, 15, 16],
            "byMinute": [0, 20, 40],
        }
        minutely = {
            "frequency": "minutely",
            "interval": 20,
            "byHour": [9, 10, 11, 12, 13, 14, 15, 16],
        }
        assert ids(event(rule=daily), n=48) == ids(event(rule=minutely), n=48)

    def test_secondly(self):
        rule = {"frequency": "secondly", "interval": 20, "count": 4}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T09:00:20",
            "1997-09-02T09:00:40", "1997-09-02T09:01:00",
        ]  # fmt: skip

    def test_leap_second_candidates_are_dropped(self):
        # bySecond allows 60 (Section 3.3.3), which no real date-time reaches.
        rule = {"frequency": "minutely", "count": 3, "bySecond": [0, 60]}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T09:01:00", "1997-09-02T09:02:00",
        ]  # fmt: skip

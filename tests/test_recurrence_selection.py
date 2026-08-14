"""Tests for the steps applied within a period (Section 3.3.3.1).

A period's candidates are adjusted by "skip" when the byX properties name
an invalid date (step 2.2), and then selected from by "bySetPosition".
"""

from recurrence_helpers import at, days, event, ids


class TestSetPosition:
    def test_positive(self):
        # RFC 5545: the 3rd instance of Tuesday, Wednesday, or Thursday.
        rule = {
            "frequency": "monthly",
            "count": 3,
            "byDay": days(["tu", "we", "th"]),
            "bySetPosition": [3],
        }
        assert ids(event(start="1997-09-04T09:00:00", rule=rule)) == at(
            "1997-09-04", "1997-10-07", "1997-11-06"
        )

    def test_negative(self):
        # RFC 5545: the second-to-last weekday of the month.
        rule = {
            "frequency": "monthly",
            "byDay": days(["mo", "tu", "we", "th", "fr"]),
            "bySetPosition": [-2],
        }
        assert ids(event(start="1997-09-29T09:00:00", rule=rule), n=7) == at(
            "1997-09-29", "1997-10-30", "1997-11-27", "1997-12-30",
            "1998-01-29", "1998-02-26", "1998-03-30",
        )  # fmt: skip

    def test_selects_within_a_sub_daily_period(self):
        # Every period of a "secondly" rule holds exactly one candidate, so
        # only the first (equivalently, the last) position selects it.
        rule = {"frequency": "secondly", "count": 3, "bySetPosition": [1]}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T09:00:01", "1997-09-02T09:00:02",
        ]  # fmt: skip

    def test_out_of_range_position_empties_a_sub_daily_period(self):
        # There is never a second candidate to select, so nothing follows the
        # initial date-time, which is an occurrence regardless of the rule.
        rule = {"frequency": "secondly", "bySetPosition": [2], "until": "1997-09-02T09:01:00"}
        assert ids(event(rule=rule), n=2) == ["1997-09-02T09:00:00"]

    def test_duplicate_by_values_share_one_position(self):
        # A repeated "byMinute" value is one candidate, not two: the times of
        # a period are a set.
        rule = {"frequency": "hourly", "count": 3, "byMinute": [30, 30], "bySetPosition": [1]}
        assert ids(event(rule=rule)) == [
            "1997-09-02T09:00:00", "1997-09-02T09:30:00", "1997-09-02T10:30:00",
        ]  # fmt: skip

    def test_duplicate_by_values_do_not_fill_later_positions(self):
        # ...so there is no second candidate for position 2 to select.
        rule = {"frequency": "minutely", "bySecond": [15, 15], "bySetPosition": [2]}
        assert ids(event(rule=rule), n=2) == ["1997-09-02T09:00:00"]


class TestSkip:
    def test_omit_is_the_default(self):
        # RFC 5545 erratum example: the 15th and 30th of every month.
        rule = {"frequency": "monthly", "count": 5, "byMonthDay": [15, 30]}
        assert ids(event(start="2007-01-15T09:00:00", rule=rule)) == at(
            "2007-01-15", "2007-01-30", "2007-02-15", "2007-03-15", "2007-03-30"
        )

    def test_omit_leap_day(self):
        rule = {"frequency": "yearly"}
        assert ids(event(start="2020-02-29T09:00:00", rule=rule), n=2) == at(
            "2020-02-29", "2024-02-29"
        )

    def test_backward_leap_day(self):
        rule = {"frequency": "yearly", "skip": "backward"}
        assert ids(event(start="2020-02-29T09:00:00", rule=rule), n=5) == at(
            "2020-02-29", "2021-02-28", "2022-02-28", "2023-02-28", "2024-02-29"
        )

    def test_forward_leap_day(self):
        rule = {"frequency": "yearly", "skip": "forward"}
        assert ids(event(start="2020-02-29T09:00:00", rule=rule), n=5) == at(
            "2020-02-29", "2021-03-01", "2022-03-01", "2023-03-01", "2024-02-29"
        )

    def test_backward_month_end(self):
        # RFC 7529: monthly on the 31st, skipping backward.
        rule = {"frequency": "monthly", "skip": "backward"}
        assert ids(event(start="2014-01-31T09:00:00", rule=rule), n=5) == at(
            "2014-01-31", "2014-02-28", "2014-03-31", "2014-04-30", "2014-05-31"
        )

    def test_forward_month_end(self):
        rule = {"frequency": "monthly", "skip": "forward"}
        assert ids(event(start="2014-01-30T09:00:00", rule=rule), n=5) == at(
            "2014-01-30", "2014-03-01", "2014-03-30", "2014-04-30", "2014-05-30"
        )

    def test_forward_deduplicates_across_periods(self):
        # February 30th becomes March 1st, which the March period generates
        # again; the duplicate is eliminated (Section 3.3.3.1, step 5).
        rule = {"frequency": "monthly", "skip": "forward", "byMonthDay": [1, 30]}
        assert ids(event(start="2014-01-01T09:00:00", rule=rule), n=7) == at(
            "2014-01-01", "2014-01-30", "2014-02-01", "2014-03-01",
            "2014-03-30", "2014-04-01", "2014-04-30",
        )  # fmt: skip

    def test_backward_deduplicates_within_a_period(self):
        # February 30th and 31st both become February 28th (step 2.3).
        rule = {"frequency": "monthly", "skip": "backward", "byMonthDay": [30, 31]}
        assert ids(event(start="2014-01-30T09:00:00", rule=rule), n=5) == at(
            "2014-01-30", "2014-01-31", "2014-02-28", "2014-03-30", "2014-03-31"
        )

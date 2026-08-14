"""Tests for the recurrence set of an Event or Task (Sections 3.3 and 3.3.4).

The occurrences of an object are its initial date-time, the date-times of
its "recurrenceRule", and the occurrences its "recurrenceOverrides" add,
exclude, or modify; ``expand`` yields them in recurrence id order, and
``Occurrence.materialize`` turns one into a standalone instance object.
"""

import pytest

from json_calendar.models import Event, Task
from json_calendar.recurrence import Occurrence, UnsupportedCalendarError, expand
from recurrence_helpers import at, days, dt, event, ids, task


class TestNonRecurring:
    def test_plain_event_yields_its_start(self):
        assert ids(event()) == ["1997-09-02T09:00:00"]

    def test_occurrence_fields(self):
        e = event()
        (occurrence,) = expand(e)
        assert isinstance(occurrence, Occurrence)
        assert occurrence.base is e
        assert occurrence.recurrence_id == dt("1997-09-02T09:00:00")
        assert occurrence.start == dt("1997-09-02T09:00:00")
        assert occurrence.patch is None

    def test_task_with_start_yields_its_start(self):
        assert ids(task(start="2020-03-01T09:00:00")) == ["2020-03-01T09:00:00"]

    def test_task_with_due_only_yields_its_due(self):
        assert ids(task(due="2020-03-01T12:00:00")) == ["2020-03-01T12:00:00"]

    def test_untimed_task_yields_nothing(self):
        assert ids(task()) == []

    def test_instance_object_yields_itself(self):
        instance = event(recurrenceId="1997-09-05T09:00:00")
        (occurrence,) = expand(instance)
        assert occurrence.recurrence_id == dt("1997-09-05T09:00:00")
        assert occurrence.start == dt("1997-09-02T09:00:00")
        assert occurrence.materialize() is instance


class TestInitialDateTime:
    def test_start_not_matching_the_rule_is_the_first_occurrence(self):
        # 1997-09-02 is a Tuesday; the rule only generates Mondays.
        rule = {"frequency": "weekly", "byDay": days(["mo"])}
        assert ids(event(rule=rule), n=3) == at("1997-09-02", "1997-09-08", "1997-09-15")

    def test_start_counts_toward_count(self):
        rule = {"frequency": "weekly", "count": 3, "byDay": days(["mo"])}
        assert ids(event(rule=rule)) == at("1997-09-02", "1997-09-08", "1997-09-15")

    def test_start_matching_the_rule_is_not_duplicated(self):
        rule = {"frequency": "daily", "count": 3}
        assert ids(event(rule=rule)) == at("1997-09-02", "1997-09-03", "1997-09-04")

    def test_candidates_before_the_start_are_eliminated(self):
        # The first monthly period contains days before the start (step 4).
        rule = {"frequency": "monthly", "count": 3, "byMonthDay": [2, 20]}
        assert ids(event(start="1997-09-20T09:00:00", rule=rule)) == at(
            "1997-09-20", "1997-10-02", "1997-10-20"
        )

    def test_task_recurs_by_its_start(self):
        t = task(
            start="2020-03-01T09:00:00",
            due="2020-03-03T09:00:00",
            recurrenceRule={"frequency": "weekly", "count": 2},
        )
        assert ids(t) == ["2020-03-01T09:00:00", "2020-03-08T09:00:00"]


class TestPathologicalRules:
    def test_empty_rule_terminates(self):
        # February 30th never exists; the rule generates nothing, but the
        # initial date-time is still the first occurrence.
        rule = {"frequency": "yearly", "byMonth": ["2"], "byMonthDay": [30]}
        assert ids(event(start="2020-01-15T09:00:00", rule=rule)) == ["2020-01-15T09:00:00"]

    def test_zero_count_yields_nothing(self):
        assert ids(event(rule={"frequency": "daily", "count": 0})) == []


class TestRscale:
    @pytest.mark.parametrize("rscale", ["gregorian", "gregory", "iso8601"])
    def test_gregorian_aliases_are_supported(self, rscale):
        rule = {"frequency": "daily", "count": 2, "rscale": rscale}
        assert ids(event(rule=rule)) == at("1997-09-02", "1997-09-03")

    @pytest.mark.parametrize("rscale", ["hebrew", "chinese", "islamic-umalqura", "example.com:x"])
    def test_other_calendar_systems_raise(self, rscale):
        e = event(rule={"frequency": "yearly", "rscale": rscale})
        with pytest.raises(UnsupportedCalendarError):
            expand(e)


DAILY_5 = {"frequency": "daily", "count": 5}  # 1997-09-02 .. 1997-09-06


class TestOverrides:
    def test_excluded_removes_the_occurrence(self):
        e = event(rule=DAILY_5, overrides={"1997-09-04T09:00:00": {"excluded": True}})
        assert ids(e) == at("1997-09-02", "1997-09-03", "1997-09-05", "1997-09-06")

    def test_excluded_non_generated_id_is_a_no_op(self):
        e = event(rule=DAILY_5, overrides={"1997-10-01T09:00:00": {"excluded": True}})
        assert ids(e) == at("1997-09-02", "1997-09-03", "1997-09-04", "1997-09-05", "1997-09-06")

    def test_modifying_override_keeps_the_recurrence_id(self):
        e = event(rule=DAILY_5, overrides={"1997-09-04T09:00:00": {"title": "Changed"}})
        assert ids(e) == at("1997-09-02", "1997-09-03", "1997-09-04", "1997-09-05", "1997-09-06")
        overridden = [o for o in expand(e) if o.patch is not None]
        assert len(overridden) == 1
        assert overridden[0].recurrence_id == dt("1997-09-04T09:00:00")
        assert overridden[0].patch == {"title": "Changed"}

    def test_patched_start_takes_precedence(self):
        e = event(rule=DAILY_5, overrides={"1997-09-04T09:00:00": {"start": "1997-09-04T14:00:00"}})
        (occurrence,) = [o for o in expand(e) if o.patch is not None]
        assert occurrence.recurrence_id == dt("1997-09-04T09:00:00")
        assert occurrence.start == dt("1997-09-04T14:00:00")

    def test_non_generated_id_is_an_additional_occurrence(self):
        e = event(rule=DAILY_5, overrides={"1997-09-10T10:00:00": {}})
        assert ids(e) == [
            *at("1997-09-02", "1997-09-03", "1997-09-04", "1997-09-05", "1997-09-06"),
            "1997-09-10T10:00:00",
        ]

    def test_additional_occurrences_merge_in_order(self):
        e = event(
            rule=DAILY_5,
            overrides={"1997-09-04T15:00:00": {}, "1997-09-03T15:00:00": {}},
        )
        assert ids(e) == [
            "1997-09-02T09:00:00", "1997-09-03T09:00:00", "1997-09-03T15:00:00",
            "1997-09-04T09:00:00", "1997-09-04T15:00:00", "1997-09-05T09:00:00",
            "1997-09-06T09:00:00",
        ]  # fmt: skip

    def test_override_may_precede_the_start(self):
        # Section 3.3.4: the recurrence id may occur before the original start.
        e = event(overrides={"1997-08-30T09:00:00": {}})
        assert ids(e) == at("1997-08-30", "1997-09-02")

    def test_overrides_without_a_rule(self):
        e = event(overrides={"1997-09-09T09:00:00": {}, "1997-09-16T09:00:00": {}})
        assert ids(e) == at("1997-09-02", "1997-09-09", "1997-09-16")

    def test_override_of_the_initial_occurrence(self):
        e = event(overrides={"1997-09-02T09:00:00": {"title": "First"}})
        (occurrence,) = expand(e)
        assert occurrence.patch == {"title": "First"}

    def test_task_due_only_overrides(self):
        # Every occurrence has "recurrenceId" set, which requires a "start"
        # (Section 4.2.2), so the patch of a due-only Task must supply one.
        t = task(
            due="2020-03-01T12:00:00",
            recurrenceOverrides={"2020-03-08T12:00:00": {"start": "2020-03-08T11:00:00"}},
        )
        assert ids(t) == ["2020-03-01T12:00:00", "2020-03-08T12:00:00"]


class TestWindow:
    def test_start_inclusive_end_exclusive(self):
        e = event(rule=DAILY_5)
        result = ids(e, start=dt("1997-09-03T09:00:00"), end=dt("1997-09-05T09:00:00"))
        assert result == at("1997-09-03", "1997-09-04")

    def test_window_on_an_infinite_rule(self):
        e = event(rule={"frequency": "daily"})
        result = ids(e, start=dt("1998-01-01T00:00:00"), end=dt("1998-01-04T00:00:00"))
        assert result == at("1998-01-01", "1998-01-02", "1998-01-03")

    def test_patched_start_moves_out_of_the_window(self):
        e = event(rule=DAILY_5, overrides={"1997-09-04T09:00:00": {"start": "1997-09-20T09:00:00"}})
        result = ids(e, start=dt("1997-09-03T09:00:00"), end=dt("1997-09-05T09:00:00"))
        assert result == at("1997-09-03")

    def test_patched_start_moves_into_the_window(self):
        e = event(
            rule=DAILY_5,
            overrides={"1997-09-10T09:00:00": {"start": "1997-09-03T10:00:00"}},
        )
        result = ids(e, start=dt("1997-09-03T09:00:00"), end=dt("1997-09-05T09:00:00"))
        assert result == ["1997-09-03T09:00:00", "1997-09-04T09:00:00", "1997-09-10T09:00:00"]
        (added,) = [o for o in expand(e, start=dt("1997-09-03T09:00:00")) if o.patch]
        assert added.start == dt("1997-09-03T10:00:00")


class TestMaterialize:
    def test_rule_occurrence(self):
        e = event(rule=DAILY_5, title="Standup", timeZone="America/New_York", duration="PT15M")
        occurrence = list(expand(e))[2]
        instance = occurrence.materialize()
        assert isinstance(instance, Event)
        assert instance.start == dt("1997-09-04T09:00:00")
        assert instance.recurrenceId == dt("1997-09-04T09:00:00")
        assert instance.recurrenceIdTimeZone == "America/New_York"
        assert instance.title == "Standup"
        assert instance.duration == "PT15M"
        assert instance.uid == e.uid
        assert instance.recurrenceRule is None
        assert instance.recurrenceOverrides is None

    def test_patched_occurrence(self):
        e = event(
            rule=DAILY_5,
            title="Standup",
            overrides={"1997-09-04T09:00:00": {"title": "Retro", "duration": "PT1H"}},
        )
        (occurrence,) = [o for o in expand(e) if o.patch is not None]
        instance = occurrence.materialize()
        assert isinstance(instance, Event)
        assert instance.title == "Retro"
        assert instance.duration == "PT1H"
        assert instance.start == dt("1997-09-04T09:00:00")
        assert instance.recurrenceId == dt("1997-09-04T09:00:00")

    def test_non_recurring_object_is_returned_as_is(self):
        e = event(title="Standup")
        (occurrence,) = expand(e)
        assert occurrence.materialize() is e

    def test_non_recurring_due_only_task_is_returned_as_is(self):
        # A Task with no "start" must not be given a "recurrenceId" (Section 4.2).
        t = task(due="2020-03-01T12:00:00")
        (occurrence,) = expand(t)
        assert occurrence.materialize() is t

    def test_due_only_task_shifts_due(self):
        t = task(
            due="2020-03-01T12:00:00",
            recurrenceOverrides={"2020-03-08T12:00:00": {"start": "2020-03-08T11:00:00"}},
        )
        instance = list(expand(t))[1].materialize()
        assert isinstance(instance, Task)
        assert instance.due == dt("2020-03-08T12:00:00")
        assert instance.start == dt("2020-03-08T11:00:00")

    def test_task_with_start_and_due_shifts_only_start(self):
        t = task(
            start="2020-03-01T09:00:00",
            due="2020-03-03T09:00:00",
            recurrenceRule={"frequency": "weekly", "count": 2},
        )
        instance = list(expand(t))[1].materialize()
        assert isinstance(instance, Task)
        assert instance.start == dt("2020-03-08T09:00:00")
        assert instance.due == dt("2020-03-03T09:00:00")

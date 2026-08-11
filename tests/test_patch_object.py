"""Tests for PatchObject (Section 1.5.9) and recurrence overrides (Section 3.3.4)."""

import pytest
from pydantic import TypeAdapter, ValidationError

from json_calendar import Event, PatchObject, Task

MASTER = {
    "@type": "Event",
    "version": "2.0",
    "uid": "e5c5d63b-0e40-4c72-b0b9-b6759f9505fa",
    "updated": "2020-01-02T18:23:04Z",
    "title": "Weekly sync",
    "start": "2020-01-07T14:00:00",
    "timeZone": "Europe/Berlin",
    "duration": "PT1H",
    "recurrenceRule": {"frequency": "weekly"},
    "locations": {"1": {"name": "Room A"}},
    "keywords": {"a/b": True},
    "example.com:tags": ["red", "green", "blue"],
    "example.com:items": [{"x": 1}, {"x": 2}],
    "example.com:map": {"a/b": {"x": 1}},
}

OCCURRENCE = "2020-01-14T14:00:00"


def event(patch, **master):
    data = {**MASTER, **master, "recurrenceOverrides": {OCCURRENCE: patch}}
    return Event.model_validate(data)


def rejects(patch, **master):
    with pytest.raises(ValidationError):
        event(patch, **master)


class TestPatchObjectType:
    """Checks the PatchObject type enforces without an object to patch against."""

    adapter = TypeAdapter(PatchObject)

    def test_accepts_disjoint_pointers(self):
        self.adapter.validate_python({"title": "x", "locations/1/name": "y", "a/b": 1, "a/c": 2})

    def test_rejects_prefix_collisions(self):
        # The example of Section 1.5.9, condition 3.
        with pytest.raises(ValidationError):
            self.adapter.validate_python({"alerts/1/offset": "PT0S", "alerts": {}})

    def test_prefixes_compare_by_reference_token_not_by_string(self):
        self.adapter.validate_python({"a": 1, "a~1b": 2})  # "a" and the single token "a/b"

    @pytest.mark.parametrize("key", ["x~", "x~2y", "a/b~/c"])
    def test_rejects_invalid_escape_sequences(self, key):
        with pytest.raises(ValidationError):
            self.adapter.validate_python({key: 1})

    def test_value_validity_is_only_checked_against_a_target(self):
        self.adapter.validate_python({"priority": 999})


class TestPointerEvaluation:
    """Pointer escapes and path existence (Section 1.5.9, condition 2)."""

    def test_escaped_solidus_resolves_to_a_map_key(self):
        assert event({"example.com:map/a~1b/x": 2})
        assert event({"keywords/a~1b": None})

    def test_escapes_are_not_confused(self):
        rejects({"example.com:map/a~0b/x": 2})  # "a~b" is not a key, "a/b" is

    def test_reference_tokens_prior_to_the_last_must_exist(self):
        rejects({"locations/2/name": "x"})
        rejects({"nowhere/deep": 1})

    def test_the_last_reference_token_may_be_an_addition(self):
        assert event({"locations/1/description": "second floor"})
        assert event({"locations/2": {"name": "Room B"}})

    def test_must_not_reference_into_a_scalar(self):
        rejects({"title/0": "x"})

    def test_rejects_an_empty_pointer(self):
        rejects({"": 1})


class TestArrayReferences:
    """Patching inside arrays (Section 1.5.9, condition 1)."""

    def test_may_replace_an_existing_array_member(self):
        assert event({"example.com:tags/1": "teal"})

    def test_may_patch_inside_an_array_member(self):
        assert event({"example.com:items/0/x": 42})
        assert event({"example.com:items/0/x": None})  # the last token is not an index

    def test_array_members_must_not_be_removed(self):
        rejects({"example.com:tags/1": None})

    def test_must_not_use_dash_as_an_array_index(self):
        rejects({"example.com:tags/-": "x"})

    def test_the_indexed_member_must_exist(self):
        rejects({"example.com:tags/5": "x"})
        rejects({"example.com:items/5/x": 1})

    @pytest.mark.parametrize("token", ["first", "01", "-1"])
    def test_rejects_tokens_that_are_not_array_indices(self, token):
        rejects({f"example.com:tags/{token}": "x"})


class TestPrefixCollisions:
    """No pointer may prefix another (Section 1.5.9, condition 3)."""

    def test_rejects_a_pointer_that_prefixes_another(self):
        rejects({"locations": {"1": {"name": "Room B"}}, "locations/1/name": "Room C"})

    def test_string_prefixes_of_whole_tokens_do_not_collide(self):
        assert event({"title": "a", "titleFoo": "b"})

    def test_ignored_pointers_still_count(self):
        rejects({"uid": "x", "uid/y": 1})


class TestPatchedValueValidity:
    """Patched values must be valid for the property being set (condition 4)."""

    def test_rejects_out_of_range_values(self):
        assert event({"priority": 5})
        rejects({"priority": 999})

    def test_rejects_values_of_the_wrong_type(self):
        rejects({"title": 42})
        rejects({"locations/1/name": 42})
        rejects({"start": "bogus"})

    def test_added_properties_must_have_valid_names(self):
        assert event({"futureProperty": 1})
        rejects({"not a valid name": 1})

    def test_null_removes_only_optional_properties(self):
        assert event({"locale": None})
        rejects({"updated": None})
        rejects({"start": None})

    def test_null_removal_of_an_absent_property_is_a_noop(self):
        assert event({"color": None})

    def test_the_patched_occurrence_must_satisfy_cross_property_invariants(self):
        assert event({"timeZone": None})
        rejects({"timeZone": None}, endTimeZone="Asia/Tokyo")
        rejects({"locations": None}, mainLocationId="1")

    def test_one_invalid_patch_rejects_the_patch_object_in_its_entirety(self):
        rejects({"description": "fine", "priority": 999})

    def test_one_invalid_override_rejects_the_calendar_object(self):
        with pytest.raises(ValidationError):
            Event.model_validate(
                {
                    **MASTER,
                    "recurrenceOverrides": {
                        "2020-01-14T14:00:00": {"title": "ok"},
                        "2020-01-21T14:00:00": {"priority": 999},
                    },
                }
            )


class TestIgnoredPointers:
    """Pointers that MUST be ignored in recurrence overrides (Section 3.3.4)."""

    @pytest.mark.parametrize(
        "prop",
        [
            "@type",
            "method",
            "organizerCalendarAddress",
            "privacy",
            "prodId",
            "recurrenceId",
            "recurrenceIdTimeZone",
            "sentBy",
            "uid",
        ],
    )
    def test_exactly_matching_pointers_are_ignored(self, prop):
        # The value would be invalid everywhere, so validity proves the patch is ignored.
        assert event({prop: 12345})

    @pytest.mark.parametrize(
        "key",
        [
            "recurrenceRule",
            "recurrenceRule/frequency",
            "recurrenceOverrides",
            "recurrenceOverrides/2020-01-01T00:00:00",
            "relatedTo",
            "relatedTo/some-uid/relation",
        ],
    )
    def test_pointers_starting_with_recurrence_or_relation_tokens_are_ignored(self, key):
        assert event({key: 12345})

    def test_participant_calendar_addresses_are_ignored(self):
        master = {
            "organizerCalendarAddress": "mailto:organizer@example.com",
            "participants": {
                "1": {"name": "Tom", "calendarAddress": "mailto:tom@example.com"},
            },
        }
        assert event({"participants/1/calendarAddress": 12345}, **master)
        rejects({"participants/1/name": 12345}, **master)
        rejects({"participants/1/calendarAddress/0": "x"}, **master)  # not an exact match


class TestOccurrenceSemantics:
    """How overrides apply to occurrences (Section 3.3.4)."""

    def test_an_empty_patch_is_valid(self):
        assert event({})

    def test_start_may_be_patched(self):
        assert event({"start": "2020-01-14T09:00:00"})

    def test_start_may_move_before_the_master_start(self):
        assert event({"start": "2019-12-01T09:00:00"})

    def test_unset_defaults_do_not_become_set_on_the_occurrence(self):
        # A name-only participant is only valid while "participationStatus" and
        # "expectReply" remain unset, so the occurrence must not set them either.
        assert event({}, participants={"1": {"name": "Tom"}})
        assert event({"participants/1/name": "Tim"}, participants={"1": {"name": "Tom"}})


TASK_MASTER = {
    "@type": "Task",
    "version": "2.0",
    "uid": "0af5e0cf-15fb-4e94-a48f-eb4f0f545c78",
    "updated": "2020-01-02T18:23:04Z",
    "title": "Water plants",
    "start": "2020-01-07T14:00:00",
    "due": "2020-01-09T14:00:00",
    "recurrenceRule": {"frequency": "weekly"},
}


class TestTaskOverrides:
    def task(self, patch):
        return Task.model_validate({**TASK_MASTER, "recurrenceOverrides": {OCCURRENCE: patch}})

    def test_patches_validate_against_the_task_model(self):
        assert self.task({"percentComplete": 50})
        with pytest.raises(ValidationError):
            self.task({"percentComplete": 150})

    def test_optional_due_may_be_removed(self):
        assert self.task({"due": None})

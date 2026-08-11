"""Tests for the Group object (Sections 2.3 and 4.3)."""

import pytest
from pydantic import ValidationError

from json_calendar import Event, Group, Task

EVENT_ENTRY = {
    "@type": "Event",
    "uid": "a8df6573-0474-496d-8496-033ad45d7fea",
    "updated": "2020-01-02T18:23:04Z",
    "title": "Some event",
    "start": "2020-01-15T13:00:00",
    "timeZone": "America/New_York",
    "duration": "PT1H",
}

TASK_ENTRY = {
    "@type": "Task",
    "uid": "2a358cee-6489-4f14-a57f-c104db4dc2f2",
    "updated": "2020-01-09T14:32:01Z",
    "title": "Do something",
}

SIMPLE = {
    "@type": "Group",
    "version": "2.0",
    "uid": "bf0ac22b-4989-4caf-9ebd-54301b4ee51a",
    "updated": "2020-01-15T18:00:00Z",
    "title": "A simple group",
    "entries": [EVENT_ENTRY, TASK_ENTRY],
}


class TestGroup:
    def test_parses_simple_group(self):
        group = Group.model_validate(SIMPLE)
        assert isinstance(group.entries[0], Event)
        assert isinstance(group.entries[1], Task)

    def test_json_round_trip(self):
        group = Group.model_validate(SIMPLE)
        assert group.model_dump(mode="json", exclude_unset=True) == SIMPLE

    @pytest.mark.parametrize("field", ["@type", "version", "uid", "updated", "entries"])
    def test_mandatory_fields(self, field):
        with pytest.raises(ValidationError):
            Group.model_validate({k: v for k, v in SIMPLE.items() if k != field})

    def test_rejects_unregistered_version(self):
        with pytest.raises(ValidationError):
            Group.model_validate({**SIMPLE, "version": "99.99"})

    def test_type_cannot_be_populated_by_field_name(self):
        data = {k: v for k, v in SIMPLE.items() if k != "@type"}
        with pytest.raises(ValidationError):
            Group.model_validate({**data, "type": "Group"})

    def test_entries_must_set_their_type(self):
        entry = {k: v for k, v in EVENT_ENTRY.items() if k != "@type"}
        with pytest.raises(ValidationError):
            Group.model_validate({**SIMPLE, "entries": [entry]})

    def test_entries_must_not_set_version(self):
        entry = {**EVENT_ENTRY, "version": "2.0"}
        with pytest.raises(ValidationError):
            Group.model_validate({**SIMPLE, "entries": [entry]})

    def test_entry_with_recurrence_overrides_is_valid_without_version(self):
        entry = {
            **EVENT_ENTRY,
            "recurrenceRule": {"frequency": "weekly"},
            "recurrenceOverrides": {"2020-01-22T13:00:00": {"title": "Rescheduled"}},
        }
        assert Group.model_validate({**SIMPLE, "entries": [entry]})

    def test_invalid_entry_is_rejected(self):
        entry = {k: v for k, v in EVENT_ENTRY.items() if k != "start"}
        with pytest.raises(ValidationError):
            Group.model_validate({**SIMPLE, "entries": [entry]})

    def test_entries_of_unknown_type_are_preserved(self):
        data = {**SIMPLE, "entries": [EVENT_ENTRY, TASK_ENTRY, {"@type": "Note", "text": "hello"}]}
        group = Group.model_validate(data)
        assert len(group.entries) == 3
        assert group.model_dump(mode="json", exclude_unset=True) == data

    def test_source_must_be_a_uri(self):
        assert Group.model_validate({**SIMPLE, "source": "https://example.com/cal.json"})
        with pytest.raises(ValidationError):
            Group.model_validate({**SIMPLE, "source": "not a uri"})

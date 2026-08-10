import pytest

import json_calendar
from json_calendar.models import Event, Group, Task


def test_version() -> None:
    assert json_calendar.__version__


def test_event_round_trip() -> None:
    data = {"@type": "Event", "uid": "2a358cee-6489-4f14-a57f-c104db4dc357"}
    event = Event.model_validate(data)
    assert event.uid == "2a358cee-6489-4f14-a57f-c104db4dc357"
    assert event.model_dump(exclude_unset=True) == data


def test_event_rejects_wrong_type() -> None:
    with pytest.raises(ValueError):
        Event.model_validate({"@type": "Task", "uid": "x"})


def test_unknown_properties_are_preserved() -> None:
    data = {"@type": "Event", "uid": "x", "example.com/custom": {"foo": 1}}
    event = Event.model_validate(data)
    assert event.model_dump(exclude_unset=True) == data


def test_group_entries() -> None:
    group = Group.model_validate(
        {
            "@type": "Group",
            "uid": "g1",
            "entries": [
                {"@type": "Event", "uid": "e1"},
                {"@type": "Task", "uid": "t1"},
            ],
        }
    )
    assert isinstance(group.entries[0], Event)
    assert isinstance(group.entries[1], Task)

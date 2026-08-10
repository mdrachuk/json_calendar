"""Tests for the Task object (Sections 2.2, 3, and 4.2)."""

import pytest
from pydantic import ValidationError

from json_calendar import Task

SIMPLE = {
    "@type": "Task",
    "version": "2.0",
    "uid": "2a358cee-6489-4f14-a57f-c104db4dc2f2",
    "updated": "2020-01-09T14:32:01Z",
    "title": "Do something",
}


def task(**overrides):
    data = {**SIMPLE, **overrides}
    return Task.model_validate({k: v for k, v in data.items() if v is not None})


class TestBasics:
    def test_parses_simple_task(self):
        parsed = task()
        assert parsed.uid == "2a358cee-6489-4f14-a57f-c104db4dc2f2"
        assert parsed.title == "Do something"

    def test_json_round_trip(self):
        assert task().model_dump(mode="json", exclude_unset=True) == SIMPLE

    def test_rejects_wrong_type_name(self):
        with pytest.raises(ValidationError):
            task(**{"@type": "Event"})


class TestDates:
    def test_task_with_due_date(self):
        parsed = task(due="2020-01-19T18:00:00", timeZone="Europe/Vienna")
        assert parsed.due.year == 2020

    def test_time_zone_requires_due_or_start(self):
        # Draft-18 states this condition inverted, contradicting its own
        # example 5.2; we implement the reading consistent with the examples.
        with pytest.raises(ValidationError):
            task(timeZone="Europe/Vienna")

    def test_show_without_time_requires_due_or_start(self):
        with pytest.raises(ValidationError):
            task(showWithoutTime=True)
        assert task(showWithoutTime=True, start="2020-04-01T00:00:00")

    def test_estimated_duration(self):
        assert task(estimatedDuration="PT1H")
        with pytest.raises(ValidationError):
            task(estimatedDuration="1 hour")


class TestRecurrence:
    def test_recurrence_requires_start(self):
        assert task(start="2020-01-06T09:00:00", recurrenceRule={"frequency": "weekly"})
        with pytest.raises(ValidationError):
            task(recurrenceRule={"frequency": "weekly"})
        with pytest.raises(ValidationError):
            task(due="2020-01-19T18:00:00", recurrenceId="2020-01-19T18:00:00")


class TestProgress:
    def test_percent_complete(self):
        assert task(percentComplete=50).percentComplete == 50
        with pytest.raises(ValidationError):
            task(percentComplete=101)

    def test_progress_values(self):
        for value in ["needs-action", "in-process", "completed", "failed", "cancelled"]:
            assert task(progress=value).progress == value
        with pytest.raises(ValidationError):
            task(progress="done")

    def test_task_participants_may_track_progress(self):
        parsed = task(
            organizerCalendarAddress="mailto:o@schedule.example.com",
            participants={
                "1": {
                    "calendarAddress": "mailto:tom@example.com",
                    "participationStatus": "accepted",
                    "progress": "completed",
                    "percentComplete": 100,
                }
            },
        )
        assert parsed.participants["1"].percentComplete == 100

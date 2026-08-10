"""Tests for the Event object (Sections 2.1, 3, and 4.1)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from json_calendar import Event

SIMPLE = {
    "@type": "Event",
    "version": "2.0",
    "uid": "a8df6573-0474-496d-8496-033ad45d7fea",
    "updated": "2020-01-02T18:23:04Z",
    "title": "Some event",
    "start": "2020-01-15T13:00:00",
    "timeZone": "America/New_York",
    "duration": "PT1H",
}


def event(**overrides):
    data = {**SIMPLE, **overrides}
    return Event.model_validate({k: v for k, v in data.items() if v is not None})


class TestBasics:
    def test_parses_simple_event(self):
        parsed = event()
        assert parsed.uid == "a8df6573-0474-496d-8496-033ad45d7fea"
        assert parsed.updated == datetime(2020, 1, 2, 18, 23, 4, tzinfo=UTC)
        assert parsed.start == datetime(2020, 1, 15, 13, 0, 0)
        assert parsed.timeZone == "America/New_York"
        assert parsed.duration == "PT1H"

    def test_json_round_trip(self):
        assert event().model_dump(mode="json", exclude_unset=True) == SIMPLE

    @pytest.mark.parametrize("field", ["uid", "updated", "start"])
    def test_mandatory_fields(self, field):
        with pytest.raises(ValidationError):
            event(**{field: None})

    def test_rejects_wrong_type_name(self):
        with pytest.raises(ValidationError):
            event(**{"@type": "Task"})

    def test_defaults(self):
        parsed = event()
        assert parsed.title == "Some event"
        assert parsed.description == ""
        assert parsed.showWithoutTime is False
        assert parsed.sequence == 0
        assert parsed.priority == 0
        assert parsed.freeBusyStatus == "busy"
        assert parsed.privacy == "public"
        assert parsed.status == "confirmed"

    def test_version_format(self):
        with pytest.raises(ValidationError):
            event(version="2")


class TestUnknownAndVendorProperties:
    def test_vendor_property_is_preserved(self):
        data = {**SIMPLE, "example.com:foo": {"bar": "baz"}}
        parsed = Event.model_validate(data)
        assert parsed.model_dump(mode="json", exclude_unset=True) == data

    def test_unknown_iana_style_property_is_preserved(self):
        data = {**SIMPLE, "futureProperty": 42}
        parsed = Event.model_validate(data)
        assert parsed.model_dump(mode="json", exclude_unset=True) == data

    def test_rejects_known_property_with_wrong_case(self):
        with pytest.raises(ValidationError):
            Event.model_validate({**SIMPLE, "Title": "x"})

    def test_rejects_syntactically_invalid_property_name(self):
        with pytest.raises(ValidationError):
            Event.model_validate({**SIMPLE, "not a valid name": 1})


class TestWhatAndWhere:
    def test_description_content_type_must_be_text(self):
        assert event(descriptionContentType="text/html")
        with pytest.raises(ValidationError):
            event(descriptionContentType="application/json")

    def test_description_content_type_charset_must_be_utf8(self):
        assert event(descriptionContentType="text/plain;charset=utf-8")
        with pytest.raises(ValidationError):
            event(descriptionContentType="text/plain;charset=latin1")

    def test_main_location_id_must_reference_a_location(self):
        locations = {"1": {"name": "Frankfurt Airport (FRA)"}}
        assert event(locations=locations, mainLocationId="1")
        with pytest.raises(ValidationError):
            event(locations=locations, mainLocationId="2")
        with pytest.raises(ValidationError):
            event(mainLocationId="1")

    def test_main_location_must_have_a_name(self):
        with pytest.raises(ValidationError):
            event(locations={"1": {"coordinates": "geo:1,2"}}, mainLocationId="1")

    def test_categories_must_be_uris(self):
        assert event(categories={"http://example.com/categories/music/r-b": True})
        with pytest.raises(ValidationError):
            event(categories={"music": True})

    def test_keywords(self):
        assert event(keywords={"math": True, "lecture": True})
        with pytest.raises(ValidationError):
            event(keywords={"math": False})

    def test_color(self):
        assert event(color="turquoise")
        assert event(color="#123ABC")
        with pytest.raises(ValidationError):
            event(color="#123")


class TestSchedulingProperties:
    def test_priority_range(self):
        assert event(priority=9).priority == 9
        with pytest.raises(ValidationError):
            event(priority=10)
        with pytest.raises(ValidationError):
            event(priority=-1)

    def test_status(self):
        assert event(status="cancelled").status == "cancelled"
        assert event(status="example.com:paused").status == "example.com:paused"
        with pytest.raises(ValidationError):
            event(status="CANCELLED")

    def test_free_busy_status(self):
        assert event(freeBusyStatus="free")
        with pytest.raises(ValidationError):
            event(freeBusyStatus="available")

    def test_privacy(self):
        assert event(privacy="secret")
        with pytest.raises(ValidationError):
            event(privacy="hidden")

    def test_method_is_lowercase_itip(self):
        assert event(method="request").method == "request"
        with pytest.raises(ValidationError):
            event(method="REQUEST")
        with pytest.raises(ValidationError):
            event(method="deliver")


class TestTimeZones:
    def test_end_time_zone_requires_time_zone(self):
        assert event(endTimeZone="Asia/Tokyo")
        with pytest.raises(ValidationError):
            event(timeZone=None, endTimeZone="Asia/Tokyo")

    def test_rejects_unknown_time_zone(self):
        with pytest.raises(ValidationError):
            event(timeZone="Mars/Olympus_Mons")

    def test_duration_must_be_unsigned(self):
        with pytest.raises(ValidationError):
            event(duration="-PT1H")


class TestRecurrence:
    def test_recurrence_rule(self):
        parsed = event(recurrenceRule={"frequency": "weekly", "until": "2020-06-24T09:00:00"})
        assert parsed.recurrenceRule.frequency == "weekly"

    def test_recurrence_id_excludes_rule_and_overrides(self):
        assert event(recurrenceId="2020-01-15T13:00:00")
        with pytest.raises(ValidationError):
            event(
                recurrenceId="2020-01-15T13:00:00",
                recurrenceRule={"frequency": "weekly"},
            )
        with pytest.raises(ValidationError):
            event(
                recurrenceId="2020-01-15T13:00:00",
                recurrenceOverrides={"2020-01-22T13:00:00": {}},
            )

    def test_recurrence_id_time_zone_requires_recurrence_id(self):
        assert event(recurrenceId="2020-01-15T13:00:00", recurrenceIdTimeZone="Europe/London")
        with pytest.raises(ValidationError):
            event(recurrenceIdTimeZone="Europe/London")

    def test_recurrence_overrides(self):
        parsed = event(
            recurrenceRule={"frequency": "weekly"},
            recurrenceOverrides={
                "2020-01-07T14:00:00": {"title": "Introduction (optional)"},
                "2020-04-01T09:00:00": {"excluded": True},
            },
        )
        assert parsed.recurrenceOverrides is not None
        assert parsed.recurrenceOverrides[datetime(2020, 4, 1, 9)] == {"excluded": True}

    def test_override_keys_must_be_local_date_times(self):
        with pytest.raises(ValidationError):
            event(recurrenceOverrides={"2020-04-01T09:00:00Z": {"excluded": True}})

    def test_excluded_override_must_be_the_sole_member(self):
        with pytest.raises(ValidationError):
            event(recurrenceOverrides={"2020-04-01T09:00:00": {"excluded": True, "title": "x"}})
        with pytest.raises(ValidationError):
            event(recurrenceOverrides={"2020-04-01T09:00:00": {"excluded": False}})


PARTICIPANTS = {
    "dG9tQGZvb2Jhci5xlLmNvbQ": {
        "name": "Tom Tool",
        "calendarAddress": "mailto:tom@calendar.example.com",
        "participationStatus": "accepted",
    }
}


class TestParticipants:
    def test_participants_with_organizer(self):
        parsed = event(
            organizerCalendarAddress="mailto:f245f875@schedule.example.com",
            participants=PARTICIPANTS,
        )
        assert parsed.participants["dG9tQGZvb2Jhci5xlLmNvbQ"].name == "Tom Tool"

    def test_participant_calendar_address_requires_organizer(self):
        with pytest.raises(ValidationError):
            event(participants=PARTICIPANTS)

    def test_organizer_requires_a_participant_calendar_address(self):
        with pytest.raises(ValidationError):
            event(organizerCalendarAddress="mailto:f@schedule.example.com")
        with pytest.raises(ValidationError):
            event(
                organizerCalendarAddress="mailto:f@schedule.example.com",
                participants={"1": {"name": "No Address"}},
            )

    def test_sent_by_requires_organizer(self):
        assert event(
            sentBy="assistant@example.com",
            organizerCalendarAddress="mailto:f@schedule.example.com",
            participants=PARTICIPANTS,
        )
        with pytest.raises(ValidationError):
            event(sentBy="assistant@example.com")

    def test_event_participants_must_not_track_task_progress(self):
        participants = {
            "1": {
                "calendarAddress": "mailto:tom@example.com",
                "participationStatus": "accepted",
                "progress": "in-process",
            }
        }
        with pytest.raises(ValidationError):
            event(
                organizerCalendarAddress="mailto:f@schedule.example.com",
                participants=participants,
            )

"""Round-trip tests for the examples of Section 5 of the spec.

Each example is completed with the mandatory properties the spec elides
behind the "..." placeholder, and the JSON typos of the draft are fixed.
"""

import pytest

from json_calendar import Event, Task

BASE = {
    "@type": "Event",
    "version": "2.0",
    "uid": "3f6b6bec-a0e4-4a49-b067-58a3b191f4b7",
    "updated": "2020-01-02T18:23:04Z",
}

ALL_DAY_EVENT = {
    **BASE,
    "title": "April Fool's Day",
    "showWithoutTime": True,
    "start": "1900-04-01T00:00:00",
    "duration": "P1D",
    "recurrenceRule": {"frequency": "yearly"},
}

TASK_WITH_DUE_DATE = {
    **BASE,
    "@type": "Task",
    "title": "Buy groceries",
    "due": "2020-01-19T18:00:00",
    "timeZone": "Europe/Vienna",
    "estimatedDuration": "PT1H",
}

EVENT_WITH_END_TIME_ZONE = {
    **BASE,
    "title": "Flight XY51 to Tokyo",
    "start": "2020-04-01T09:00:00",
    "timeZone": "Europe/Berlin",
    "endTimeZone": "Asia/Tokyo",
    "duration": "PT10H30M",
    "mainLocationId": "1",
    "locations": {
        "1": {"name": "Frankfurt Airport (FRA)"},
        "2": {"name": "Narita International Airport (NRT)"},
    },
}

FLOATING_TIME_EVENT = {
    **BASE,
    "title": "Yoga",
    "start": "2020-01-01T07:00:00",
    "duration": "PT30M",
    "recurrenceRule": {"frequency": "daily"},
}

EVENT_WITH_LOCATIONS = {
    **BASE,
    "title": "Live from Music Bowl: The Band",
    "description": "Go see the biggest music event ever!",
    "locale": "en",
    "start": "2020-07-04T17:00:00",
    "timeZone": "America/New_York",
    "duration": "PT3H",
    "mainLocationId": "c0503d30-8c50-4372-87b5-7657e8e0fedd",
    "locations": {
        "c0503d30-8c50-4372-87b5-7657e8e0fedd": {
            "name": "The Music Bowl",
            "coordinates": "geo:40.7829,-73.9654",
        },
        "ee42e41e-1046-4489-9760-c0b85f0dc176": {
            "name": "BAZ Parking, 9 West 57th Street, New York",
            "coordinates": "geo:40.7637,-73.9748",
            "locationTypes": {"parking": True},
        },
    },
    "virtualLocations": {
        "vloc1": {
            "name": "Free live Stream from Music Bowl",
            "uri": "https://stream.example.com/the_band_2020",
        }
    },
}

RECURRING_EVENT_WITH_OVERRIDES = {
    **BASE,
    "title": "Calculus I",
    "start": "2020-01-08T09:00:00",
    "timeZone": "Europe/London",
    "duration": "PT1H30M",
    "locations": {"mlab": {"name": "Math lab room 1"}},
    "recurrenceRule": {"frequency": "weekly", "until": "2020-06-24T09:00:00"},
    "recurrenceOverrides": {
        "2020-01-07T14:00:00": {"title": "Introduction to Calculus I (optional)"},
        "2020-04-01T09:00:00": {"excluded": True},
        "2020-06-25T09:00:00": {
            "title": "Calculus I Exam",
            "start": "2020-06-25T10:00:00",
            "duration": "PT2H",
            "locations": {"auditorium": {"name": "Big Auditorium"}},
        },
    },
}

RECURRING_EVENT_WITH_PARTICIPANTS = {
    **BASE,
    "title": "FooBar team meeting",
    "start": "2020-01-08T09:00:00",
    "timeZone": "Africa/Johannesburg",
    "duration": "PT1H",
    "virtualLocations": {
        "0": {
            "name": "ChatMe meeting room",
            "uri": "https://chatme.example.com?id=1234567&pw=a8a24627b63d",
        }
    },
    "recurrenceRule": {"frequency": "weekly"},
    "organizerCalendarAddress": "mailto:f245f875-7f63-4a5e-a2c8@schedule.example.com",
    "participants": {
        "dG9tQGZvb2Jhci5xlLmNvbQ": {
            "name": "Tom Tool",
            "email": "tom@foobar.example.com",
            "calendarAddress": "mailto:tom@calendar.example.com",
            "participationStatus": "accepted",
        },
        "em9lQGZvb2GFtcGxlLmNvbQ": {
            "name": "Zoe Zelda",
            "calendarAddress": "mailto:zoe@foobar.example.com",
            "participationStatus": "accepted",
            "roles": {"owner": True, "chair": True},
        },
    },
    "recurrenceOverrides": {
        "2020-03-04T09:00:00": {
            "participants/dG9tQGZvb2Jhci5xlLmNvbQ/participationStatus": "declined"
        }
    },
}


@pytest.mark.parametrize(
    "example",
    [
        ALL_DAY_EVENT,
        EVENT_WITH_END_TIME_ZONE,
        FLOATING_TIME_EVENT,
        EVENT_WITH_LOCATIONS,
        RECURRING_EVENT_WITH_OVERRIDES,
        RECURRING_EVENT_WITH_PARTICIPANTS,
    ],
    ids=lambda e: e["title"],
)
def test_event_examples_round_trip(example):
    assert Event.model_validate(example).model_dump(mode="json", exclude_unset=True) == example


def test_task_example_round_trip():
    parsed = Task.model_validate(TASK_WITH_DUE_DATE)
    assert parsed.model_dump(mode="json", exclude_unset=True) == TASK_WITH_DUE_DATE

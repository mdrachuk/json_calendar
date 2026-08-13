"""Validation errors cite the part of the spec that imposes the violated rule."""

import pytest
from pydantic import TypeAdapter, ValidationError

from json_calendar._types import Duration, Id, Int, LanguageTag, PatchObject, TimeZoneId, Uri
from json_calendar.models import Alert, Event, Group, Link, Participant, RecurrenceRule
from json_calendar.models._base import Color
from json_calendar.models.location import VirtualLocation


@pytest.mark.parametrize(
    ("citation", "scalar", "value"),
    [
        ("(Section 1.5.1)", Id, "no spaces allowed"),
        ("(Section 1.5.2)", Int, 2**53),
        ("(Section 1.5.6)", Duration, "P1H"),
        ("(Section 1.5.8)", TimeZoneId, "Mars/Olympus_Mons"),
        ("(Section 1.5.9)", PatchObject, {"a": 1, "a/b": 2}),
        ("(RFC 6901)", PatchObject, {"a~2b": 1}),
        ("(RFC 3986)", Uri, "http://exa mple.com"),
        ("(RFC 5646)", LanguageTag, "not a tag"),
        ("(Section 3.2.12)", Color, "notacolor"),
    ],
)
def test_scalar_type_errors_cite_the_spec(citation, scalar, value):
    with pytest.raises(ValidationError) as info:
        TypeAdapter(scalar).validate_python(value)
    assert citation in str(info.value)


@pytest.mark.parametrize(
    ("citation", "props"),
    [
        ("(Section 3.3.3)", {"frequency": "fortnightly"}),
        ("(Section 3.3.3)", {"interval": 0}),
        ("(Section 3.3.3)", {"rscale": "klingon"}),
        ("(Section 3.3.3)", {"skip": "OMIT"}),
        ("(Section 3.3.3)", {"firstDayOfWeek": "monday"}),
        ("(Section 3.3.3; RFC 7529)", {"byMonth": ["123"]}),
        ("(Section 3.3.3)", {"count": 3, "until": "2020-06-24T09:00:00"}),
    ],
)
def test_recurrence_rule_errors_cite_the_spec(citation, props):
    with pytest.raises(ValidationError) as info:
        RecurrenceRule.model_validate({"frequency": "daily", **props})
    assert citation in str(info.value)


@pytest.mark.parametrize(
    ("citation", "props"),
    [
        ("(Section 2.1)", {"@type": "Meeting"}),
        ("(Section 3.1.2)", {"version": "1.0"}),
        ("(Section 3.1.4)", {"prodId": 7}),
        ("(Section 3.1.8)", {"method": "invite"}),
        ("(Section 3.2.1)", {"title": 5}),
        ("(Section 3.2.4)", {"showWithoutTime": "yes"}),
        ("(Section 3.2.10)", {"keywords": {"math": False}}),
    ],
)
def test_calendar_object_field_errors_cite_the_spec(citation, props):
    event = {
        "@type": "Event",
        "uid": "e1",
        "version": "2.0",
        "updated": "2020-01-01T00:00:00Z",
        "start": "2020-06-01T09:00:00",
    }
    with pytest.raises(ValidationError) as info:
        Event.model_validate({**event, **props})
    assert citation in str(info.value)


def test_field_errors_keep_the_more_specific_type_citation():
    with pytest.raises(ValidationError) as info:
        RecurrenceRule.model_validate({"frequency": "daily", "byMonthDay": [2**53]})
    assert "(Section 1.5.2)" in str(info.value)
    assert "(Section 3.3.3)" not in str(info.value)


def test_open_enum_errors_cite_the_spec():
    with pytest.raises(ValidationError) as info:
        Participant.model_validate(
            {"calendarAddress": "mailto:a@example.com", "participationStatus": "unsure"}
        )
    assert "(Section 3.4.6)" in str(info.value)


def test_model_rule_errors_cite_the_spec():
    with pytest.raises(ValidationError) as info:
        Link.model_validate({"href": "https://example.com", "display": {"badge": True}})
    assert "(Section 1.5.11)" in str(info.value)


def test_property_name_errors_cite_the_spec():
    with pytest.raises(ValidationError) as info:
        Link.model_validate({"href": "https://example.com", "BAD NAME": 1})
    assert "(Sections 1.7.2 and 1.8.1)" in str(info.value)


@pytest.mark.parametrize(
    ("citation", "missing"),
    [
        ("(Section 2.1)", "@type"),
        ("(Section 3.1.1)", "uid"),
        ("(Section 3.1.2)", "version"),
        ("(Section 3.1.6)", "updated"),
        ("(Section 4.1.1)", "start"),
    ],
)
def test_missing_required_property_errors_cite_the_spec(citation, missing):
    event = {
        "@type": "Event",
        "uid": "e1",
        "version": "2.0",
        "updated": "2020-01-01T00:00:00Z",
        "start": "2020-06-01T09:00:00",
    }
    del event[missing]
    with pytest.raises(ValidationError) as info:
        Event.model_validate(event)
    assert f"Field required {citation}" in str(info.value)


@pytest.mark.parametrize(
    ("citation", "model", "data"),
    [
        ("(Section 3.5.1)", Alert, {}),
        ("(Section 1.5.11)", Link, {}),
        ("(Section 3.2.7)", VirtualLocation, {}),
        ("(Section 4.3.1)", Group, {"@type": "Group", "uid": "g", "version": "2.0"}),
    ],
)
def test_missing_required_component_property_errors_cite_the_spec(citation, model, data):
    with pytest.raises(ValidationError) as info:
        model.model_validate(data)
    assert f"Field required {citation}" in str(info.value)


@pytest.mark.parametrize(
    ("citation", "props"),
    [
        ("(Section 3.3.3)", {"byDay": []}),
        ("(Section 3.3.3)", {"byMonthDay": []}),
        ("(Section 3.3.3; RFC 7529)", {"byMonth": []}),
        ("(Section 3.3.3)", {"bySetPosition": []}),
    ],
)
def test_empty_container_errors_cite_the_spec(citation, props):
    with pytest.raises(ValidationError) as info:
        RecurrenceRule.model_validate({"frequency": "daily", **props})
    assert citation in str(info.value)


def test_empty_participant_and_link_containers_cite_the_spec():
    with pytest.raises(ValidationError) as info:
        Participant.model_validate({"calendarAddress": "mailto:a@example.com", "roles": {}})
    assert "(Section 3.4.6)" in str(info.value)
    with pytest.raises(ValidationError) as info:
        Link.model_validate({"href": "https://example.com", "rel": "icon", "display": {}})
    assert "(Section 1.5.11)" in str(info.value)


def test_cited_errors_keep_their_error_location():
    with pytest.raises(ValidationError) as info:
        RecurrenceRule.model_validate({"frequency": "daily", "byMonth": ["1", "123"]})
    assert info.value.errors()[0]["loc"] == ("byMonth", 1)


def test_recurrence_override_errors_cite_the_spec():
    with pytest.raises(ValidationError) as info:
        Event.model_validate(
            {
                "@type": "Event",
                "uid": "e1",
                "version": "2.0",
                "updated": "2020-01-01T00:00:00Z",
                "start": "2020-06-01T09:00:00",
                "recurrenceRule": {"frequency": "daily"},
                "recurrenceOverrides": {"2020-06-02T09:00:00": {"excluded": True, "title": "x"}},
            }
        )
    assert "(Section 3.3.4)" in str(info.value)

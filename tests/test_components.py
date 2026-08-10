"""Tests for the component objects: Relation, Link, Location, VirtualLocation,
Participant, and Alert (Sections 1.5.10, 1.5.11, 3.2, 3.4.6, and 3.5)."""

import pytest
from pydantic import ValidationError

from json_calendar.models import (
    AbsoluteTrigger,
    Alert,
    Link,
    Location,
    OffsetTrigger,
    Participant,
    Relation,
    UnknownTrigger,
    VirtualLocation,
)


class TestRelation:
    def test_defaults_to_empty_relation(self):
        assert Relation().relation == {}

    def test_known_relation_types(self):
        relation = Relation.model_validate(
            {"@type": "Relation", "relation": {"first": True, "next": True}}
        )
        assert relation.relation == {"first": True, "next": True}

    def test_rejects_false_values(self):
        with pytest.raises(ValidationError):
            Relation.model_validate({"relation": {"next": False}})

    def test_rejects_unknown_relation_type(self):
        with pytest.raises(ValidationError):
            Relation.model_validate({"relation": {"bogus": True}})

    def test_accepts_vendor_relation_type(self):
        relation = Relation.model_validate({"relation": {"example.com:custom": True}})
        assert relation.relation == {"example.com:custom": True}

    def test_rejects_wrong_type_name(self):
        with pytest.raises(ValidationError):
            Relation.model_validate({"@type": "Link"})


class TestLink:
    def test_minimal(self):
        link = Link.model_validate({"href": "https://example.com/doc.pdf"})
        assert link.href == "https://example.com/doc.pdf"
        assert link.rel == "enclosure"

    def test_href_is_mandatory(self):
        with pytest.raises(ValidationError):
            Link.model_validate({"title": "no href"})

    def test_href_must_be_a_uri(self):
        with pytest.raises(ValidationError):
            Link.model_validate({"href": "not a uri"})

    def test_display_requires_icon_rel(self):
        with pytest.raises(ValidationError):
            Link.model_validate({"href": "https://example.com/i.png", "display": {"badge": True}})

    def test_display_with_icon_rel(self):
        link = Link.model_validate(
            {"href": "https://example.com/i.png", "rel": "icon", "display": {"badge": True}}
        )
        assert link.display == {"badge": True}

    def test_rejects_unknown_display_value(self):
        with pytest.raises(ValidationError):
            Link.model_validate(
                {"href": "https://example.com/i.png", "rel": "icon", "display": {"bogus": True}}
            )

    def test_accepts_vendor_display_value(self):
        link = Link.model_validate(
            {
                "href": "https://example.com/i.png",
                "rel": "icon",
                "display": {"example.com:hero": True},
            }
        )
        assert link.display == {"example.com:hero": True}

    def test_rejects_negative_size(self):
        with pytest.raises(ValidationError):
            Link.model_validate({"href": "https://example.com/f", "size": -1})


class TestLocation:
    def test_requires_at_least_one_property(self):
        with pytest.raises(ValidationError):
            Location.model_validate({})
        with pytest.raises(ValidationError):
            Location.model_validate({"@type": "Location"})

    def test_name_only(self):
        location = Location.model_validate({"name": "Frankfurt Airport (FRA)"})
        assert location.name == "Frankfurt Airport (FRA)"

    def test_coordinates_must_be_geo_uri(self):
        location = Location.model_validate({"coordinates": "geo:40.7829,-73.9654"})
        assert location.coordinates == "geo:40.7829,-73.9654"
        with pytest.raises(ValidationError):
            Location.model_validate({"coordinates": "40.7829,-73.9654"})

    def test_location_types(self):
        location = Location.model_validate({"locationTypes": {"parking": True}})
        assert location.locationTypes == {"parking": True}

    def test_links_must_not_be_empty(self):
        with pytest.raises(ValidationError):
            Location.model_validate({"name": "x", "links": {}})


class TestVirtualLocation:
    def test_minimal(self):
        vloc = VirtualLocation.model_validate({"uri": "https://chat.example.com/room1"})
        assert vloc.uri == "https://chat.example.com/room1"
        assert vloc.name == ""

    def test_uri_is_mandatory(self):
        with pytest.raises(ValidationError):
            VirtualLocation.model_validate({"name": "Room 1"})

    def test_features(self):
        vloc = VirtualLocation.model_validate(
            {"uri": "tel:+1-555-555-5555", "features": {"audio": True, "phone": True}}
        )
        assert vloc.features == {"audio": True, "phone": True}

    def test_rejects_unknown_feature(self):
        with pytest.raises(ValidationError):
            VirtualLocation.model_validate(
                {"uri": "https://x.example.com", "features": {"bogus": True}}
            )

    def test_rejects_false_feature(self):
        with pytest.raises(ValidationError):
            VirtualLocation.model_validate(
                {"uri": "https://x.example.com", "features": {"audio": False}}
            )


class TestParticipant:
    def test_name_alone_is_valid(self):
        participant = Participant.model_validate({"name": "Tom Tool"})
        assert participant.name == "Tom Tool"

    def test_email_requires_calendar_address(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"email": "tom@foobar.example.com"})
        participant = Participant.model_validate(
            {
                "email": "tom@foobar.example.com",
                "calendarAddress": "mailto:tom@calendar.example.com",
            }
        )
        assert participant.email == "tom@foobar.example.com"

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            Participant.model_validate(
                {"email": "not an email", "calendarAddress": "mailto:t@example.com"}
            )

    def test_roles_require_calendar_address(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"roles": {"chair": True}})

    def test_roles(self):
        participant = Participant.model_validate(
            {
                "calendarAddress": "mailto:zoe@foobar.example.com",
                "roles": {"owner": True, "chair": True},
            }
        )
        assert participant.roles == {"owner": True, "chair": True}

    def test_roles_must_not_be_empty(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"calendarAddress": "mailto:zoe@example.com", "roles": {}})

    def test_rejects_unknown_role(self):
        with pytest.raises(ValidationError):
            Participant.model_validate(
                {"calendarAddress": "mailto:zoe@example.com", "roles": {"boss": True}}
            )

    def test_participation_status_requires_calendar_address(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"participationStatus": "accepted"})

    def test_rejects_unknown_participation_status(self):
        with pytest.raises(ValidationError):
            Participant.model_validate(
                {"calendarAddress": "mailto:t@example.com", "participationStatus": "maybe"}
            )

    def test_expect_reply_requires_calendar_address(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"expectReply": True})

    def test_delegated_to_requires_calendar_address_and_content(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"delegatedTo": {"mailto:x@example.com": True}})
        with pytest.raises(ValidationError):
            Participant.model_validate(
                {"calendarAddress": "mailto:t@example.com", "delegatedTo": {}}
            )
        participant = Participant.model_validate(
            {
                "calendarAddress": "mailto:t@example.com",
                "delegatedTo": {"mailto:x@example.com": True},
            }
        )
        assert participant.delegatedTo == {"mailto:x@example.com": True}

    def test_description_content_type_requires_description(self):
        with pytest.raises(ValidationError):
            Participant.model_validate({"descriptionContentType": "text/html"})

    def test_progress_requires_accepted_status(self):
        with pytest.raises(ValidationError):
            Participant.model_validate(
                {"calendarAddress": "mailto:t@example.com", "progress": "in-process"}
            )
        participant = Participant.model_validate(
            {
                "calendarAddress": "mailto:t@example.com",
                "participationStatus": "accepted",
                "progress": "in-process",
            }
        )
        assert participant.progress == "in-process"


class TestAlert:
    def test_trigger_is_mandatory(self):
        with pytest.raises(ValidationError):
            Alert.model_validate({})

    def test_offset_trigger_is_the_default_type(self):
        alert = Alert.model_validate({"trigger": {"offset": "-PT5M"}})
        assert isinstance(alert.trigger, OffsetTrigger)
        assert alert.trigger.offset == "-PT5M"
        assert alert.trigger.relativeTo == "start"

    def test_absolute_trigger(self):
        alert = Alert.model_validate(
            {"trigger": {"@type": "AbsoluteTrigger", "when": "2020-01-01T10:00:00Z"}}
        )
        assert isinstance(alert.trigger, AbsoluteTrigger)

    def test_absolute_trigger_requires_when(self):
        with pytest.raises(ValidationError):
            Alert.model_validate({"trigger": {"@type": "AbsoluteTrigger"}})

    def test_unknown_trigger_is_preserved(self):
        data = {"trigger": {"@type": "example.com:Trigger", "foo": 1}}
        alert = Alert.model_validate(data)
        assert isinstance(alert.trigger, UnknownTrigger)
        assert alert.model_dump(mode="json", exclude_unset=True) == data

    def test_offset_must_be_signed_duration(self):
        with pytest.raises(ValidationError):
            Alert.model_validate({"trigger": {"offset": "5M"}})

    def test_relative_to_values(self):
        alert = Alert.model_validate({"trigger": {"offset": "PT5M", "relativeTo": "end"}})
        assert isinstance(alert.trigger, OffsetTrigger)
        assert alert.trigger.relativeTo == "end"
        with pytest.raises(ValidationError):
            Alert.model_validate({"trigger": {"offset": "PT5M", "relativeTo": "middle"}})

    def test_action(self):
        alert = Alert.model_validate({"trigger": {"offset": "-PT5M"}})
        assert alert.action == "display"
        assert Alert.model_validate({"trigger": {"offset": "-PT5M"}, "action": "email"})
        with pytest.raises(ValidationError):
            Alert.model_validate({"trigger": {"offset": "-PT5M"}, "action": "bogus"})

    def test_snooze_relation_is_allowed(self):
        alert = Alert.model_validate(
            {"trigger": {"offset": "-PT5M"}, "relatedTo": {"1": {"relation": {"snooze": True}}}}
        )
        assert alert.relatedTo is not None
        assert alert.relatedTo["1"].relation == {"snooze": True}

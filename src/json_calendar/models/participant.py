"""The Participant object (Section 3.4.6)."""

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import Email, Id, Uri, is_id, is_uri, open_enum
from json_calendar.models._base import JSCalendarObject, TextContentType
from json_calendar.models.link import Link


def _check_id_or_uri(value: str) -> str:
    if not is_id(value) and not is_uri(value):
        raise ValueError(f"{value!r} is neither an Id (Section 1.5.1) nor a URI (RFC 3986)")
    return value


ParticipantKind = Annotated[
    str, open_enum("individual", "group", "location", "resource"), cites("Section 3.4.6")
]
RoleValue = Annotated[
    str,
    open_enum("owner", "optional", "informational", "chair", "required"),
    cites("Section 3.4.6"),
]
ParticipationStatus = Annotated[
    str,
    open_enum("needs-action", "accepted", "declined", "tentative", "delegated"),
    cites("Section 3.4.6"),
]
ParticipantProgress = Annotated[
    str, open_enum("in-process", "completed", "failed"), cites("Section 3.4.6")
]


class Participant(JSCalendarObject):
    """A participant of a calendar object (Section 3.4.6)."""

    type: Annotated[Literal["Participant"], cites("Section 3.4.6")] = Field(
        default="Participant", alias="@type"
    )
    name: Annotated[str, cites("Section 3.4.6")] | None = None
    email: Email | None = None
    description: Annotated[str, cites("Section 3.4.6")] | None = None
    descriptionContentType: TextContentType | None = None
    calendarAddress: Uri | None = None
    kind: ParticipantKind | None = None
    roles: Annotated[
        dict[RoleValue, Annotated[Literal[True], cites("Section 3.4.6")]] | None,
        cites("Section 3.4.6"),
    ] = Field(default=None, min_length=1)
    participationStatus: ParticipationStatus = "needs-action"
    expectReply: Annotated[bool, Field(strict=True), cites("Section 3.4.6")] = False
    sentBy: Email | None = None
    delegatedTo: Annotated[
        dict[Uri, Annotated[Literal[True], cites("Section 3.4.6")]] | None,
        cites("Section 3.4.6"),
    ] = Field(default=None, min_length=1)
    delegatedFrom: Annotated[
        dict[Uri, Annotated[Literal[True], cites("Section 3.4.6")]] | None,
        cites("Section 3.4.6"),
    ] = Field(default=None, min_length=1)
    # The spec gives the type signature Id[Boolean] but requires URI keys;
    # keys matching either reading of the draft are accepted, nothing else.
    memberOf: Annotated[
        dict[
            Annotated[str, AfterValidator(_check_id_or_uri)],
            Annotated[Literal[True], cites("Section 3.4.6")],
        ]
        | None,
        cites("Section 3.4.6"),
    ] = Field(default=None, min_length=1)
    links: Annotated[dict[Id, Link] | None, cites("Section 3.4.6")] = Field(
        default=None, min_length=1
    )
    progress: ParticipantProgress | None = None
    percentComplete: Annotated[int, Field(strict=True, ge=0, le=100), cites("Section 4.2.4")] | (
        None
    ) = None

    _REQUIRE_CALENDAR_ADDRESS = (
        "email",
        "kind",
        "roles",
        "participationStatus",
        "expectReply",
        "sentBy",
        "delegatedTo",
        "delegatedFrom",
        "memberOf",
        "progress",
    )

    @model_validator(mode="after")
    def _validate_dependencies(self) -> "Participant":
        if self.calendarAddress is None:
            for name in self._REQUIRE_CALENDAR_ADDRESS:
                if name in self.model_fields_set:
                    raise ValueError(
                        f'if "{name}" is set, the "calendarAddress" property '
                        f"must be set (Section 3.4.6)"
                    )
        if self.descriptionContentType is not None and self.description is None:
            raise ValueError(
                'if "descriptionContentType" is set, the "description" property '
                "must be set (Section 3.4.6)"
            )
        if self.progress is not None and self.participationStatus != "accepted":
            raise ValueError(
                'if "progress" is set, "participationStatus" must be "accepted" (Section 3.4.6)'
            )
        return self

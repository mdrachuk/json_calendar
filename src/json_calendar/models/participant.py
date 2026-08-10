"""The Participant object (Section 3.4.6)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar._types import Email, Id, Uri, open_enum
from json_calendar.models._base import JSCalendarObject, TextContentType
from json_calendar.models.link import Link

ParticipantKind = Annotated[str, open_enum("individual", "group", "location", "resource")]
RoleValue = Annotated[str, open_enum("owner", "optional", "informational", "chair", "required")]
ParticipationStatus = Annotated[
    str, open_enum("needs-action", "accepted", "declined", "tentative", "delegated")
]
ParticipantProgress = Annotated[str, open_enum("in-process", "completed", "failed")]


class Participant(JSCalendarObject):
    """A participant of a calendar object (Section 3.4.6)."""

    type: Literal["Participant"] = Field(default="Participant", alias="@type")
    name: str | None = None
    email: Email | None = None
    description: str | None = None
    descriptionContentType: TextContentType | None = None
    calendarAddress: Uri | None = None
    kind: ParticipantKind | None = None
    roles: dict[RoleValue, Literal[True]] | None = Field(default=None, min_length=1)
    participationStatus: ParticipationStatus = "needs-action"
    expectReply: bool = False
    sentBy: Email | None = None
    delegatedTo: dict[Uri, Literal[True]] | None = Field(default=None, min_length=1)
    delegatedFrom: dict[Uri, Literal[True]] | None = Field(default=None, min_length=1)
    # The spec gives the type signature Id[Boolean] but requires URI keys; we
    # keep the keys unconstrained to accept both readings of the draft.
    memberOf: dict[str, Literal[True]] | None = Field(default=None, min_length=1)
    links: dict[Id, Link] | None = Field(default=None, min_length=1)
    progress: ParticipantProgress | None = None
    percentComplete: Annotated[int, Field(strict=True, ge=0, le=100)] | None = None

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
                        f'if "{name}" is set, the "calendarAddress" property must be set'
                    )
        if self.descriptionContentType is not None and self.description is None:
            raise ValueError(
                'if "descriptionContentType" is set, the "description" property must be set'
            )
        if self.progress is not None and self.participationStatus != "accepted":
            raise ValueError('if "progress" is set, "participationStatus" must be "accepted"')
        return self

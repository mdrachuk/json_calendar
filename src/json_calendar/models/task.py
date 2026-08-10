"""The Task object (Sections 2.2 and 4.2)."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from json_calendar._types import Duration, LocalDateTime, open_enum
from json_calendar.models.calendar_object import CalendarObject

TaskProgress = Annotated[
    str, open_enum("needs-action", "in-process", "completed", "failed", "cancelled")
]


class Task(CalendarObject):
    """An action item, assignment, to-do, or work item (Sections 2.2 and 4.2)."""

    type: Literal["Task"] = Field(default="Task", alias="@type")
    due: LocalDateTime | None = None
    start: LocalDateTime | None = None
    estimatedDuration: Duration | None = None
    percentComplete: Annotated[int, Field(strict=True, ge=0, le=100)] | None = None
    progress: TaskProgress | None = None

    @model_validator(mode="after")
    def _validate_task(self) -> "Task":
        # Draft-18 words this condition as "if timeZone is NOT set...", which
        # contradicts its own Simple Task example (Section 5.2); we implement
        # the reading that is consistent with the examples.
        if (self.timeZone is not None or self.showWithoutTime) and (
            self.due is None and self.start is None
        ):
            raise ValueError('at least one of the "due" and "start" properties must be set')
        if self.start is None and (
            self.recurrenceRule is not None or self.recurrenceId is not None
        ):
            raise ValueError(
                '"start" must be set if the "recurrenceRule" or "recurrenceId" properties are set'
            )
        return self

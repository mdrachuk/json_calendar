"""The RecurrenceRule and NDay objects (Section 3.3.3)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._types import Int, LocalDateTime, UnsignedInt
from json_calendar.models._base import JSCalendarObject

WeekDay = Literal["mo", "tu", "we", "th", "fr", "sa", "su"]


class RecurrenceRule(JSCalendarObject):
    """A repeating pattern for recurring calendar objects (Section 3.3.3)."""

    type: Literal["RecurrenceRule"] = Field(default="RecurrenceRule", alias="@type")
    frequency: Literal["yearly", "monthly", "weekly", "daily", "hourly", "minutely", "secondly"]
    interval: Annotated[int, Field(strict=True, ge=1)] = 1
    rscale: Annotated[str, AfterValidator(_check_lowercase)] = "gregorian"
    skip: Literal["omit", "backward", "forward"] = "omit"
    firstDayOfWeek: WeekDay = "mo"
    byDay: list[NDay] | None = Field(default=None, min_length=1)
    byMonthDay: list[Annotated[Int, AfterValidator(_check_nonzero)]] | None = Field(
        default=None, min_length=1
    )
    byMonth: list[Annotated[str, Field(pattern=r"^\d+L?$")]] | None = Field(
        default=None, min_length=1
    )
    byYearDay: list[Annotated[Int, AfterValidator(_check_nonzero)]] | None = Field(
        default=None, min_length=1
    )
    byWeekNo: list[Annotated[Int, AfterValidator(_check_nonzero)]] | None = Field(
        default=None, min_length=1
    )
    byHour: list[Annotated[int, Field(strict=True, ge=0, le=23)]] | None = Field(
        default=None, min_length=1
    )
    byMinute: list[Annotated[int, Field(strict=True, ge=0, le=59)]] | None = Field(
        default=None, min_length=1
    )
    bySecond: list[Annotated[int, Field(strict=True, ge=0, le=60)]] | None = Field(
        default=None, min_length=1
    )
    bySetPosition: list[Int] | None = Field(default=None, min_length=1)
    count: UnsignedInt | None = None
    until: LocalDateTime | None = None

    @model_validator(mode="after")
    def _validate(self) -> RecurrenceRule:
        if self.count is not None and self.until is not None:
            raise ValueError('the "count" and "until" properties must not both be set')
        if self.rscale == "gregorian":
            for name, values, bound in (
                ("byMonthDay", self.byMonthDay, 31),
                ("byYearDay", self.byYearDay, 366),
                ("byWeekNo", self.byWeekNo, 53),
            ):
                for value in values or ():
                    if abs(value) > bound:
                        raise ValueError(
                            f'"{name}" values must be between -{bound} and {bound} '
                            f"in the gregorian calendar system"
                        )
        return self


class NDay(JSCalendarObject):
    """A day of the week on which to repeat (Section 3.3.3)."""

    type: Literal["NDay"] = Field(default="NDay", alias="@type")
    day: WeekDay
    nthOfPeriod: Annotated[Int, AfterValidator(_check_nonzero)] | None = None


def _check_nonzero(value: int) -> int:
    if value == 0:
        raise ValueError("value must not be zero")
    return value


def _check_lowercase(value: str) -> str:
    if value != value.lower():
        raise ValueError(f"{value!r} must be lowercase")
    return value


NDay.model_rebuild()
RecurrenceRule.model_rebuild()

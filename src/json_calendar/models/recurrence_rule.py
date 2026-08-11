"""The RecurrenceRule and NDay objects (Section 3.3.3)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from json_calendar._spec import cites
from json_calendar._types import MAX_INT, Int, LocalDateTime, UnsignedInt, open_enum
from json_calendar.models._base import JSCalendarObject

WeekDay = Annotated[Literal["mo", "tu", "we", "th", "fr", "sa", "su"], cites("Section 3.3.3")]

# The calendar systems registered in the Unicode CLDR (common/bcp47/calendar.xml),
# including the aliased and deprecated names, which RFC 7529 also permits;
# "rscale" values must be one of these or a vendor-specific value.
_CLDR_CALENDAR_SYSTEMS = (
    "buddhist",
    "chinese",
    "coptic",
    "dangi",
    "ethioaa",
    "ethiopic",
    "ethiopic-amete-alem",
    "gregorian",
    "gregory",
    "hebrew",
    "indian",
    "islamic",
    "islamic-civil",
    "islamic-rgsa",
    "islamic-tbla",
    "islamic-umalqura",
    "islamicc",
    "iso8601",
    "japanese",
    "persian",
    "roc",
)


class RecurrenceRule(JSCalendarObject):
    """A repeating pattern for recurring calendar objects (Section 3.3.3)."""

    type: Annotated[Literal["RecurrenceRule"], cites("Section 3.3.3")] = Field(
        default="RecurrenceRule", alias="@type"
    )
    frequency: Annotated[
        Literal["yearly", "monthly", "weekly", "daily", "hourly", "minutely", "secondly"],
        cites("Section 3.3.3"),
    ]
    interval: Annotated[int, Field(strict=True, ge=1, le=MAX_INT), cites("Section 3.3.3")] = 1
    rscale: Annotated[
        str,
        AfterValidator(_check_lowercase),
        open_enum(*_CLDR_CALENDAR_SYSTEMS),
        cites("Section 3.3.3"),
    ] = "gregorian"
    skip: Annotated[Literal["omit", "backward", "forward"], cites("Section 3.3.3")] = "omit"
    firstDayOfWeek: WeekDay = "mo"
    byDay: Annotated[list[NDay] | None, cites("Section 3.3.3")] = Field(default=None, min_length=1)
    byMonthDay: Annotated[
        list[Annotated[Int, AfterValidator(_check_nonzero), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    # RFC 7529: monthnum = 1*2DIGIT ["L"]; month numbering starts from 1.
    byMonth: Annotated[
        list[
            Annotated[
                str,
                Field(pattern=r"^[0-9]{1,2}L?$"),
                AfterValidator(_check_month_nonzero),
                cites("Section 3.3.3; RFC 7529"),
            ]
        ]
        | None,
        cites("Section 3.3.3; RFC 7529"),
    ] = Field(default=None, min_length=1)
    byYearDay: Annotated[
        list[Annotated[Int, AfterValidator(_check_nonzero), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    byWeekNo: Annotated[
        list[Annotated[Int, AfterValidator(_check_nonzero), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    byHour: Annotated[
        list[Annotated[int, Field(strict=True, ge=0, le=23), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    byMinute: Annotated[
        list[Annotated[int, Field(strict=True, ge=0, le=59), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    bySecond: Annotated[
        list[Annotated[int, Field(strict=True, ge=0, le=60), cites("Section 3.3.3")]] | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    bySetPosition: Annotated[list[Int] | None, cites("Section 3.3.3")] = Field(
        default=None, min_length=1
    )
    count: UnsignedInt | None = None
    until: LocalDateTime | None = None

    @model_validator(mode="after")
    def _validate(self) -> RecurrenceRule:
        if self.count is not None and self.until is not None:
            raise ValueError(
                'the "count" and "until" properties must not both be set (Section 3.3.3)'
            )
        if self.rscale in ("gregorian", "gregory", "iso8601"):
            for name, values, bound in (
                ("byMonthDay", self.byMonthDay, 31),
                ("byYearDay", self.byYearDay, 366),
                ("byWeekNo", self.byWeekNo, 53),
            ):
                for value in values or ():
                    if abs(value) > bound:
                        raise ValueError(
                            f'"{name}" values must be between -{bound} and {bound} '
                            f"in the gregorian calendar system (Section 3.3.3)"
                        )
            for month in self.byMonth or ():
                if month.endswith("L") or int(month) > 12:
                    raise ValueError(
                        '"byMonth" values must be between 1 and 12 with no leap '
                        "month suffix in the gregorian calendar system (Section 3.3.3)"
                    )
        return self


class NDay(JSCalendarObject):
    """A day of the week on which to repeat (Section 3.3.3)."""

    type: Annotated[Literal["NDay"], cites("Section 3.3.3")] = Field(default="NDay", alias="@type")
    day: WeekDay
    nthOfPeriod: Annotated[Int, AfterValidator(_check_nonzero), cites("Section 3.3.3")] | None = (
        None
    )


def _check_nonzero(value: int) -> int:
    if value == 0:
        raise ValueError("value must not be zero")
    return value


def _check_month_nonzero(value: str) -> str:
    if int(value.rstrip("L")) == 0:
        raise ValueError("month numbers start from 1")
    return value


def _check_lowercase(value: str) -> str:
    if value != value.lower():
        raise ValueError(f"{value!r} must be lowercase")
    return value


NDay.model_rebuild()
RecurrenceRule.model_rebuild()

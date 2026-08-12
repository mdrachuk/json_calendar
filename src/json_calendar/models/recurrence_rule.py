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

# The bounds implied by "the maximum number ... any month/year may have in
# the calendar given by the rscale property" (Section 3.3.3) per calendar
# system: the number of months in a year, whether RFC 7529 leap-month
# suffixes can occur, and the maximum days in any month and in any year (the
# byWeekNo bound follows from the latter). Vendor-specific calendar systems
# have no known bounds and are not checked.
_CALENDAR_BOUNDS: dict[str, tuple[int, bool, int, int]] = {
    "buddhist": (12, False, 31, 366),  # the Gregorian calendar with offset years
    "chinese": (12, True, 30, 385),  # lunisolar; leap years have a 13th lunation
    "coptic": (13, False, 30, 366),  # 12 30-day months plus the epagomenal 13th
    "dangi": (12, True, 30, 385),  # the Korean variant of the Chinese calendar
    "ethioaa": (13, False, 30, 366),
    "ethiopic": (13, False, 30, 366),
    "ethiopic-amete-alem": (13, False, 30, 366),
    "gregorian": (12, False, 31, 366),
    "gregory": (12, False, 31, 366),
    "hebrew": (12, True, 30, 385),  # lunisolar; leap years insert Adar I ("5L")
    "indian": (12, False, 31, 366),  # the Indian national (Saka) calendar
    "islamic": (12, False, 30, 355),  # lunar; all variants have 354- or 355-day years
    "islamic-civil": (12, False, 30, 355),
    "islamic-rgsa": (12, False, 30, 355),
    "islamic-tbla": (12, False, 30, 355),
    "islamic-umalqura": (12, False, 30, 355),
    "islamicc": (12, False, 30, 355),
    "iso8601": (12, False, 31, 366),
    "japanese": (12, False, 31, 366),  # the Gregorian calendar with era-based years
    "persian": (12, False, 31, 366),  # the Solar Hijri calendar
    "roc": (12, False, 31, 366),  # the Gregorian calendar with era-based years
}


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
    # RFC 5545, Section 3.3.10: BYSETPOS values must not be zero.
    bySetPosition: Annotated[
        list[Annotated[Int, AfterValidator(_check_nonzero), cites("Section 3.3.3; RFC 5545")]]
        | None,
        cites("Section 3.3.3"),
    ] = Field(default=None, min_length=1)
    count: UnsignedInt | None = None
    until: LocalDateTime | None = None

    @model_validator(mode="after")
    def _validate(self) -> RecurrenceRule:
        if self.count is not None and self.until is not None:
            raise ValueError(
                'the "count" and "until" properties must not both be set (Section 3.3.3)'
            )
        bounds = _CALENDAR_BOUNDS.get(self.rscale)
        if bounds is not None:
            months, has_leap_months, month_days, year_days = bounds
            for name, values, bound in (
                ("byMonthDay", self.byMonthDay, month_days),
                ("byYearDay", self.byYearDay, year_days),
                ("byWeekNo", self.byWeekNo, (year_days + 6) // 7),
            ):
                for value in values or ():
                    if abs(value) > bound:
                        raise ValueError(
                            f'"{name}" values must be between -{bound} and {bound} '
                            f"in the {self.rscale} calendar system (Section 3.3.3)"
                        )
            for month in self.byMonth or ():
                if month.endswith("L") and not has_leap_months:
                    raise ValueError(
                        f'"byMonth" values must have no leap month suffix in the '
                        f"{self.rscale} calendar system (Section 3.3.3; RFC 7529)"
                    )
                if int(month.rstrip("L")) > months:
                    raise ValueError(
                        f'"byMonth" month numbers must be between 1 and {months} '
                        f"in the {self.rscale} calendar system (Section 3.3.3)"
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

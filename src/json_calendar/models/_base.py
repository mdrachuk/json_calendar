"""The base class and shared value annotations for JSCalendar objects.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from json_calendar._types import is_valid_property_name


def _check_text_content_type(value: str) -> str:
    media_type, _, params = value.partition(";")
    if not media_type.strip().lower().startswith("text/"):
        raise ValueError(f"{value!r} is not a subtype of the 'text' media type")
    for param in params.split(";"):
        name, _, param_value = param.strip().partition("=")
        if name.lower() == "charset" and param_value.strip('"').lower() != "utf-8":
            raise ValueError("the 'charset' parameter value must be 'utf-8'")
    return value


def _check_color(value: str) -> str:
    if value.startswith("#"):
        hex_part = value[1:]
        if len(hex_part) != 6 or any(c not in "0123456789abcdefABCDEF" for c in hex_part):
            raise ValueError(f"{value!r} is not an RGB value in six-digit hexadecimal notation")
    elif not value.isalpha():
        raise ValueError(f"{value!r} is not a CSS color name")
    return value


JSCalendarVersion = Annotated[str, Field(pattern=r"^\d+\.\d+$")]
TextContentType = Annotated[str, AfterValidator(_check_text_content_type)]
Color = Annotated[str, AfterValidator(_check_color)]


class JSCalendarObject(BaseModel):
    """Base class for all JSCalendar objects.

    JSCalendar objects are JSON objects whose type is identified by the
    "@type" property. Properties unknown to this implementation are
    preserved through a parse/serialize round trip (Section 1.7.4), but
    their names must be syntactically valid and must not differ only in
    case from a known property (Section 1.7.1).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
        extra="allow",
    )

    @model_validator(mode="after")
    def _validate_extra_property_names(self) -> "JSCalendarObject":
        extra = self.__pydantic_extra__ or {}
        if not extra:
            return self
        known = {}
        for name, field in type(self).model_fields.items():
            alias = field.alias or name
            known[alias.lower()] = alias
            known[name.lower()] = name
        for key in extra:
            canonical = known.get(key.lower())
            if canonical is not None and key != canonical:
                raise ValueError(
                    f"property {key!r} differs only in case from the known "
                    f"property {canonical!r} (Section 1.7.1)"
                )
            if not is_valid_property_name(key):
                raise ValueError(f"{key!r} is not a valid property name")
        return self

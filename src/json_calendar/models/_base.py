"""The base class and shared value annotations for JSCalendar objects.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    ValidationError,
    ValidatorFunctionWrapHandler,
    model_validator,
)

from json_calendar._css3_colors import check_color
from json_calendar._spec import cite_errors, cites, property_citations
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


# This implementation supports only the JSCalendar version specified in
# jscalendarbis; version "1.0" objects follow the RFC 8984 schema instead.
JSCalendarVersion = Annotated[Literal["2.0"], cites("Section 3.1.2")]
TextContentType = Annotated[str, AfterValidator(_check_text_content_type), cites("Section 3.2.3")]
Color = Annotated[str, AfterValidator(check_color), cites("Section 3.2.12")]


class JSCalendarObject(BaseModel):
    """Base class for all JSCalendar objects.

    JSCalendar objects are JSON objects whose type is identified by the
    "@type" property. Properties unknown to this implementation are
    preserved through a parse/serialize round trip (Section 1.7.4), but
    their names must be syntactically valid and must not differ only in
    case from a known property (Section 1.7.1).
    """

    model_config = ConfigDict(
        serialize_by_alias=True,
        extra="allow",
    )

    @model_validator(mode="wrap")
    @classmethod
    def _cite_property_errors(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        """Cite the spec on errors no field validator sees, e.g. missing fields."""
        try:
            return handler(value)
        except ValidationError as error:
            citations = _property_citations(cls)
            raise cite_errors(
                error,
                lambda detail: citations.get(detail["loc"][0]) if detail["loc"] else None,
            ) from None

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
                raise ValueError(f"{key!r} is not a valid property name (Sections 1.7.2 and 1.8.1)")
        return self


_PROPERTY_CITATIONS_CACHE: dict[type[JSCalendarObject], dict[str, str]] = {}


def _property_citations(cls: type[JSCalendarObject]) -> dict[str, str]:
    citations = _PROPERTY_CITATIONS_CACHE.get(cls)
    if citations is None:
        citations = _PROPERTY_CITATIONS_CACHE[cls] = property_citations(cls.model_fields)
    return citations

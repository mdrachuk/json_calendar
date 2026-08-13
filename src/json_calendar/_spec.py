"""Spec citations for validation error messages.

Validation errors name the part of the specification that imposes the
violated rule, e.g. "'x' is not a URI (RFC 3986)". A bare "Section"
citation refers to the JSCalendar specification itself; rules imposed by
other documents are cited by the document name.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, LiteralString, cast

from pydantic import GetCoreSchemaHandler, ValidationError, ValidatorFunctionWrapHandler
from pydantic.fields import FieldInfo
from pydantic_core import (
    CoreSchema,
    ErrorDetails,
    InitErrorDetails,
    PydanticCustomError,
    core_schema,
)


@dataclass(frozen=True)
class Cites:
    """``Annotated`` metadata appending ``(spec)`` to validation errors.

    Use as the last ``Annotated`` metadata item so that the citation covers
    the constraints and validators declared before it. Error messages that
    already carry a citation, and error locations, are kept as they are.
    """

    spec: str

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(self._check, handler(source_type))

    def _check(self, value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        try:
            return handler(value)
        except ValidationError as error:
            raise cite_errors(error, lambda detail: self.spec) from None


def cites(spec: str) -> Cites:
    """Append ``(spec)`` to the message of every validation error of a type."""
    return Cites(spec)


def cite_errors(
    error: ValidationError, citation_for: Callable[[ErrorDetails], str | None]
) -> ValidationError:
    """Rebuild ``error``, appending citations to messages that lack one."""
    line_errors: list[InitErrorDetails] = []
    for detail in error.errors(include_url=False):
        message = detail["msg"]
        spec = citation_for(detail)
        if spec is not None and not any(marker in message for marker in _CITATION_MARKERS):
            message = f"{message.removeprefix('Value error, ')} ({spec})"
        # The LiteralString casts appease the stubs; without a context argument
        # the message is never treated as a format template.
        line_errors.append(
            {
                "type": PydanticCustomError(
                    cast("LiteralString", detail["type"]), cast("LiteralString", message)
                ),
                "loc": detail["loc"],
                "input": detail["input"],
            }
        )
    return ValidationError.from_exception_data(error.title, line_errors)


def property_citations(model_fields: dict[str, FieldInfo]) -> dict[str, str]:
    """Map each field's name and alias to the outermost citation of its type."""
    citations: dict[str, str] = {}
    for name, field in model_fields.items():
        spec = next(
            (meta.spec for meta in reversed(field.metadata) if isinstance(meta, Cites)), None
        )
        if spec is not None:
            citations[name] = spec
            citations[field.alias or name] = spec
    return citations


_CITATION_MARKERS = ("(Section", "(RFC")

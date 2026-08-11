"""Spec citations for validation error messages.

Validation errors name the part of the specification that imposes the
violated rule, e.g. "'x' is not a URI (RFC 3986)". A bare "Section"
citation refers to the JSCalendar specification itself; rules imposed by
other documents are cited by the document name.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from typing import Any

from pydantic import ValidationError, ValidatorFunctionWrapHandler, WrapValidator

_CITATION_MARKERS = ("(Section", "(RFC")


def cites(spec: str) -> WrapValidator:
    """Append ``(spec)`` to the message of every validation error of a type.

    Use as the last ``Annotated`` metadata item so that the citation covers
    the constraints and validators declared before it. Messages that already
    carry a citation are kept as they are.
    """

    def check(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        try:
            return handler(value)
        except ValidationError as error:
            messages = []
            for detail in error.errors(include_url=False):
                message = detail["msg"].removeprefix("Value error, ")
                if not any(marker in message for marker in _CITATION_MARKERS):
                    message = f"{message} ({spec})"
                messages.append(message)
            raise ValueError("; ".join(messages)) from None

    return WrapValidator(check)

# Accepted Deviations

This document records intentional differences between this library's validation behavior and
draft-ietf-calext-jscalendarbis-18.

## Optional properties accept `null`

The JSCalendar specification defines optional properties as properties that may be omitted. If an
optional property is present, its value is still required to match the property's declared type;
`null` is therefore not generally a valid value.

This library represents optional properties with nullable Pydantic fields and accepts explicit
`null` values for them. For example, an Event with `"created": null` is accepted. Unless
`exclude_none=True` is used when serializing, the explicit `null` may also be preserved in the
output.

Consumers requiring strict JSCalendar output should omit properties whose values are `None`, for
example with `model_dump(mode="json", exclude_none=True)`.

## Boolean set values may coerce numeric `1` to `true`

JSCalendar represents sets such as `keywords`, `categories`, `relation`, `roles`, `features`, and
`display` as JSON objects whose member values must be the JSON Boolean `true`.

These values are modeled with Pydantic's `Literal[True]`. As a result, numeric values equal to
`true`, notably JSON `1` and `1.0`, are accepted and normalized to `true`. This differs from strict
validation of the JSON value type required by the specification.

Consumers requiring strict input validation should reject non-Boolean set values before passing
data to these models.

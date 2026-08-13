# json-calendar

[![test](https://github.com/mdrachuk/json_calendar/actions/workflows/test.yml/badge.svg)](https://github.com/mdrachuk/json_calendar/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/json-calendar)](https://pypi.org/project/json-calendar/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python library for working with **JSCalendar 2.0**, as specified in
[draft-ietf-calext-jscalendarbis-18](https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html)
(the successor to [RFC 8984](https://www.rfc-editor.org/rfc/rfc8984)).

> ⚠️ Early development. The API is not stable yet.

## Components

- **Model & validator** — pydantic models for `Event`, `Task`, and `Group`
  objects and their value types. Answers "is this valid JSCalendar 2.0?" and
  gives you typed access to every property.
- **Recurrence engine** — expands `recurrenceRules`, applies
  `excludedRecurrenceRules` and `recurrenceOverrides`, and yields concrete
  occurrence instances.
- **iCalendar converter** — converts JSCalendar objects to and from
  iCalendar (RFC 5545).

## Installation

```sh
pip install json-calendar
# or
uv add json-calendar
```

Requires Python 3.11+.

## Usage

```python
from json_calendar import Event

event = Event.model_validate(
    {
        "@type": "Event",
        "version": "2.0",
        "uid": "a8df6573-0474-496d-8496-033ad45d7fea",
        "updated": "2020-01-02T18:23:04Z",
        "title": "Some event",
        "start": "2020-01-15T13:00:00",
        "timeZone": "America/New_York",
        "duration": "PT1H",
    }
)

assert event.start.isoformat() == "2020-01-15T13:00:00"
print(event.model_dump_json(exclude_unset=True))
```

## Development

The project uses [uv](https://docs.astral.sh/uv/) for project management,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting,
[ty](https://docs.astral.sh/ty/) for type checking, and
[pytest](https://docs.pytest.org/) for tests.

```sh
uv sync                  # create the venv and install dependencies
uv run pytest            # run tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run ty check          # type check
```

### Releasing

Pushing a `v*` tag builds the package, publishes it to PyPI (via
[trusted publishing](https://docs.pypi.org/trusted-publishers/)), and creates
a GitHub release:

```sh
git tag v0.1.0
git push origin v0.1.0
```

## License

[MIT](LICENSE)

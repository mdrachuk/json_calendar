"""JSCalendar 2.0 for Python.

A library for working with the JSCalendar 2.0 standard
(draft-ietf-calext-jscalendarbis): a data model and validator built on
pydantic, a recurrence engine, and a converter to/from iCalendar.

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

from json_calendar.models import Event, Group, JSCalendarObject, Task

__version__ = "0.1.0"

__all__ = [
    "Event",
    "Group",
    "JSCalendarObject",
    "Task",
    "__version__",
]

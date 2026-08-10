"""Evaluating and applying PatchObject patches (Section 1.5.9).

Spec: https://www.ietf.org/archive/id/draft-ietf-calext-jscalendarbis-18.html
"""

import re
from collections.abc import Callable, Mapping
from itertools import pairwise
from typing import Any

_BAD_ESCAPE = re.compile(r"~(?![01])")
_ARRAY_INDEX = re.compile(r"^(?:0|[1-9][0-9]*)$")


def apply_patch(
    target: dict[str, Any],
    patch: Mapping[str, Any],
    ignore: Callable[[list[str]], bool] = lambda tokens: False,
) -> dict[str, Any]:
    """Apply ``patch`` to ``target`` in place, raising ValueError on invalid patches.

    Pointers for which ``ignore`` returns true are skipped (Section 3.3.4).
    """
    for pointer, value in patch.items():
        tokens = parse_pointer(pointer)
        if ignore(tokens):
            continue
        node: Any = target
        for token in tokens[:-1]:
            if isinstance(node, list):
                node = node[_index(token, node, pointer)]
            elif isinstance(node, dict):
                if token not in node:
                    raise ValueError(
                        f"{token!r} in the pointer {pointer!r} does not exist "
                        f"in the object being patched"
                    )
                node = node[token]
            else:
                raise ValueError(f"the pointer {pointer!r} references inside a scalar value")
        last = tokens[-1]
        if isinstance(node, list):
            if value is None:
                raise ValueError(
                    f"the patch value for the array index pointer {pointer!r} must not be null"
                )
            node[_index(last, node, pointer)] = value
        elif isinstance(node, dict):
            if value is None:
                node.pop(last, None)
            else:
                node[last] = value
        else:
            raise ValueError(f"the pointer {pointer!r} references inside a scalar value")
    return target


def parse_pointer(key: str) -> list[str]:
    """Split a PatchObject key into its JSON Pointer reference tokens (RFC 6901)."""
    tokens = []
    for token in key.split("/"):
        if _BAD_ESCAPE.search(token):
            raise ValueError(f"invalid escape sequence in the JSON Pointer {key!r}")
        tokens.append(token.replace("~1", "/").replace("~0", "~"))
    return tokens


def check_no_prefix_collisions(pointers: Mapping[str, list[str]]) -> None:
    """Ensure no pointer is a prefix of another (Section 1.5.9, condition 3)."""
    keys = sorted(pointers, key=pointers.__getitem__)
    for shorter, longer in pairwise(keys):
        prefix, tokens = pointers[shorter], pointers[longer]
        if tokens[: len(prefix)] == prefix:
            raise ValueError(f"the patch {shorter!r} is a prefix of the patch {longer!r}")


def _index(token: str, array: list[Any], pointer: str) -> int:
    if not _ARRAY_INDEX.match(token):
        raise ValueError(f"{token!r} in the pointer {pointer!r} is not an array index")
    index = int(token)
    if index >= len(array):
        raise ValueError(f"no array member at {token!r} exists to patch by the pointer {pointer!r}")
    return index

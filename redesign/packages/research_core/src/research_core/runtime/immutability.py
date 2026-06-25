from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
from types import MappingProxyType
from typing import Any


def freeze_nested(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_nested(nested) for key, nested in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_nested(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_nested(item) for item in value)
    return deepcopy(value)


def freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("payload keys must be strings")
        return MappingProxyType(
            {key: freeze_json_value(nested) for key, nested in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        raise ValueError("payload values must be JSON-compatible")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("payload float values must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return deepcopy(value)
    raise ValueError("payload values must be JSON-compatible")


def thaw_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_json_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return deepcopy(value)
    raise ValueError("payload values must be JSON-compatible")

from decimal import Decimal
from math import inf, nan
from pathlib import Path
from types import MappingProxyType

import pytest
from research_core.runtime.immutability import freeze_json_value, freeze_nested, thaw_json_value


def test_freeze_json_value_recursively_copies_and_freezes_mappings_and_lists() -> None:
    value = {"items": [{"name": "source", "score": 1}], "tags": ["agent"]}

    frozen = freeze_json_value(value)
    value["items"][0]["score"] = 2
    value["tags"].append("mutated")

    assert isinstance(frozen, MappingProxyType)
    assert frozen["items"][0]["score"] == 1
    assert frozen["tags"] == ("agent",)
    with pytest.raises(TypeError):
        frozen["tags"] = ("changed",)


def test_freeze_json_value_rejects_non_json_compatible_values() -> None:
    invalid_values = (
        {"tags": {"agent"}},
        {"path": Path("source.md")},
        {"amount": Decimal("1.0")},
        {"nan": nan},
        {"inf": inf},
        {1: "non-string key"},
    )

    for value in invalid_values:
        with pytest.raises(ValueError, match="payload"):
            freeze_json_value(value)


def test_thaw_json_value_returns_mutable_plain_copies() -> None:
    frozen = freeze_json_value({"items": [{"name": "source"}], "tags": ["agent"]})

    thawed = thaw_json_value(frozen)
    thawed["items"][0]["name"] = "changed"
    thawed["tags"].append("new")

    assert thawed == {"items": [{"name": "changed"}], "tags": ["agent", "new"]}
    assert frozen["items"][0]["name"] == "source"
    assert frozen["tags"] == ("agent",)


def test_thaw_json_value_rejects_non_json_compatible_frozen_values() -> None:
    with pytest.raises(ValueError, match="payload values must be JSON-compatible"):
        thaw_json_value(frozenset({"agent"}))


def test_freeze_nested_recursively_freezes_standard_containers() -> None:
    value = {
        "items": [{"name": "source"}],
        "tags": {"agent", "research"},
    }

    frozen = freeze_nested(value)
    value["items"][0]["name"] = "changed"
    value["tags"].add("mutated")

    assert isinstance(frozen, MappingProxyType)
    assert frozen["items"][0]["name"] == "source"
    assert frozen["tags"] == frozenset({"agent", "research"})

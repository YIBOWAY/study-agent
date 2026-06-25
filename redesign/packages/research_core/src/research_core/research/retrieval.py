from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from research_core.research.entities import Source, _freeze_metadata, _require_non_empty

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class SearchResult:
    source_id: str
    title: str
    snippet: str
    score: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("source_id", self.source_id)
        _require_non_empty("title", self.title)
        _require_non_empty("snippet", self.snippet)
        if not isinstance(self.score, int) or isinstance(self.score, bool) or self.score <= 0:
            raise ValueError("score must be a positive integer")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class FakeRetriever:
    def __init__(self, sources: Sequence[Source]) -> None:
        source_tuple = tuple(sources)
        if any(not isinstance(source, Source) for source in source_tuple):
            raise ValueError("sources must contain Source objects")
        self._sources = source_tuple

    def search(self, query: str, limit: int = 10) -> tuple[SearchResult, ...]:
        _require_non_empty("query", query)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit must be a positive integer")

        query_tokens = tuple(dict.fromkeys(_tokenize(query)))
        if not query_tokens:
            raise ValueError("query must contain at least one searchable token")

        scored_results: list[tuple[int, int, SearchResult]] = []
        normalized_query = query.casefold().strip()
        for index, source in enumerate(self._sources):
            score = self._score(source, query_tokens, normalized_query)
            if score <= 0:
                continue
            scored_results.append(
                (
                    score,
                    index,
                    SearchResult(
                        source_id=source.id,
                        title=source.title,
                        snippet=_snippet(source.content),
                        score=score,
                        metadata={"uri": source.uri},
                    ),
                )
            )

        scored_results.sort(key=lambda item: (-item[0], item[1]))
        return tuple(result for _, _, result in scored_results[:limit])

    def _score(
        self,
        source: Source,
        query_tokens: Sequence[str],
        normalized_query: str,
    ) -> int:
        title_tokens = set(_tokenize(source.title))
        content_tokens = set(_tokenize(source.content))
        combined = f"{source.title}\n{source.content}".casefold()

        matched_tokens = sum(
            1 for token in query_tokens if token in title_tokens or token in content_tokens
        )
        title_bonus = sum(1 for token in query_tokens if token in title_tokens)
        phrase_bonus = 1 if normalized_query in combined else 0
        return matched_tokens + title_bonus + phrase_bonus


def _tokenize(value: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _TOKEN_PATTERN.finditer(value))


def _snippet(content: str) -> str:
    return content.strip()[:140]

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    start_char: int
    end_char: int


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def chunk_text(text: str, max_chars: int = 900, overlap_chars: int = 120) -> list[TextChunk]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    if max_chars < 1:
        raise ValueError("max_chars must be greater than zero")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be greater than or equal to zero")
    if len(normalized) <= max_chars:
        return [TextChunk(chunk_index=0, content=normalized, start_char=0, end_char=len(normalized))]

    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        hard_end = min(start + max_chars, len(normalized))
        end = hard_end
        if hard_end < len(normalized):
            boundary = normalized.rfind(" ", start + 1, hard_end)
            if boundary > start:
                end = boundary
        if end <= start:
            end = hard_end
        chunks.append(
            TextChunk(
                chunk_index=len(chunks),
                content=normalized[start:end],
                start_char=start,
                end_char=end,
            )
        )
        if end >= len(normalized):
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        while next_start > 0 and normalized[next_start] != " ":
            next_start -= 1
        start = next_start + 1 if next_start > 0 else next_start
    return chunks

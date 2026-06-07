import pytest
from pydantic import ValidationError

from serviceops_api.knowledge_base.chunking import chunk_text
from serviceops_api.knowledge_base.embeddings import DeterministicEmbeddingProvider, cosine_similarity
from serviceops_api.knowledge_base.models import IngestKnowledgeDocumentPayload


def test_ingest_payload_rejects_blank_body() -> None:
    with pytest.raises(ValidationError):
        IngestKnowledgeDocumentPayload(title="E61 guide", body="   ")


def test_short_text_produces_one_chunk_with_offsets() -> None:
    text = "Inspect the thermosiphon loop before replacing the pressurestat."

    chunks = chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == text
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)


def test_long_text_produces_ordered_overlapping_chunks() -> None:
    text = " ".join(f"section-{index:03d}" for index in range(90))

    chunks = chunk_text(text, max_chars=120, overlap_chars=24)

    assert len(chunks) > 1
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0].start_char == 0
    assert chunks[-1].end_char == len(text)
    for previous, current in zip(chunks, chunks[1:]):
        assert current.start_char < previous.end_char
        assert current.end_char > previous.end_char
        assert current.content == text[current.start_char : current.end_char]


def test_deterministic_embeddings_rank_related_text_higher() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=12)

    query, related, unrelated = provider.embed_texts(
        [
            "E61 overheating thermosiphon scale boiler pressure",
            "Scale in the thermosiphon can overheat an E61 group",
            "Burr alignment changes espresso grinder retention",
        ]
    )

    assert len(query) == 12
    assert provider.embed_texts(["E61 overheating"])[0] == provider.embed_texts(["E61 overheating"])[0]
    assert cosine_similarity(query, related) > cosine_similarity(query, unrelated)

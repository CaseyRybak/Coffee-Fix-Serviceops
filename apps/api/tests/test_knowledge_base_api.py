import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.knowledge_base.repository import SqliteKnowledgeBaseRepository
from serviceops_api.service_requests.repository import ServiceRequestRepository


DOCUMENT_PAYLOAD = {
    "title": "E61 group overheating guide",
    "source_uri": "seed://repair/e61-overheating",
    "body": (
        "E61 overheating is often caused by scale in the thermosiphon loop. "
        "Descale the group, inspect flow restrictors, and confirm boiler pressure "
        "before replacing the pressurestat."
    ),
    "metadata": {"machine_family": "E61"},
}


def create_test_app():
    app = create_app(
        service_request_repository=ServiceRequestRepository.in_memory(),
        knowledge_base_repository=SqliteKnowledgeBaseRepository.in_memory(),
    )
    return app


async def post_json(path: str, body: dict[str, object]) -> httpx.Response:
    app = create_test_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body)


def test_ingests_text_document_with_embedded_chunks() -> None:
    response = asyncio.run(post_json("/knowledge-base/documents", DOCUMENT_PAYLOAD))

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == 1
    assert body["title"] == "E61 group overheating guide"
    assert body["source_uri"] == "seed://repair/e61-overheating"
    assert body["status"] == "embedded"
    assert body["chunk_count"] > 0


def test_retrieves_relevant_chunks_with_source_metadata() -> None:
    async def scenario() -> tuple[httpx.Response, dict[str, object], dict[str, object]]:
        app = create_test_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            e61_response = await client.post("/knowledge-base/documents", json=DOCUMENT_PAYLOAD)
            grinder_response = await client.post(
                "/knowledge-base/documents",
                json={
                    "title": "Grinder burr alignment guide",
                    "source_uri": "seed://repair/grinder-burr-alignment",
                    "body": (
                        "Burr alignment issues change espresso grinder retention and particle distribution. "
                        "Inspect carrier wobble, clean retained grounds, and recalibrate the grind setting."
                    ),
                },
            )
            retrieval_response = await client.post(
                "/knowledge-base/retrieval",
                json={"query": "why is my E61 group overheating after descaling", "limit": 1},
            )
        return retrieval_response, e61_response.json(), grinder_response.json()

    response, e61_document, grinder_document = asyncio.run(scenario())

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "why is my E61 group overheating after descaling"
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["document_id"] == e61_document["document_id"]
    assert result["document_id"] != grinder_document["document_id"]
    assert result["document_title"] == "E61 group overheating guide"
    assert result["source_uri"] == "seed://repair/e61-overheating"
    assert result["chunk_id"] >= 1
    assert result["chunk_index"] == 0
    assert result["start_char"] == 0
    assert result["end_char"] > result["start_char"]
    assert "thermosiphon" in result["content"]
    assert result["score"] > 0

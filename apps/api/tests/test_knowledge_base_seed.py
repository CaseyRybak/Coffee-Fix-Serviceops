import asyncio

import httpx

from serviceops_api.knowledge_base.repository import SqliteKnowledgeBaseRepository
from serviceops_api.knowledge_base.seed_documents import REPAIR_KNOWLEDGE_SEED_DOCUMENTS
from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def test_e61_overheating_seed_document_captures_repair_knowledge() -> None:
    seed = REPAIR_KNOWLEDGE_SEED_DOCUMENTS[0]

    assert "E61 overheating" in seed.title
    assert seed.source_uri == "seed://repair/e61-overheating"
    assert "thermosiphon" in seed.body
    assert "scale" in seed.body
    assert "boiler pressure" in seed.body
    assert "pressurestat" in seed.body


def test_seed_document_can_be_retrieved_by_repair_question() -> None:
    async def scenario() -> httpx.Response:
        app = create_app(
            service_request_repository=ServiceRequestRepository.in_memory(),
            knowledge_base_repository=SqliteKnowledgeBaseRepository.in_memory(),
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post("/knowledge-base/documents", json=REPAIR_KNOWLEDGE_SEED_DOCUMENTS[0].model_dump())
            return await client.post(
                "/knowledge-base/retrieval",
                json={"query": "E61 overheating pressure", "limit": 1},
            )

    response = asyncio.run(scenario())

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["document_title"] == REPAIR_KNOWLEDGE_SEED_DOCUMENTS[0].title
    assert result["source_uri"] == "seed://repair/e61-overheating"

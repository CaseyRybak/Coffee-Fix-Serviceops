from __future__ import annotations

from fastapi import APIRouter, status

from serviceops_api.knowledge_base.models import (
    IngestKnowledgeDocumentPayload,
    KnowledgeDocumentResponse,
    KnowledgeRetrievalPayload,
    KnowledgeRetrievalResponse,
)
from serviceops_api.knowledge_base.use_cases import IngestKnowledgeDocument, RetrieveKnowledge


def create_knowledge_base_router(
    ingest_document: IngestKnowledgeDocument,
    retrieve_knowledge: RetrieveKnowledge,
) -> APIRouter:
    router = APIRouter(prefix="/knowledge-base", tags=["knowledge base"])

    @router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
    async def create_knowledge_document(payload: IngestKnowledgeDocumentPayload) -> KnowledgeDocumentResponse:
        return ingest_document.execute(payload)

    @router.post("/retrieval", response_model=KnowledgeRetrievalResponse)
    async def retrieve_knowledge_chunks(payload: KnowledgeRetrievalPayload) -> KnowledgeRetrievalResponse:
        return retrieve_knowledge.execute(payload)

    return router

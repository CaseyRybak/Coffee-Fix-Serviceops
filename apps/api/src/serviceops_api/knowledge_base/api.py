from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, status

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
    write_dependency: Callable[..., object] | None = None,
    read_dependency: Callable[..., object] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/knowledge-base", tags=["knowledge base"])
    write_dependencies = [Depends(write_dependency)] if write_dependency is not None else []
    read_dependencies = [Depends(read_dependency)] if read_dependency is not None else write_dependencies

    @router.post(
        "/documents",
        response_model=KnowledgeDocumentResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=write_dependencies,
    )
    async def create_knowledge_document(payload: IngestKnowledgeDocumentPayload) -> KnowledgeDocumentResponse:
        return ingest_document.execute(payload)

    @router.post("/retrieval", response_model=KnowledgeRetrievalResponse, dependencies=read_dependencies)
    async def retrieve_knowledge_chunks(payload: KnowledgeRetrievalPayload) -> KnowledgeRetrievalResponse:
        return retrieve_knowledge.execute(payload)

    return router

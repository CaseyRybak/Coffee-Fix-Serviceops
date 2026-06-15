from __future__ import annotations

from dataclasses import dataclass

from serviceops_api.knowledge_base.models import KnowledgeRetrievalPayload
from serviceops_api.knowledge_base.use_cases import RetrieveKnowledge


@dataclass(frozen=True)
class RagEvaluationCase:
    query: str
    expected_source_uri: str
    expected_terms: list[str]


RAG_EVALUATION_CASES = [
    RagEvaluationCase(
        query="E61 overheats after descaling",
        expected_source_uri="seed://repair/e61-overheating",
        expected_terms=["thermosiphon", "pressurestat", "boiler pressure"],
    ),
    RagEvaluationCase(
        query="Jura no coffee flow",
        expected_source_uri="seed://repair/no-coffee-flow",
        expected_terms=["brew unit", "flow meter", "pump"],
    ),
    RagEvaluationCase(
        query="DeLonghi не включается нет питания",
        expected_source_uri="seed://repair/no-power-startup",
        expected_terms=["розетка", "кабель", "плата питания"],
    ),
    RagEvaluationCase(
        query="Bosch бьет током при касании корпуса",
        expected_source_uri="seed://repair/electric-shock-safety",
        expected_terms=["не пользоваться", "заземление", "УЗО"],
    ),
    RagEvaluationCase(
        query="milk foam weak",
        expected_source_uri="seed://repair/milk-foam-weak",
        expected_terms=["cappuccinatore", "air intake", "milk tube"],
    ),
    RagEvaluationCase(
        query="coffee machine leaking water",
        expected_source_uri="seed://repair/water-leak-triage",
        expected_terms=["tank valve", "drip tray", "hydraulic circuit"],
    ),
    RagEvaluationCase(
        query="grinder spins but no beans ground",
        expected_source_uri="seed://repair/grinder-not-grinding",
        expected_terms=["burrs", "blocked chute", "weak coffee extraction"],
    ),
    RagEvaluationCase(
        query="how often descale hard water",
        expected_source_uri="seed://repair/descaling-hard-water",
        expected_terms=["hard water", "descaling", "filter"],
    ),
]


def run_rag_evaluation(retrieve: RetrieveKnowledge) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for case in RAG_EVALUATION_CASES:
        response = retrieve.execute(KnowledgeRetrievalPayload(query=case.query, limit=3))
        source_uris = [result.source_uri for result in response.results]
        combined_content = "\n".join(result.content.lower() for result in response.results)
        term_matched = any(term.lower() in combined_content for term in case.expected_terms)
        expected_source_found = case.expected_source_uri in source_uris
        results.append(
            {
                "query": case.query,
                "expected_source_uri": case.expected_source_uri,
                "top_source_uris": source_uris,
                "term_matched": term_matched,
                "passed": expected_source_found and term_matched,
            }
        )
    return results

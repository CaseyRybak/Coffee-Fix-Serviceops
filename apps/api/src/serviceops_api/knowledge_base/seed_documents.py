from __future__ import annotations

from serviceops_api.knowledge_base.models import IngestKnowledgeDocumentPayload


REPAIR_KNOWLEDGE_SEED_DOCUMENTS = [
    IngestKnowledgeDocumentPayload(
        title="E61 overheating repair guide",
        source_uri="seed://repair/e61-overheating",
        body=(
            "E61 overheating after warmup or descaling is commonly caused by scale in the thermosiphon loop, "
            "restricted group flow, or excessive boiler pressure. Confirm boiler pressure first, then inspect "
            "the thermosiphon inlet and outlet for scale, clean flow restrictors, and verify that group water "
            "circulates steadily before replacing the pressurestat. If pressure climbs above the machine "
            "specification during idle, test the pressurestat contacts and pressure line for blockage."
        ),
        metadata={"machine_family": "E61", "topic": "overheating"},
    )
]

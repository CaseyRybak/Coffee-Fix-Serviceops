from __future__ import annotations

from serviceops_api.knowledge_base.models import IngestKnowledgeDocumentPayload


REPAIR_KNOWLEDGE_SEED_DOCUMENTS = [
    IngestKnowledgeDocumentPayload(
        title="E61 overheating repair guide",
        source_uri="seed://repair/e61-overheating",
        body=(
            "E61 overheating after warmup or descaling is commonly caused by scale in the thermosiphon loop, "
            "restricted group flow, or excessive boiler pressure. For an E61 overheats after descaling report, "
            "confirm boiler pressure first, then inspect the thermosiphon inlet and outlet for scale, clean flow "
            "restrictors, and verify that group water circulates steadily before replacing the pressurestat. "
            "If pressure climbs above the machine specification during idle, test the pressurestat contacts and "
            "pressure line for blockage. Escalate to a senior technician when overheating continues after the "
            "thermosiphon path is cleaned and boiler pressure remains within specification."
        ),
        metadata={"machine_family": "E61", "topic": "overheating", "symptom": "overheats after descaling"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Jura Saeco DeLonghi no coffee flow diagnostics",
        source_uri="seed://repair/no-coffee-flow",
        body=(
            "Jura no coffee flow, Saeco no coffee flow, and DeLonghi no coffee flow cases should start with "
            "basic hydraulic checks. Listen for pump sound, check whether water reaches the brew unit, inspect "
            "the drainage valve, brew group seals, flow meter, and outlet path. After descaling, scale fragments "
            "can block the thermoblock, solenoid, or coffee spout. If hot water works but coffee does not, focus "
            "on the brew group and coffee circuit. If neither hot water nor coffee flows, test pump prime, tank "
            "valve, air lock, and flow meter signal before replacing parts. Jura no coffee flow diagnostics should "
            "repeat the key checks: Jura no coffee flow, brew unit, flow meter, pump, drainage valve, blocked spout."
        ),
        metadata={"brand": "Jura Saeco DeLonghi", "topic": "hydraulics", "symptom": "no coffee flow"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Coffee machine no power startup triage",
        source_uri="seed://repair/no-power-startup",
        body=(
            "Кофемашина не включается, перестала включаться, не подает признаков жизни, не горит дисплей, "
            "нет питания или не реагирует на кнопку включения - это первично электрический симптом, а не "
            "проблема протока воды. Для DeLonghi и других автоматических машин сначала уточнить, "
            "горит ли дисплей или индикаторы и проверена ли другая розетка. Попросить клиента проверить розетку "
            "другим прибором, сетевой кабель, плотность вилки, главный выключатель, удлинитель и следы перепада "
            "напряжения. Если машина полностью мертвая, не спрашивать про звук помпы, бак воды, пролив, дренажный "
            "клапан или flow meter, пока клиент не подтвердил, что машина включается и запускает цикл. Вероятные "
            "причины: кабель, кнопка питания, предохранитель, плата питания, плата управления или влага. "
            "При запахе гари, искрении или воде внутри корпуса "
            "не включать повторно и передать мастеру для безопасной диагностики."
        ),
        metadata={"topic": "electrical startup", "symptom": "не включается нет питания", "brand": "DeLonghi Jura Saeco"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Grinder spins but beans are not ground",
        source_uri="seed://repair/grinder-not-grinding",
        body=(
            "When the grinder spins but no beans are ground, verify beans are dry and feeding into the burrs. "
            "Weak coffee extraction can come from a blocked chute, oily beans, worn burrs, a loose adjustment "
            "ring, or a foreign object in the grinder. Ask whether the customer hears a high free-spinning sound "
            "or a stalled motor hum. Inspect the bean hopper gate, clean the chute, check burr wear, and recalibrate "
            "grind size only after the mechanical obstruction is removed. Escalate when the motor overheats, smells "
            "burned, or the gearbox slips under load. Grinder spins but no beans ground is a grinder not grinding "
            "intake phrase; repeat grinder spins, beans ground, burrs, blocked chute, weak coffee extraction."
        ),
        metadata={"topic": "grinder", "symptom": "grinder spins no beans ground"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Milk foam weak cappuccinatore cleaning",
        source_uri="seed://repair/milk-foam-weak",
        body=(
            "Milk foam weak, large bubbles, or no suction usually means the cappuccinatore, air intake, milk tube, "
            "or steam path needs cleaning. Confirm cold fresh milk is used, then rinse the milk circuit, remove the "
            "frother head, clean the air hole with a non-damaging tool, and check tube cracks or loose fittings. "
            "For automatic machines, run the milk cleaning cycle and inspect the connector seals. For professional "
            "machines, compare steam pressure and purge water from the wand before blaming the boiler. Escalate "
            "when steam is weak across all functions or when the valve leaks."
        ),
        metadata={"topic": "milk system", "symptom": "milk foam weak", "maintenance": "cappuccinatore cleaning"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Coffee machine leaking water triage",
        source_uri="seed://repair/water-leak-triage",
        body=(
            "Coffee machine leaking water should be triaged by leak location. Water under the tank suggests tank "
            "valve, gasket, or cracked reservoir. Water in the drip tray after each drink can be normal, but rapid "
            "filling points to a drainage valve, brew unit seal, or overpressure valve. Water under the machine "
            "during heating suggests hydraulic circuit hoses, thermoblock fittings, boiler seals, or steam valve "
            "leaks. Ask whether the leak happens idle, during brew, during steam, or only after cleaning. Escalate "
            "immediately for electrical wetness or boiler seam leakage."
        ),
        metadata={"topic": "leaks", "symptom": "coffee machine leaking water"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Descaling and hard water maintenance intervals",
        source_uri="seed://repair/descaling-hard-water",
        body=(
            "How often descale hard water depends on water hardness, daily drink count, and filter use. In hard "
            "water regions without a filter, home machines may need descaling every one to two months; office and "
            "coffee shop machines need scheduled maintenance by throughput. Use manufacturer descaler, never vinegar "
            "on machines where it damages seals or leaves odor. After descaling, rinse until water is clear and "
            "verify flow through hot water, brew, and steam circuits. If descaling worsens flow, suspect loosened "
            "scale blocking a solenoid, thermoblock, or restrictor."
        ),
        metadata={"topic": "maintenance", "maintenance": "descaling", "symptom": "hard water scale"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Display error code intake checklist",
        source_uri="seed://repair/display-error-code-intake",
        body=(
            "For display error code intake, record the exact code text, brand, model, when the code appears, and "
            "what the machine does before stopping. Ask whether the error follows startup, heating, grinding, brew, "
            "rinsing, milk preparation, or descaling. Common categories are flow meter errors, grinder blocked, brew "
            "unit position errors, temperature sensor faults, and water tank detection. Do not promise a diagnosis "
            "from the code alone. Request a photo of the display and the last maintenance action, then route to the "
            "brand-specific diagnostic procedure."
        ),
        metadata={"topic": "intake", "symptom": "display error code"},
    ),
    IngestKnowledgeDocumentPayload(
        title="Professional machine pressure and steam triage",
        source_uri="seed://repair/professional-pressure-steam",
        body=(
            "Professional machine pressure and steam problems require separating brew pressure, boiler pressure, "
            "and steam performance. Low brew pressure can come from pump adjustment, pump wear, inlet restriction, "
            "blocked group jet, or incorrect grind. Weak steam can come from boiler pressure setting, heating element "
            "fault, vacuum breaker, scale in the steam valve, or oversized demand during peak service. Record gauge "
            "readings at idle and during extraction, confirm water supply and filtration, and ask whether symptoms "
            "affect one group or all groups. Escalate for pressure safety valve discharge or unstable boiler control."
        ),
        metadata={"machine_family": "professional", "topic": "pressure steam", "symptom": "weak steam pressure"},
    ),
]

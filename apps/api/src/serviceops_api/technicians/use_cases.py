from __future__ import annotations

from typing import Protocol

from serviceops_api.staff_auth import StaffUser
from serviceops_api.scheduling.models import validate_window
from serviceops_api.technicians.models import (
    DiagnosisChecklistPayload,
    RecordPartsUsedPayload,
    RepairResultPayload,
    TechnicianActionResponse,
    TechnicianProfileListResponse,
    TechnicianProfilePayload,
    TechnicianProfileSnapshot,
    TechnicianRecommendationResponse,
    TechnicianRequestDetail,
    TechnicianRequestListResponse,
)
from serviceops_api.inventory.repository import InventoryStore


class TechnicianServiceRequestStore(Protocol):
    def list_requests_for_technician(self, technician_identifier: str) -> list[dict[str, object]]:
        """Return requests assigned to a technician."""

    def get_technician_request(self, request_number: str, technician_identifier: str) -> dict[str, object]:
        """Return a technician-safe request detail."""

    def record_technician_diagnosis(
        self,
        request_number: str,
        technician_identifier: str,
        checklist: dict[str, bool],
        summary: str,
        actor: str,
    ) -> str:
        """Persist diagnosis and append a status event."""

    def record_technician_result(
        self,
        request_number: str,
        technician_identifier: str,
        result: str,
        summary: str,
        next_step: str | None,
        actor: str,
    ) -> str:
        """Persist repair result and append a status event."""

    def record_technician_parts_used_status(
        self,
        request_number: str,
        technician_identifier: str,
        actor: str,
    ) -> str:
        """Append a request-history event after parts usage."""

    def get_technician_recommendation_request(self, request_number: str) -> dict[str, object]:
        """Return request fields needed by deterministic technician recommendation."""

    def count_scheduled_appointments_for_technician(self, technician_identifier: str) -> int:
        """Return active scheduled appointment count for workload ranking."""

    def has_appointment_overlap_for_technician(self, technician_identifier: str, starts_at: str, ends_at: str) -> bool:
        """Return whether the technician is already booked in a requested window."""


class StaffAccountReader(Protocol):
    def list_accounts(self) -> list[dict[str, object]]:
        """List staff accounts."""

    def get_account_by_username(self, username: str) -> dict[str, object] | None:
        """Return one staff account."""

    def record_audit_event(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        """Record a safe staff audit event."""


class TechnicianProfileStore(Protocol):
    def list_profiles(self) -> list[dict[str, object]]:
        """Return technician profiles."""

    def get_profile(self, staff_username: str) -> dict[str, object] | None:
        """Return one technician profile."""

    def upsert_profile(
        self,
        staff_username: str,
        *,
        active: bool,
        skill_brands: list[str],
        service_regions: list[str],
        notes: str | None,
    ) -> dict[str, object]:
        """Create or update one technician profile."""


def technician_identifier(staff: StaffUser) -> str:
    return staff.username


class ListTechnicianRequests:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, staff: StaffUser) -> TechnicianRequestListResponse:
        return TechnicianRequestListResponse.model_validate(
            {"items": self._repository.list_requests_for_technician(technician_identifier(staff))}
        )


class GetTechnicianRequest:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, staff: StaffUser) -> TechnicianRequestDetail:
        return TechnicianRequestDetail.model_validate(
            self._repository.get_technician_request(request_number, technician_identifier(staff))
        )


class RecordTechnicianDiagnosis:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        payload: DiagnosisChecklistPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        status = self._repository.record_technician_diagnosis(
            request_number=request_number,
            technician_identifier=technician_identifier(staff),
            checklist={
                "machine_powered_on": payload.machine_powered_on,
                "water_supply_checked": payload.water_supply_checked,
                "leak_checked": payload.leak_checked,
                "error_code_checked": payload.error_code_checked,
            },
            summary=payload.summary,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician diagnosis recorded",
        )


class RecordTechnicianResult:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        payload: RepairResultPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        status = self._repository.record_technician_result(
            request_number=request_number,
            technician_identifier=technician_identifier(staff),
            result=payload.result,
            summary=payload.summary,
            next_step=payload.next_step,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician result recorded",
        )


class RecordTechnicianPartsUsed:
    def __init__(self, service_repository: TechnicianServiceRequestStore, inventory_repository: InventoryStore) -> None:
        self._service_repository = service_repository
        self._inventory_repository = inventory_repository

    def execute(
        self,
        request_number: str,
        payload: RecordPartsUsedPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        identifier = technician_identifier(staff)
        self._service_repository.get_technician_request(request_number, identifier)
        self._inventory_repository.record_parts_used(
            request_number=request_number,
            part_id=payload.part_id,
            quantity=payload.quantity,
            note=payload.note,
            actor="technician",
        )
        status = self._service_repository.record_technician_parts_used_status(
            request_number=request_number,
            technician_identifier=identifier,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician parts used recorded",
        )


class ListTechnicianProfiles:
    def __init__(self, profile_repository: TechnicianProfileStore, staff_repository: StaffAccountReader) -> None:
        self._profile_repository = profile_repository
        self._staff_repository = staff_repository

    def execute(self) -> TechnicianProfileListResponse:
        profiles = {str(profile["staff_username"]): profile for profile in self._profile_repository.list_profiles()}
        items = [
            _profile_snapshot(account, profiles.get(str(account["username"])))
            for account in self._staff_repository.list_accounts()
            if "technician" in account["roles"]
        ]
        return TechnicianProfileListResponse(items=items)


class UpsertTechnicianProfile:
    def __init__(self, profile_repository: TechnicianProfileStore, staff_repository: StaffAccountReader) -> None:
        self._profile_repository = profile_repository
        self._staff_repository = staff_repository

    def execute(self, username: str, payload: TechnicianProfilePayload, actor: str) -> TechnicianProfileSnapshot:
        account = self._staff_repository.get_account_by_username(username)
        if account is None:
            raise KeyError(username)
        if "technician" not in account["roles"]:
            raise ValueError("Staff account must have technician role")
        profile = self._profile_repository.upsert_profile(
            username,
            active=payload.active,
            skill_brands=payload.skill_brands,
            service_regions=payload.service_regions,
            notes=payload.notes,
        )
        self._staff_repository.record_audit_event(
            actor,
            username,
            "technician_profile.upserted",
            {
                "active": payload.active,
                "skill_brand_count": len(payload.skill_brands),
                "service_region_count": len(payload.service_regions),
            },
        )
        return _profile_snapshot(account, profile)


class RecommendTechnicians:
    def __init__(
        self,
        service_repository: TechnicianServiceRequestStore,
        profile_repository: TechnicianProfileStore,
        staff_repository: StaffAccountReader,
    ) -> None:
        self._service_repository = service_repository
        self._profile_repository = profile_repository
        self._staff_repository = staff_repository

    def execute(
        self,
        request_number: str,
        *,
        starts_at: str | None = None,
        ends_at: str | None = None,
    ) -> TechnicianRecommendationResponse:
        if (starts_at is None) != (ends_at is None):
            raise ValueError("starts_at and ends_at must be provided together")
        if starts_at is not None and ends_at is not None:
            validate_window(starts_at, ends_at)

        request = self._service_repository.get_technician_recommendation_request(request_number)
        profiles = {str(profile["staff_username"]): profile for profile in self._profile_repository.list_profiles()}
        items = [
            self._recommendation_item(account, profiles.get(str(account["username"])), request, starts_at, ends_at)
            for account in self._staff_repository.list_accounts()
            if "technician" in account["roles"]
        ]
        items.sort(
            key=lambda item: (
                -int(item["score"]),
                int(item["scheduled_visit_count"]),
                str(item["display_name"]),
                str(item["staff_username"]),
            )
        )
        return TechnicianRecommendationResponse.model_validate({"request": request, "items": items})

    def _recommendation_item(
        self,
        account: dict[str, object],
        profile: dict[str, object] | None,
        request: dict[str, object],
        starts_at: str | None,
        ends_at: str | None,
    ) -> dict[str, object]:
        username = str(account["username"])
        skill_brands = list(profile["skill_brands"]) if profile else []
        service_regions = list(profile["service_regions"]) if profile else []
        profile_active = bool(profile["active"]) if profile else True
        staff_active = bool(account["active"])
        request_brand = str(request["brand"])
        request_address = str(request["address"])
        scheduled_count = self._service_repository.count_scheduled_appointments_for_technician(username)
        reasons: list[str] = []
        risks: list[str] = []
        score = 0

        if staff_active:
            score += 15
            reasons.append("Staff account is active")
        else:
            score -= 100
            risks.append("Staff account is inactive")

        if profile is None:
            risks.append("Technician profile is not configured")
        elif profile_active:
            score += 20
            reasons.append("Technician profile is active")
        else:
            score -= 100
            risks.append("Profile is inactive")

        if _contains_casefold(skill_brands, request_brand):
            score += 40
            reasons.append(f"Brand match: {request_brand}")
        elif skill_brands:
            risks.append(f"Brand mismatch: request {request_brand}")
        else:
            risks.append("No brand skills configured")

        matched_region = _matched_region(service_regions, request_address)
        if matched_region:
            score += 30
            reasons.append(f"Region match: {matched_region}")
        elif service_regions:
            risks.append("Region mismatch for request address")
        else:
            risks.append("No service regions configured")

        if starts_at is not None and ends_at is not None:
            if self._service_repository.has_appointment_overlap_for_technician(username, starts_at, ends_at):
                score -= 100
                risks.append("Scheduling conflict in requested window")
            else:
                score += 10
                reasons.append("No scheduling conflict in requested window")
        else:
            risks.append("No appointment window provided; schedule conflict will be checked when booking")

        if scheduled_count == 0:
            score += 5
            reasons.append("No active scheduled visits")
        else:
            risks.append(f"Active scheduled visits: {scheduled_count}")

        return {
            "staff_username": username,
            "display_name": str(account["display_name"]),
            "phone": str(account.get("phone", "")),
            "score": score,
            "active": profile_active,
            "staff_active": staff_active,
            "skill_brands": skill_brands,
            "service_regions": service_regions,
            "scheduled_visit_count": scheduled_count,
            "reasons": reasons,
            "risks": risks,
        }


def _profile_snapshot(account: dict[str, object], profile: dict[str, object] | None) -> TechnicianProfileSnapshot:
    return TechnicianProfileSnapshot(
        staff_username=str(account["username"]),
        display_name=str(account["display_name"]),
        phone=str(account.get("phone", "")),
        staff_active=bool(account["active"]),
        active=bool(profile["active"]) if profile else True,
        skill_brands=list(profile["skill_brands"]) if profile else [],
        service_regions=list(profile["service_regions"]) if profile else [],
        notes=None if profile is None else profile.get("notes"),  # type: ignore[arg-type]
        created_at=None if profile is None else str(profile["created_at"]),
        updated_at=None if profile is None else str(profile["updated_at"]),
    )


def _contains_casefold(values: list[object], needle: str) -> bool:
    folded = needle.casefold()
    return any(str(value).casefold() == folded for value in values)


def _matched_region(regions: list[object], address: str) -> str | None:
    folded_address = address.casefold()
    for region in regions:
        region_text = str(region).strip()
        if not region_text:
            continue
        folded_region = region_text.casefold()
        if folded_region in folded_address or folded_address in folded_region:
            return region_text
    return None

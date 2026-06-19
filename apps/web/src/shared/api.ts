import type { IntakeFormState, IntakePayload } from "./types";

export function buildServiceRequestPayload(form: IntakeFormState): IntakePayload {
  const payload: IntakePayload = {
    customer: {
      name: form.name.trim(),
      phone: form.phone.trim(),
      client_type: form.clientType,
    },
    machine: {
      brand: form.brand.trim(),
      location_type: form.locationType,
    },
    problem: form.problem.trim(),
    address: form.address.trim(),
    urgency: form.urgency,
  };

  const telegram = form.telegram.trim();
  if (telegram) payload.customer.telegram = telegram;

  const model = form.model.trim();
  if (model) payload.machine.model = model;

  return payload;
}

export function resolveApiBaseUrl(configuredBaseUrl: string | undefined, origin: string | undefined): string {
  if (configuredBaseUrl) return configuredBaseUrl;
  if (origin === "http://localhost:3000") return "http://localhost:8000";
  if (origin === "http://127.0.0.1:3000") return "http://127.0.0.1:8000";
  return "";
}

export function apiBaseUrl(): string {
  return resolveApiBaseUrl(
    import.meta.env.VITE_SERVICEOPS_API_BASE_URL,
    typeof window !== "undefined" ? window.location.origin : undefined,
  );
}

export function normalizeRequestNumber(value: string): string {
  return value.trim().toUpperCase();
}

export function statusPathFromRequestNumber(requestNumber: string): string {
  return `/status/${encodeURIComponent(normalizeRequestNumber(requestNumber))}`;
}

export function buildStatusLookupPath(value: string): string {
  const cleaned = value.trim();
  const normalized = normalizeRequestNumber(cleaned);
  if (/^CFX-\d{8}-\d{6}$/.test(normalized)) {
    return `/service-requests/${encodeURIComponent(normalized)}/status`;
  }
  return `/status/${encodeURIComponent(cleaned)}`;
}

export function statusLookupValueFromPath(pathname: string): string | null {
  const [, route, tokenOrNumber] = pathname.split("/");
  if (route !== "status" || !tokenOrNumber) return null;
  return decodeURIComponent(tokenOrNumber);
}

export function replaceStatusRoute(requestNumber: string): void {
  if (typeof window === "undefined") return;
  const nextPath = statusPathFromRequestNumber(requestNumber);
  if (window.location.pathname !== nextPath) {
    window.history.replaceState(null, "", nextPath);
  }
}

export function replaceStatusLookupRoute(): void {
  if (typeof window === "undefined") return;
  if (window.location.pathname !== "/status") {
    window.history.replaceState(null, "", "/status");
  }
}

export function telegramOptInPathFromRequestNumber(requestNumber: string): string {
  return `/service-requests/${encodeURIComponent(normalizeRequestNumber(requestNumber))}/telegram-opt-in`;
}

export function buildCustomerAnswerPayload(questionId: number, answer: string) {
  return {
    question_id: questionId,
    answer: answer.trim(),
  };
}

export function buildTelegramOptInPayload(telegram: string) {
  const cleaned = telegram.trim();
  return cleaned ? { telegram: cleaned } : { telegram: undefined };
}

export function buildDispatcherListPath(): string {
  return "/dispatcher/service-requests";
}

export function buildDispatcherSchedulePath(): string {
  return "/dispatcher/schedule";
}

export function buildDispatcherTechnicianCandidatesPath(): string {
  return "/dispatcher/technician-candidates";
}

export function buildDispatcherTechnicianRecommendationsPath(
  requestNumber: string,
  startsAt?: string,
  endsAt?: string,
): string {
  const path = `${buildDispatcherDetailPath(requestNumber)}/technician-recommendations`;
  if (!startsAt || !endsAt) return path;
  const params = new URLSearchParams({ starts_at: startsAt, ends_at: endsAt });
  return `${path}?${params.toString()}`;
}

export function buildDispatcherDetailPath(requestNumber: string): string {
  return `/dispatcher/service-requests/${encodeURIComponent(normalizeRequestNumber(requestNumber))}`;
}

export function buildDispatcherStatusPath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/status`;
}

export function buildDispatcherClarificationPath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/clarifications`;
}

export function buildDispatcherAssignmentPath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/assignment`;
}

export function buildDispatcherInternalNotePath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/internal-notes`;
}

export function buildDispatcherAppointmentPath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/appointments`;
}

export function buildDispatcherAppointmentReschedulePath(requestNumber: string, appointmentId: number): string {
  return `${buildDispatcherAppointmentPath(requestNumber)}/${appointmentId}/reschedule`;
}

export function buildDispatcherAppointmentCancelPath(requestNumber: string, appointmentId: number): string {
  return `${buildDispatcherAppointmentPath(requestNumber)}/${appointmentId}/cancel`;
}

export function buildGenerateAiSuggestionsPath(requestNumber: string): string {
  return `${buildDispatcherDetailPath(requestNumber)}/ai-suggestions/generate`;
}

export function buildAcceptAiClarificationPath(requestNumber: string, suggestionId: number): string {
  return `${buildDispatcherDetailPath(requestNumber)}/ai-suggestions/${suggestionId}/accept-clarification`;
}

export function buildIgnoreAiSuggestionPath(requestNumber: string, suggestionId: number): string {
  return `${buildDispatcherDetailPath(requestNumber)}/ai-suggestions/${suggestionId}/ignore`;
}

export function buildTechnicianListPath(): string {
  return "/technician/service-requests";
}

export function buildTechnicianSchedulePath(): string {
  return "/technician/schedule";
}

export function buildTechnicianDetailPath(requestNumber: string): string {
  return `/technician/service-requests/${encodeURIComponent(normalizeRequestNumber(requestNumber))}`;
}

export function buildTechnicianDiagnosisPath(requestNumber: string): string {
  return `${buildTechnicianDetailPath(requestNumber)}/diagnosis`;
}

export function buildTechnicianResultPath(requestNumber: string): string {
  return `${buildTechnicianDetailPath(requestNumber)}/result`;
}

export function buildTechnicianPartsUsedPath(requestNumber: string): string {
  return `${buildTechnicianDetailPath(requestNumber)}/parts-used`;
}

export function buildInventoryPartsPath(): string {
  return "/inventory/parts";
}

export function buildInventoryStockPath(partId: number): string {
  return `/inventory/parts/${partId}/stock`;
}

export function buildInventoryPartCompatibilityPath(partId: number): string {
  return `/inventory/parts/${partId}/compatibility`;
}

export function buildInventoryReservationsPath(): string {
  return "/inventory/reservations";
}

export function buildInventoryReservationReleasePath(reservationId: number): string {
  return `/inventory/reservations/${reservationId}/release`;
}

export function buildInventoryMovementsPath(): string {
  return "/inventory/movements";
}

export function buildInventoryLowStockPath(): string {
  return "/inventory/low-stock";
}

export function buildInventoryProcurementSuppliersPath(): string {
  return "/inventory/procurement/suppliers";
}

export function buildInventoryProcurementPurchaseRequestsPath(): string {
  return "/inventory/procurement/purchase-requests";
}

export function buildInventoryProcurementLowStockDraftPath(): string {
  return "/inventory/procurement/purchase-requests/low-stock-draft";
}

export function buildInventoryProcurementPurchaseRequestItemsPath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/items`;
}

export function buildInventoryProcurementPurchaseRequestSubmitPath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/submit`;
}

export function buildInventoryProcurementPurchaseRequestApprovePath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/approve`;
}

export function buildInventoryProcurementPurchaseRequestMarkOrderedPath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/mark-ordered`;
}

export function buildInventoryProcurementPurchaseRequestReceivePath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/receive`;
}

export function buildInventoryProcurementPurchaseRequestCancelPath(purchaseRequestId: number): string {
  return `/inventory/procurement/purchase-requests/${purchaseRequestId}/cancel`;
}

export function buildOwnerDashboardPath(): string {
  return "/owner/dashboard";
}

export function buildOwnerDailyReportPath(): string {
  return "/owner/daily-report";
}

export function buildAssistantRunsPath(): string {
  return "/assistant/runs";
}

export function buildAssistantConfirmPath(runId: number): string {
  return `/assistant/runs/${runId}/confirm`;
}

export function buildAdminStaffPath(): string {
  return "/admin/staff";
}

export function buildAdminStaffRolesPath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/roles`;
}

export function buildAdminStaffProfilePath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/profile`;
}

export function buildAdminStaffActivatePath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/activate`;
}

export function buildAdminStaffDeactivatePath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/deactivate`;
}

export function buildAdminStaffResetPasswordPath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/reset-password`;
}

export function buildAdminStaffAuditPath(): string {
  return "/admin/staff/audit";
}

export function buildAdminTechnicianProfilesPath(): string {
  return "/admin/technician-profiles";
}

export function buildAdminTechnicianProfilePath(username: string): string {
  return `/admin/technician-profiles/${encodeURIComponent(username)}`;
}

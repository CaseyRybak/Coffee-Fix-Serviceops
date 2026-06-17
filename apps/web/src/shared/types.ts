export type ClientType = "private" | "office" | "coffee_shop" | "restaurant" | "other";
export type LocationType = "home" | "office" | "coffee_shop" | "restaurant" | "other";
export type Urgency = "today" | "one_two_days" | "planned";
export type FormStep = 1 | 2 | 3;

export interface IntakeFormState {
  name: string;
  phone: string;
  telegram: string;
  clientType: ClientType;
  brand: string;
  model: string;
  locationType: LocationType;
  problem: string;
  address: string;
  visitTime: string;
  comment: string;
  urgency: Urgency;
}

export interface IntakePayload {
  customer: {
    name: string;
    phone: string;
    telegram?: string;
    client_type: ClientType;
  };
  machine: {
    brand: string;
    model?: string;
    location_type: LocationType;
  };
  problem: string;
  address: string;
  urgency: Urgency;
}

export type RequestStatus =
  | "new"
  | "needs_clarification"
  | "awaiting_assignment"
  | "technician_assigned"
  | "visit_scheduled"
  | "diagnostics"
  | "waiting_for_parts"
  | "repair_in_progress"
  | "completed"
  | "closed"
  | "warranty_case"
  | "cancelled";

export interface PublicStatusSnapshot {
  request_number: string;
  public_token: string;
  status: RequestStatus;
  customer: {
    name: string;
    phone_masked: string;
    telegram: string | null;
  };
  machine: {
    brand: string;
    model: string | null;
  };
  problem_summary: string;
  timeline: Array<{
    status: RequestStatus;
    title: string;
    description: string;
    actor: string;
    created_at: string;
  }>;
  clarification: {
    question_id: number;
    question: string;
    answer: string | null;
    answered_at: string | null;
  } | null;
  clarification_history?: Array<{
    question_id: number;
    question: string;
    answer: string | null;
    answered_at: string | null;
  }>;
  telegram_opt_in: {
    enabled: boolean;
    link: string;
  };
  appointment?: PublicAppointmentSnapshot | null;
}

export type AppointmentStatus = "scheduled" | "rescheduled" | "cancelled";

export interface PublicAppointmentSnapshot {
  starts_at: string | null;
  ends_at: string | null;
  window_label: string;
  status: AppointmentStatus;
}

export interface AppointmentSnapshot extends PublicAppointmentSnapshot {
  appointment_id: number;
  request_number: string;
  technician_identifier: string;
  technician_name: string;
  reschedule_reason: string | null;
  cancel_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduleListItem {
  appointment: AppointmentSnapshot;
  request_status: RequestStatus;
  customer_name: string;
  machine_label: string;
  urgency: Urgency;
  address: string;
  latest_event_title: string;
}

export interface ScheduleListResponse {
  items: ScheduleListItem[];
}

export interface DispatcherListItem {
  request_number: string;
  status: RequestStatus;
  customer_name: string;
  customer_phone: string;
  machine_label: string;
  urgency: Urgency;
  address: string;
  created_at: string;
  latest_event_title: string;
}

export interface DispatcherListResponse {
  items: DispatcherListItem[];
}

export type DispatcherStatusFilter = "all" | RequestStatus;
export type DispatcherUrgencyFilter = "all" | Urgency;
export type StaffRole = "dispatcher" | "admin" | "technician" | "inventory";

export interface StaffSession {
  accessToken: string;
  username: string;
  roles: StaffRole[];
}

export interface StaffAccountItem {
  username: string;
  display_name: string;
  first_name: string;
  last_name: string;
  phone: string;
  roles: StaffRole[];
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StaffAccountListResponse {
  items: StaffAccountItem[];
}

export interface StaffAuditEvent {
  actor_username: string;
  target_username: string;
  action: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface StaffAuditListResponse {
  items: StaffAuditEvent[];
}

export type SlaState = "on_track" | "near_deadline" | "overdue" | "inactive";

export interface OwnerSlaSnapshot {
  request_number: string;
  state: SlaState;
  deadline_at: string | null;
  hours_remaining: number | null;
  is_overdue: boolean;
  is_near_deadline: boolean;
}

export interface OwnerDashboardMetrics {
  new_requests: number;
  in_progress_requests: number;
  waiting_for_parts_requests: number;
  completed_requests: number;
  overdue_requests: number;
  near_deadline_requests: number;
}

export interface OwnerSlaRiskItem {
  request_number: string;
  status: RequestStatus;
  urgency: Urgency;
  customer_name: string;
  machine_label: string;
  latest_event_title: string;
  sla: OwnerSlaSnapshot;
}

export interface TechnicianWorkloadItem {
  technician_identifier: string;
  active_requests: number;
  scheduled_visits: number;
  waiting_for_parts: number;
}

export interface IssueGroupItem {
  label: string;
  count: number;
}

export interface LowStockRiskItem {
  part_id: number;
  sku: string;
  name: string;
  unit: string;
  available_quantity: number;
  low_stock_threshold: number | null;
}

export interface OwnerDashboardResponse {
  generated_at: string;
  metrics: OwnerDashboardMetrics;
  sla_risks: OwnerSlaRiskItem[];
  technician_workload: TechnicianWorkloadItem[];
  top_issue_groups: IssueGroupItem[];
  low_stock_risk: LowStockRiskItem[];
}

export interface OwnerDailyReportResponse {
  report_date: string;
  generated_at: string;
  summary: OwnerDashboardMetrics;
  highlights: string[];
  sla_risks: OwnerSlaRiskItem[];
  low_stock_risk: LowStockRiskItem[];
  dashboard_url: string;
}

export interface TechnicianCandidate {
  username: string;
  display_name: string;
  phone: string;
}

export interface TechnicianCandidateListResponse {
  items: TechnicianCandidate[];
}

export interface DispatcherRequestDetail {
  request_number: string;
  status: RequestStatus;
  customer: {
    name: string;
    phone: string;
    telegram: string | null;
    client_type: ClientType;
  };
  machine: {
    brand: string;
    model: string | null;
    location_type: LocationType;
  };
  problem: string;
  address: string;
  urgency: Urgency;
  created_at: string;
  timeline: PublicStatusSnapshot["timeline"];
  clarification: PublicStatusSnapshot["clarification"];
  clarification_history?: NonNullable<PublicStatusSnapshot["clarification"]>[];
  assignment: {
    technician_name: string | null;
    technician_phone: string | null;
    technician_region: string | null;
    visit_window: string | null;
  };
  appointment?: AppointmentSnapshot | null;
  internal_notes: Array<{
    note: string;
    actor: string;
    created_at: string;
  }>;
  ai_suggestions?: DispatcherAiSuggestion[];
  notification_deliveries?: DispatcherNotificationDelivery[];
}

export interface DispatcherNotificationDelivery {
  event_id: string;
  event_type: string;
  status: string;
  channel: string | null;
  provider_message_id: string | null;
  error: string | null;
  attempt_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export type AiSuggestionKind =
  | "intake_classification"
  | "diagnostic_question"
  | "likely_cause"
  | "parts"
  | "customer_reply";
export type AiSuggestionStatus = "pending" | "accepted" | "ignored";

export interface DispatcherAiSuggestion {
  suggestion_id: number;
  kind: AiSuggestionKind;
  title: string;
  content: string;
  rationale: string;
  confidence: number;
  status: AiSuggestionStatus;
  source_chunks: Array<{
    document_title: string;
    source_uri: string | null;
    chunk_id: number;
    score: number;
  }>;
  created_at: string;
  acted_at: string | null;
}

export interface TechnicianListItem {
  request_number: string;
  status: RequestStatus;
  customer_name: string;
  machine_label: string;
  urgency: Urgency;
  address: string;
  visit_window: string | null;
  appointment?: PublicAppointmentSnapshot | null;
  latest_event_title: string;
}

export interface TechnicianListResponse {
  items: TechnicianListItem[];
}

export interface TechnicianRequestDetail {
  request_number: string;
  status: RequestStatus;
  customer_name: string;
  customer_phone: string;
  machine_label: string;
  problem: string;
  address: string;
  urgency: Urgency;
  visit_window: string | null;
  appointment?: PublicAppointmentSnapshot | null;
  diagnosis: {
    machine_powered_on: boolean;
    water_supply_checked: boolean;
    leak_checked: boolean;
    error_code_checked: boolean;
    summary: string;
    actor: string;
    created_at: string;
  } | null;
  repair_result: {
    result: "completed" | "waiting_for_parts" | "follow_up_required";
    summary: string;
    next_step: string | null;
    actor: string;
    created_at: string;
  } | null;
}

export type InventoryCompatibilityLevel = "exact_model" | "series" | "generic_group";

export interface InventoryCompatibility {
  compatibility_id: number;
  part_id: number;
  compatibility_level: InventoryCompatibilityLevel;
  brand: string | null;
  model: string | null;
  series: string | null;
  machine_family: string | null;
  note: string | null;
  created_at: string;
}

export interface InventoryPartItem {
  part_id: number;
  sku: string;
  name: string;
  brand: string | null;
  model: string | null;
  unit: string;
  compatibility_note: string | null;
  part_type: string | null;
  parameter_label: string | null;
  parameter_value: string | null;
  parameter_unit: string | null;
  factual_key: string | null;
  compatibility: InventoryCompatibility[];
  created_at: string;
  quantity_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
  low_stock_threshold: number | null;
  is_low_stock: boolean;
  stock_updated_at: string | null;
}

export interface InventoryPartListResponse {
  items: InventoryPartItem[];
}

export interface InventoryReservation {
  reservation_id: number;
  request_number: string;
  appointment_id: number | null;
  part_id: number;
  sku: string;
  part_name: string;
  quantity: number;
  status: "active" | "released" | "consumed";
  note: string | null;
  actor: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryReservationListResponse {
  items: InventoryReservation[];
}

export interface InventoryMovement {
  movement_id: number;
  part_id: number;
  sku: string;
  part_name: string;
  movement_type: "manual_adjustment" | "reservation_created" | "reservation_adjusted" | "release" | "consumption";
  quantity: number;
  quantity_on_hand_after: number;
  reserved_quantity_after: number;
  available_quantity_after: number;
  request_number: string | null;
  reservation_id: number | null;
  note: string | null;
  actor: string;
  created_at: string;
}

export interface InventoryMovementListResponse {
  items: InventoryMovement[];
}

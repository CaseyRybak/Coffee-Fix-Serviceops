import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  ArrowRight,
  Brush,
  Building2,
  Car,
  CheckCircle2,
  CheckSquare,
  ChevronRight,
  ClipboardList,
  Clock,
  Coffee,
  Cog,
  CupSoda,
  Droplets,
  ExternalLink,
  Eye,
  HelpCircle,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Menu,
  MessageCircle,
  Monitor,
  Package,
  Phone,
  PhoneCall,
  Power,
  Send,
  Shield,
  Thermometer,
  Wrench,
  X,
} from "lucide-react";

type ClientType = "private" | "office" | "coffee_shop" | "restaurant" | "other";
type LocationType = "home" | "office" | "coffee_shop" | "restaurant" | "other";
type Urgency = "today" | "one_two_days" | "planned";
type FormStep = 1 | 2 | 3;

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
  attachmentFilename: string;
  attachmentContentType: string;
  attachmentSizeBytes: string;
}

interface IntakePayload {
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
  attachment_metadata?: Array<{
    filename: string;
    content_type: string;
    size_bytes: number;
  }>;
}

type RequestStatus =
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

interface PublicStatusSnapshot {
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
  telegram_opt_in: {
    enabled: boolean;
    link: string;
  };
}

interface DispatcherListItem {
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

interface DispatcherListResponse {
  items: DispatcherListItem[];
}

type DispatcherStatusFilter = "all" | RequestStatus;
type DispatcherUrgencyFilter = "all" | Urgency;
type StaffRole = "dispatcher" | "admin" | "technician" | "inventory";

interface StaffSession {
  accessToken: string;
  username: string;
  roles: StaffRole[];
}

interface StaffAccountItem {
  username: string;
  display_name: string;
  roles: StaffRole[];
  active: boolean;
  created_at: string;
  updated_at: string;
}

interface StaffAccountListResponse {
  items: StaffAccountItem[];
}

interface StaffAuditEvent {
  actor_username: string;
  target_username: string;
  action: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

interface StaffAuditListResponse {
  items: StaffAuditEvent[];
}

interface DispatcherRequestDetail {
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
  assignment: {
    technician_name: string | null;
    technician_phone: string | null;
    technician_region: string | null;
    visit_window: string | null;
  };
  internal_notes: Array<{
    note: string;
    actor: string;
    created_at: string;
  }>;
  ai_suggestions?: DispatcherAiSuggestion[];
  notification_deliveries?: DispatcherNotificationDelivery[];
}

interface DispatcherNotificationDelivery {
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

type AiSuggestionKind =
  | "intake_classification"
  | "diagnostic_question"
  | "likely_cause"
  | "parts"
  | "customer_reply";
type AiSuggestionStatus = "pending" | "accepted" | "ignored";

interface DispatcherAiSuggestion {
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

interface TechnicianListItem {
  request_number: string;
  status: RequestStatus;
  customer_name: string;
  machine_label: string;
  urgency: Urgency;
  address: string;
  visit_window: string | null;
  latest_event_title: string;
}

interface TechnicianListResponse {
  items: TechnicianListItem[];
}

interface TechnicianRequestDetail {
  request_number: string;
  status: RequestStatus;
  customer_name: string;
  customer_phone: string;
  machine_label: string;
  problem: string;
  address: string;
  urgency: Urgency;
  visit_window: string | null;
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

interface InventoryPartItem {
  part_id: number;
  sku: string;
  name: string;
  brand: string | null;
  model: string | null;
  unit: string;
  compatibility_note: string | null;
  created_at: string;
  quantity_on_hand: number;
  stock_updated_at: string | null;
}

interface InventoryPartListResponse {
  items: InventoryPartItem[];
}

const initialForm: IntakeFormState = {
  name: "",
  phone: "",
  telegram: "",
  clientType: "private",
  brand: "",
  model: "",
  locationType: "home",
  problem: "",
  address: "",
  visitTime: "",
  comment: "",
  urgency: "one_two_days",
  attachmentFilename: "",
  attachmentContentType: "",
  attachmentSizeBytes: "",
};

const navLinks = [
  { label: "Услуги", href: "#services" },
  { label: "Бренды", href: "#brands" },
  { label: "Как работаем", href: "#how-it-works" },
  { label: "Гарантия", href: "#trust" },
  { label: "Статус заявки", href: "/status" },
  { label: "Контакты", href: "#footer" },
];

const clientTypes: Array<{ value: ClientType; label: string }> = [
  { value: "private", label: "Частный клиент" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

const locations: Array<{ value: LocationType; label: string }> = [
  { value: "home", label: "Дом" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

const urgencies: Array<{ value: Urgency; label: string }> = [
  { value: "today", label: "Сегодня" },
  { value: "one_two_days", label: "В ближайшие 1-2 дня" },
  { value: "planned", label: "Плановое обслуживание" },
];

const brands = [
  "Jura",
  "Saeco",
  "DeLonghi",
  "Philips",
  "Bosch",
  "Nivona",
  "WMF",
  "Nuova Simonelli",
  "La Cimbali",
  "Rancilio",
  "Melitta",
  "Miele",
];

const machineTypes = [
  "Домашние автоматические",
  "Профессиональные",
  "Офисные",
  "Кофемашины для кофеен",
  "Встраиваемые",
  "Капсульные",
];

const issues = [
  { icon: Cog, title: "Не мелет кофе", desc: "Засор жерновов или проблема с кофемолкой" },
  { icon: Droplets, title: "Течет вода", desc: "Повреждение уплотнителей или трубок подачи воды" },
  { icon: Power, title: "Не включается", desc: "Неисправность платы управления или питания" },
  { icon: Monitor, title: "Ошибка на дисплее", desc: "Диагностика кода ошибки и устранение причины" },
  { icon: Thermometer, title: "Не греет воду", desc: "Вышел из строя нагревательный элемент или термоблок" },
  { icon: Coffee, title: "Не взбивает молоко", desc: "Засор или износ капучинатора / паровой трубки" },
  { icon: CupSoda, title: "Не подает кофе", desc: "Засор заварочного устройства или группы" },
  { icon: Brush, title: "Чистка и декальцинация", desc: "Плановое обслуживание и удаление накипи" },
];

const repairSteps = [
  {
    icon: ClipboardList,
    title: "Оставляете заявку",
    desc: "Заполните короткую форму на сайте или позвоните. Укажите бренд, симптомы и удобное время.",
  },
  {
    icon: PhoneCall,
    title: "Диспетчер уточняет симптомы",
    desc: "Специалист свяжется с вами, уточнит детали неисправности и согласует время визита мастера.",
  },
  {
    icon: Wrench,
    title: "Мастер приезжает и проводит диагностику",
    desc: "Выездной мастер осматривает кофемашину, диагностирует причину и определяет объем работ.",
  },
  {
    icon: CheckSquare,
    title: "Согласуем стоимость и выполняем ремонт",
    desc: "После согласования стоимости выполняем ремонт. Большинство поломок устраняется за один выезд.",
  },
];

const trustCards = [
  {
    icon: Shield,
    title: "Гарантия на выполненные работы",
    desc: "До 6 месяцев на ремонт и установленные запчасти. Письменная гарантия по каждому обращению.",
    tone: "green",
  },
  {
    icon: Car,
    title: "Выезд на дом, в офис и кофейни",
    desc: "Работаем по Москве и Московской области. Выезд в день обращения при наличии свободных мастеров.",
    tone: "brown",
  },
  {
    icon: Package,
    title: "Запчасти и расходники в наличии",
    desc: "Собственный склад оригинальных и совместимых запчастей для популярных брендов.",
    tone: "brown",
  },
  {
    icon: Building2,
    title: "Работаем с физ. и юрлицами",
    desc: "Договор и закрывающие документы для бухгалтерии. Безналичная оплата для организаций.",
    tone: "brown",
  },
  {
    icon: Eye,
    title: "Статус заявки онлайн",
    desc: "Отслеживайте этапы ремонта по ссылке - без личного кабинета и регистрации.",
    tone: "green",
  },
  {
    icon: MessageCircle,
    title: "Уведомления в Telegram",
    desc: "Получайте обновления по статусу заявки прямо в мессенджер - по желанию клиента.",
    tone: "green",
  },
];

const nextSteps = [
  "Проверим описание и симптомы",
  "Зададим уточняющие вопросы, если нужно",
  "Подберем мастера и проверим запчасти",
  "Согласуем время визита",
];

const footerServices = [
  "Ремонт кофемашин",
  "Диагностика",
  "Плановое обслуживание",
  "Декальцинация",
  "Замена запчастей",
  "Настройка помола",
];

const footerBrands = ["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli"];
const footerClientLinks = [
  { label: "Оставить заявку", href: "/#request-form" },
  { label: "Отследить статус", href: "/status" },
  { label: "Telegram-уведомления", href: "/status" },
  { label: "Гарантийные условия", href: "#trust" },
  { label: "Оплата и документы", href: "#trust" },
];

const technicianCandidates = [
  {
    name: "Sergey Morozov",
    phone: "+7 999 310-22-11",
    region: "ЦАО",
    skills: "Jura, Saeco",
  },
  {
    name: "Pavel Sokolov",
    phone: "+7 999 222-33-44",
    region: "СЗАО",
    skills: "DeLonghi, Philips",
  },
  {
    name: "Marina Volkova",
    phone: "+7 999 450-18-07",
    region: "ЮЗАО",
    skills: "WMF, Nuova Simonelli",
  },
];

const staffSessionStorageKey = "serviceops.staffSession";

export function getNextFormStep(step: FormStep): FormStep {
  return step < 3 ? ((step + 1) as FormStep) : 3;
}

export function validateIntakeStep(form: IntakeFormState, step: FormStep): string[] {
  if (step === 1) {
    return [
      [form.name, "Имя"],
      [form.phone, "Телефон"],
    ]
      .filter(([value]) => !String(value).trim())
      .map(([, label]) => String(label));
  }

  if (step === 2) {
    return [
      [form.brand, "Бренд кофемашины"],
      [form.problem, "Комментарий"],
    ]
      .filter(([value]) => !String(value).trim())
      .map(([, label]) => String(label));
  }

  return form.address.trim() ? [] : ["Район или адрес"];
}

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

  const filename = form.attachmentFilename.trim();
  const contentType = form.attachmentContentType.trim();
  const sizeBytes = Number(form.attachmentSizeBytes);
  if (filename && contentType && Number.isFinite(sizeBytes) && sizeBytes > 0) {
    payload.attachment_metadata = [{ filename, content_type: contentType, size_bytes: sizeBytes }];
  }

  return payload;
}

export function resolveApiBaseUrl(configuredBaseUrl: string | undefined, origin: string | undefined): string {
  if (configuredBaseUrl) return configuredBaseUrl;
  if (origin === "http://localhost:3000") return "http://localhost:8000";
  if (origin === "http://127.0.0.1:3000") return "http://127.0.0.1:8000";
  return "";
}

function apiBaseUrl(): string {
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

export function buildAdminStaffPath(): string {
  return "/admin/staff";
}

export function buildAdminStaffRolesPath(username: string): string {
  return `/admin/staff/${encodeURIComponent(username)}/roles`;
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

export function buildStaffLoginPath(nextPath = "/dispatcher"): string {
  return `/staff/login?next=${encodeURIComponent(nextPath)}`;
}

export function getStoredStaffSession(storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): StaffSession | null {
  if (!storage) return null;
  const raw = storage.getItem(staffSessionStorageKey);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<StaffSession>;
    if (!parsed.accessToken || !parsed.username || !Array.isArray(parsed.roles)) return null;
    return {
      accessToken: parsed.accessToken,
      username: parsed.username,
      roles: parsed.roles.filter((role): role is StaffRole =>
        ["dispatcher", "admin", "technician", "inventory"].includes(String(role)),
      ),
    };
  } catch {
    return null;
  }
}

export function storeStaffSession(session: StaffSession, storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): void {
  storage?.setItem(staffSessionStorageKey, JSON.stringify(session));
}

export function clearStaffSession(storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): void {
  storage?.removeItem(staffSessionStorageKey);
}

export function staffAuthHeaders(session: StaffSession | null = getStoredStaffSession()): Record<string, string> {
  return session ? { Authorization: `Bearer ${session.accessToken}` } : {};
}

export function staffHasRole(session: StaffSession | null, role: StaffRole): boolean {
  return Boolean(session?.roles.includes(role));
}

export function resolveStaffLandingPath(staff: { roles: StaffRole[]; username?: string }, requestedNext: string | null): string {
  const routeRoles: Array<{ prefix: string; role: StaffRole }> = [
    { prefix: "/dispatcher", role: "dispatcher" },
    { prefix: "/technician", role: "technician" },
    { prefix: "/inventory", role: "inventory" },
    { prefix: "/admin", role: "admin" },
  ];
  const safeNext = requestedNext?.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : null;
  const matchingRoute = safeNext ? routeRoles.find((route) => safeNext.startsWith(route.prefix)) : undefined;
  if (safeNext && matchingRoute && staff.roles.includes(matchingRoute.role)) return safeNext;
  if (staff.roles.includes("dispatcher")) return "/dispatcher";
  if (staff.roles.includes("technician")) return "/technician";
  if (staff.roles.includes("inventory")) return "/inventory";
  if (staff.roles.includes("admin")) return "/admin";
  return "/staff/login";
}

export function filterDispatcherItems(
  items: DispatcherListItem[],
  statusFilter: DispatcherStatusFilter,
  urgencyFilter: DispatcherUrgencyFilter,
): DispatcherListItem[] {
  return items.filter((item) => {
    const statusMatches = statusFilter === "all" || item.status === statusFilter;
    const urgencyMatches = urgencyFilter === "all" || item.urgency === urgencyFilter;
    return statusMatches && urgencyMatches;
  });
}

function statusLabel(status: RequestStatus): string {
  const labels: Record<RequestStatus, string> = {
    new: "Новая заявка",
    needs_clarification: "Ждет уточнения",
    awaiting_assignment: "Ждет назначения мастера",
    technician_assigned: "Мастер назначен",
    visit_scheduled: "Визит запланирован",
    diagnostics: "Диагностика",
    waiting_for_parts: "Ожидаем запчасти",
    repair_in_progress: "Ремонт в работе",
    completed: "Ремонт завершен",
    closed: "Заявка закрыта",
    warranty_case: "Гарантийный случай",
    cancelled: "Заявка отменена",
  };
  return labels[status];
}

function urgencyLabel(urgency: Urgency): string {
  const labels: Record<Urgency, string> = {
    today: "Сегодня",
    one_two_days: "1-2 дня",
    planned: "Планово",
  };
  return labels[urgency];
}

export function formatCompactDateTime(value: string | null | undefined): string {
  if (!value) return "не указано";
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatCompactDate(value: string | null | undefined): string {
  if (!value) return "не указано";
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  }).format(date);
}

function aiSuggestionKindLabel(kind: AiSuggestionKind): string {
  const labels: Record<AiSuggestionKind, string> = {
    intake_classification: "Классификация",
    diagnostic_question: "Вопрос",
    likely_cause: "Причина",
    parts: "Запчасти",
    customer_reply: "Ответ клиенту",
  };
  return labels[kind];
}

function aiSuggestionStatusLabel(status: AiSuggestionStatus): string {
  const labels: Record<AiSuggestionStatus, string> = {
    pending: "На проверке",
    accepted: "Принято",
    ignored: "Игнорировано",
  };
  return labels[status];
}

function Field({
  label,
  optional,
  children,
}: {
  label: string;
  optional?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="form-field">
      <span className="field-label">
        {label}
        {optional ? <em> - необязательно</em> : null}
      </span>
      {children}
    </label>
  );
}

function ChipGroup<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}) {
  return (
    <div className="chip-row">
      {options.map((option) => (
        <button
          className={value === option.value ? "chip selected" : "chip"}
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function Logo() {
  return (
    <a className="brand" href="/" aria-label="CoffeeFix Pro">
      <span className="brand-mark">
        <Coffee aria-hidden="true" />
      </span>
      <span className="brand-copy">
        <strong>CoffeeFix Pro</strong>
        <small>ремонт и обслуживание кофемашин</small>
      </span>
    </a>
  );
}

function ServiceBar() {
  return (
    <div className="service-bar" aria-label="Сервисная информация">
      <div className="service-bar-inner">
        <div className="service-bar-left">
          <span>
            <MapPin aria-hidden="true" />
            Москва и МО
          </span>
          <span>
            <Clock aria-hidden="true" />
            Пн-Вс 08:00-22:00
          </span>
          <span className="desktop-service-note">
            <Car aria-hidden="true" />
            Выезд мастера на дом, в офис и кофейни
          </span>
        </div>
        <div className="service-bar-right">
          <a href="tel:+74950000000">
            <Phone aria-hidden="true" />
            +7 (495) 000-00-00
          </a>
          <a className="service-mini-cta" href="/#request-form">
            Вызвать мастера
          </a>
        </div>
      </div>
    </div>
  );
}

function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Logo />
        <nav className="desktop-nav" aria-label="Основная навигация">
          {navLinks.map((link) => (
            <a href={link.href} key={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="header-actions">
          <a className="header-cta" href="/#request-form">
            Оставить заявку
          </a>
          <button className="menu-button" type="button" aria-label="Меню" onClick={() => setMobileOpen((open) => !open)}>
            {mobileOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          </button>
        </div>
      </div>

      {mobileOpen ? (
        <nav className="mobile-nav" aria-label="Мобильная навигация">
          {navLinks.map((link) => (
            <a href={link.href} key={link.href} onClick={() => setMobileOpen(false)}>
              {link.label}
            </a>
          ))}
          <a className="mobile-nav-cta" href="/#request-form" onClick={() => setMobileOpen(false)}>
            Оставить заявку
          </a>
        </nav>
      ) : null}
    </header>
  );
}

function WorkspaceHeader({ session, onLogout }: { session?: StaffSession | null; onLogout?: () => void }) {
  return (
    <header className="workspace-header">
      <div className="site-header-inner workspace-header-inner">
        <Logo />
        <div className="workspace-session-actions">
          {session ? <span>{session.username}</span> : <span className="workspace-header-label">Рабочий кабинет</span>}
          {onLogout ? (
            <button type="button" onClick={onLogout} aria-label="Выйти">
              <LogOut aria-hidden="true" />
              Выйти
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="hero-section" id="top">
      <div className="section-inner hero-inner">
        <div className="hero-copy">
          <h1>
            Ремонт кофемашин
            <br />с выездом мастера
          </h1>
          <p>
            Диагностика, ремонт и обслуживание домашних, офисных и профессиональных кофемашин. Уточним симптомы,
            проверим наличие запчастей и согласуем удобное время визита.
          </p>
          <div className="hero-badges">
            {[
              "Выезд в день обращения",
              "Гарантия до 6 месяцев",
              "Запчасти в наличии",
              "Статус заявки онлайн",
              "Без предоплаты",
              "Для юрлиц",
            ].map((badge) => (
              <span key={badge}>
                <CheckCircle2 aria-hidden="true" />
                {badge}
              </span>
            ))}
          </div>
          <div className="hero-actions">
            <a className="primary-cta" href="/#request-form">
              Оставить заявку на ремонт
              <ArrowRight aria-hidden="true" />
            </a>
            <a className="secondary-cta" href="/status">
              Проверить статус заявки
            </a>
          </div>
          <p className="hero-footnote">После отправки заявки вы получите номер обращения и ссылку для отслеживания статуса.</p>
        </div>
        <div className="hero-media">
          <img
            src="/assets/hero-coffee-service-wide.png"
            alt="Профессиональная кофемашина на сервисном столе"
          />
        </div>
      </div>
    </section>
  );
}

export function SuccessState({ requestNumber, onCreateNew }: { requestNumber: string; onCreateNew?: () => void }) {
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [telegramMessage, setTelegramMessage] = useState<string | null>(null);

  async function connectTelegram() {
    setTelegramLoading(true);
    setTelegramMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${telegramOptInPathFromRequestNumber(requestNumber)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildTelegramOptInPayload("")),
      });
      if (!response.ok) throw new Error(`Telegram opt-in failed with ${response.status}`);
      const body = (await response.json()) as { link: string };
      setTelegramLink(body.link);
      window.open(body.link, "_blank", "noopener,noreferrer");
      setTelegramMessage("Откройте Telegram и нажмите Start у бота, чтобы завершить подключение.");
    } catch {
      setTelegramMessage("Не удалось подготовить Telegram-подключение. Откройте страницу статуса и попробуйте еще раз.");
    } finally {
      setTelegramLoading(false);
    }
  }

  return (
    <section className="request-card success-card" aria-live="polite">
      <div className="success-title">
        <CheckCircle2 aria-hidden="true" />
        <h2>Заявка {requestNumber} создана</h2>
      </div>
      <p>Мы получили обращение. Диспетчер проверит описание, уточнит симптомы и предложит ближайшее время визита.</p>
      <div className="success-actions">
        <a href={statusPathFromRequestNumber(requestNumber)}>
          <ExternalLink aria-hidden="true" />
          Открыть страницу статуса
        </a>
        <button className="ghost-action" type="button" onClick={connectTelegram} disabled={telegramLoading}>
          <MessageCircle aria-hidden="true" />
          {telegramLoading ? "Готовим Telegram" : "Подключить Telegram-уведомления"}
        </button>
        <button className="ghost-action" type="button" onClick={onCreateNew}>
          <ClipboardList aria-hidden="true" />
          Создать новую заявку
        </button>
      </div>
      {telegramMessage ? <p className="success-note">{telegramMessage}</p> : null}
      {telegramLink ? (
        <a className="status-link" href={telegramLink} target="_blank" rel="noreferrer">
          Открыть Telegram-бота
        </a>
      ) : null}
      <div className="next-steps">
        <p>Что дальше?</p>
        {nextSteps.map((step, index) => (
          <div className="next-step" key={step}>
            <span>{index + 1}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export function StatusPage({ initialStatus }: { initialStatus?: PublicStatusSnapshot }) {
  const [lookup, setLookup] = useState(initialStatus?.request_number ?? "");
  const [status, setStatus] = useState<PublicStatusSnapshot | null>(initialStatus ?? null);
  const [changingRequest, setChangingRequest] = useState(!initialStatus);
  const [answer, setAnswer] = useState("");
  const [telegram, setTelegram] = useState(initialStatus?.customer.telegram ?? "");
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function loadStatus(value: string) {
    const cleaned = value.trim();
    if (!cleaned) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildStatusLookupPath(cleaned)}`);
      if (!response.ok) throw new Error(`Status request failed with ${response.status}`);
      const body = (await response.json()) as PublicStatusSnapshot;
      setStatus(body);
      setLookup(body.request_number);
      setTelegram(body.customer.telegram ?? "");
      setChangingRequest(false);
    } catch {
      setMessage("Не удалось открыть статус. Проверьте номер заявки и попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialStatus) return;
    if (typeof window === "undefined") return;
    const [, route, tokenOrNumber] = window.location.pathname.split("/");
    if (route === "status" && tokenOrNumber) {
      const decoded = decodeURIComponent(tokenOrNumber);
      setLookup(decoded);
      void loadStatus(decoded);
    }
  }, [initialStatus]);

  async function handleLookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadStatus(lookup);
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!status?.clarification) return;
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}/service-requests/${status.request_number}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildCustomerAnswerPayload(status.clarification.question_id, answer)),
      });
      if (!response.ok) throw new Error(`Answer request failed with ${response.status}`);
      setAnswer("");
      await loadStatus(status.request_number);
      setMessage("Ответ сохранен. Диспетчер увидит его в заявке.");
    } catch {
      setMessage("Не удалось отправить ответ. Попробуйте еще раз.");
    }
  }

  async function requestTelegramOptIn() {
    if (!status) return;
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${telegramOptInPathFromRequestNumber(status.request_number)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildTelegramOptInPayload(telegram)),
      });
      if (!response.ok) throw new Error(`Telegram opt-in failed with ${response.status}`);
      const body = (await response.json()) as { link: string };
      setTelegramLink(body.link);
      window.open(body.link, "_blank", "noopener,noreferrer");
      setMessage("Откройте Telegram и нажмите Start у бота, чтобы завершить подключение.");
    } catch {
      setMessage("Не удалось подготовить Telegram-подключение. Попробуйте позже.");
    }
  }

  return (
    <div className="app-page status-page">
      <ServiceBar />
      <Header />
      <main className="status-main">
        <section className="section-inner status-workspace">
          {status && !changingRequest ? (
            <div className="status-lookup compact-status-header">
              <div>
                <span>Страница статуса</span>
                <h1>Статус заявки {status.request_number}</h1>
                <p>Ниже показаны текущий этап, история заявки и доступные действия.</p>
              </div>
              <button
                className="secondary-status-button"
                type="button"
                onClick={() => {
                  setLookup("");
                  setChangingRequest(true);
                }}
              >
                Проверить другую заявку
              </button>
            </div>
          ) : (
            <form className="status-lookup" onSubmit={handleLookup}>
              <div>
                <span>Страница статуса</span>
                <h1>{status ? "Проверить другую заявку" : "Проверьте статус заявки"}</h1>
                <p>Введите номер обращения из SMS, звонка диспетчера или письма после отправки заявки.</p>
              </div>
              <div className="status-lookup-controls">
                <input
                  aria-label="Номер заявки"
                  value={lookup}
                  onChange={(event) => setLookup(event.target.value)}
                  placeholder="CFX-20260605-000001"
                />
                <button className="submit-button" type="submit" disabled={loading}>
                  {loading ? "Проверяем" : "Показать статус"}
                </button>
              </div>
            </form>
          )}

          {message ? <p className="status-message">{message}</p> : null}

          {status ? (
            <div className="status-dashboard">
              <section className="status-summary">
                <div>
                  <span className="status-pill">{statusLabel(status.status)}</span>
                  <h2>{status.customer.name}</h2>
                  <p>{status.customer.phone_masked}</p>
                </div>
                <div>
                  <span>Кофемашина</span>
                  <strong>
                    {status.machine.brand}
                    {status.machine.model ? ` ${status.machine.model}` : ""}
                  </strong>
                  <p>{status.problem_summary}</p>
                </div>
              </section>

              <section className="status-panel">
                <div className="status-panel-heading">
                  <Clock aria-hidden="true" />
                  <h2>История заявки</h2>
                </div>
                <div className="timeline">
                  {status.timeline.map((event) => (
                    <article className="timeline-item" key={`${event.title}-${event.created_at}`}>
                      <span />
                      <div>
                        <small>{statusLabel(event.status)}</small>
                        <h3>{event.title}</h3>
                        <p>{event.description}</p>
                        <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                      </div>
                    </article>
                  ))}
                </div>
              </section>

              <section className="status-panel clarification-panel">
                <div className="status-panel-heading">
                  <HelpCircle aria-hidden="true" />
                  <h2>Вопрос диспетчера</h2>
                </div>
                {status.clarification ? (
                  <>
                    <p>{status.clarification.question}</p>
                    {status.clarification.answer ? (
                      <div className="saved-answer">
                        <span>Ваш ответ</span>
                        <strong>{status.clarification.answer}</strong>
                      </div>
                    ) : (
                      <form className="status-answer-form" onSubmit={submitAnswer}>
                        <textarea
                          value={answer}
                          onChange={(event) => setAnswer(event.target.value)}
                          placeholder="Напишите ответ для диспетчера"
                          required
                          rows={3}
                        />
                        <button className="submit-button" type="submit">
                          <Send aria-hidden="true" />
                          Отправить ответ
                        </button>
                      </form>
                    )}
                  </>
                ) : (
                  <p>Сейчас нет открытых уточняющих вопросов.</p>
                )}
              </section>

              <section className="status-panel telegram-panel">
                <div className="status-panel-heading">
                  <MessageCircle aria-hidden="true" />
                  <h2>Telegram-уведомления</h2>
                </div>
                <p>Можно подключить уведомления по этой заявке без личного кабинета.</p>
                <div className="telegram-controls">
                  <input value={telegram ?? ""} onChange={(event) => setTelegram(event.target.value)} placeholder="@username" />
                  <button className="submit-button" type="button" onClick={requestTelegramOptIn}>
                    Подключить Telegram
                  </button>
                </div>
                {telegramLink ? (
                  <a className="status-link" href={telegramLink} target="_blank" rel="noreferrer">
                    Открыть Telegram-бота
                  </a>
                ) : null}
              </section>
            </div>
          ) : null}
        </section>
      </main>
      <Footer />
    </div>
  );
}

export function DispatcherPage({
  initialList,
  initialDetail,
  session,
  onLogout,
}: {
  initialList?: DispatcherListResponse;
  initialDetail?: DispatcherRequestDetail;
  session?: StaffSession | null;
  onLogout?: () => void;
}) {
  const [list, setList] = useState<DispatcherListResponse>(initialList ?? { items: [] });
  const [selected, setSelected] = useState(initialDetail?.request_number ?? initialList?.items[0]?.request_number ?? "");
  const [detail, setDetail] = useState<DispatcherRequestDetail | null>(initialDetail ?? null);
  const [statusValue, setStatusValue] = useState<RequestStatus>("awaiting_assignment");
  const [statusTitle, setStatusTitle] = useState("Готово к назначению");
  const [statusDescription, setStatusDescription] = useState("Описание проверено диспетчером.");
  const [question, setQuestion] = useState("");
  const [technicianName, setTechnicianName] = useState("");
  const [technicianPhone, setTechnicianPhone] = useState("");
  const [technicianRegion, setTechnicianRegion] = useState("");
  const [visitWindow, setVisitWindow] = useState("");
  const [internalNote, setInternalNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<DispatcherStatusFilter>("all");
  const [urgencyFilter, setUrgencyFilter] = useState<DispatcherUrgencyFilter>("all");
  const filteredItems = filterDispatcherItems(list.items, statusFilter, urgencyFilter);

  async function loadList() {
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherListPath()}`, {
      headers: staffAuthHeaders(session),
    });
    if (!response.ok) throw new Error(`Dispatcher list failed with ${response.status}`);
    const body = (await response.json()) as DispatcherListResponse;
    setList(body);
    if (!selected && body.items[0]) setSelected(body.items[0].request_number);
    return body;
  }

  async function loadDetail(requestNumber: string) {
    if (!requestNumber) return;
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherDetailPath(requestNumber)}`, {
      headers: staffAuthHeaders(session),
    });
    if (!response.ok) throw new Error(`Dispatcher detail failed with ${response.status}`);
    const body = (await response.json()) as DispatcherRequestDetail;
    setDetail(body);
    setSelected(body.request_number);
  }

  async function refresh(requestNumber = selected) {
    setLoading(true);
    setMessage(null);
    try {
      await loadList();
      if (requestNumber) await loadDetail(requestNumber);
    } catch {
      setMessage("Не удалось обновить диспетчерские данные.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialList || initialDetail) return;
    void refresh();
  }, [initialList, initialDetail]);

  useEffect(() => {
    if (!selected || selected === detail?.request_number) return;
    void loadDetail(selected).catch(() => setMessage("Не удалось открыть заявку."));
  }, [selected, detail?.request_number]);

  async function postAction(path: string, body: object, afterSuccess: () => void, successMessage: string) {
    if (!detail) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`Dispatcher action failed with ${response.status}`);
      afterSuccess();
      await refresh(detail.request_number);
      setMessage(successMessage);
    } catch {
      setMessage("Не удалось сохранить действие диспетчера.");
    } finally {
      setLoading(false);
    }
  }

  async function submitStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postAction(
      buildDispatcherStatusPath(detail.request_number),
      { status: statusValue, title: statusTitle.trim(), description: statusDescription.trim() },
      () => undefined,
      "Статус обновлен.",
    );
  }

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postAction(
      buildDispatcherClarificationPath(detail.request_number),
      { question: question.trim() },
      () => setQuestion(""),
      "Вопрос клиенту сохранен.",
    );
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postAction(
      buildDispatcherAssignmentPath(detail.request_number),
      {
        technician_name: technicianName.trim(),
        technician_phone: technicianPhone.trim() || undefined,
        technician_region: technicianRegion.trim() || undefined,
        visit_window: visitWindow.trim() || undefined,
      },
      () => {
        setTechnicianName("");
        setTechnicianPhone("");
        setTechnicianRegion("");
        setVisitWindow("");
      },
      "Назначение сохранено.",
    );
  }

  async function submitInternalNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postAction(
      buildDispatcherInternalNotePath(detail.request_number),
      { note: internalNote.trim() },
      () => setInternalNote(""),
      "Внутренняя заметка сохранена.",
    );
  }

  async function generateAiSuggestions() {
    if (!detail) return;
    await postAction(
      buildGenerateAiSuggestionsPath(detail.request_number),
      {},
      () => undefined,
      "AI-подсказки обновлены.",
    );
  }

  async function acceptAiClarification(suggestionId: number) {
    if (!detail) return;
    await postAction(
      buildAcceptAiClarificationPath(detail.request_number, suggestionId),
      {},
      () => undefined,
      "AI-вопрос добавлен как уточнение клиенту.",
    );
  }

  async function ignoreAiSuggestion(suggestionId: number) {
    if (!detail) return;
    await postAction(
      buildIgnoreAiSuggestionPath(detail.request_number, suggestionId),
      {},
      () => undefined,
      "AI-подсказка скрыта.",
    );
  }

  function selectTechnicianCandidate(candidate: (typeof technicianCandidates)[number]) {
    setTechnicianName(candidate.name);
    setTechnicianPhone(candidate.phone);
    setTechnicianRegion(candidate.region);
  }

  const pendingAiSuggestions = detail?.ai_suggestions?.filter((suggestion) => suggestion.status === "pending") ?? [];
  const archivedAiSuggestions = detail?.ai_suggestions?.filter((suggestion) => suggestion.status !== "pending") ?? [];
  const visibleAiSuggestions = pendingAiSuggestions.length ? pendingAiSuggestions : detail?.ai_suggestions?.slice(0, 3) ?? [];
  const visibleTimeline = detail?.timeline.slice(-2) ?? [];
  const hiddenTimeline = detail?.timeline.slice(0, Math.max((detail?.timeline.length ?? 0) - 2, 0)) ?? [];
  const hiddenTimelineCount = hiddenTimeline.length;
  const notificationFailures = detail?.notification_deliveries?.filter((delivery) => delivery.status === "failed") ?? [];
  const technicalLogCount = detail?.notification_deliveries?.length ?? 0;

  return (
    <div className="app-page dispatcher-page">
      <WorkspaceHeader session={session} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Внутренний контур</span>
              <h1>Диспетчерская</h1>
              <p>Заявки, статусы, уточнения, назначение мастера и внутренние заметки.</p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void refresh()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          <div className="dispatcher-workspace">
            <aside className="dispatcher-list" aria-label="Список заявок">
              <div className="dispatcher-filters">
                <select
                  aria-label="Фильтр по статусу"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as DispatcherStatusFilter)}
                >
                  <option value="all">Все статусы</option>
                  {[
                    "new",
                    "needs_clarification",
                    "awaiting_assignment",
                    "technician_assigned",
                    "visit_scheduled",
                    "diagnostics",
                    "waiting_for_parts",
                    "repair_in_progress",
                    "completed",
                    "closed",
                    "warranty_case",
                    "cancelled",
                  ].map((status) => (
                    <option key={status} value={status}>
                      {statusLabel(status as RequestStatus)}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Фильтр по срочности"
                  value={urgencyFilter}
                  onChange={(event) => setUrgencyFilter(event.target.value as DispatcherUrgencyFilter)}
                >
                  <option value="all">Любая срочность</option>
                  {urgencies.map((urgency) => (
                    <option key={urgency.value} value={urgency.value}>
                      {urgency.label}
                    </option>
                  ))}
                </select>
              </div>
              {filteredItems.length ? (
                filteredItems.map((item) => (
                  <button
                    className={selected === item.request_number ? "dispatcher-list-item active" : "dispatcher-list-item"}
                    key={item.request_number}
                    type="button"
                    onClick={() => setSelected(item.request_number)}
                  >
                    <span>{statusLabel(item.status)}</span>
                    <div className="dispatcher-list-titleline">
                      <strong>{item.request_number}</strong>
                      <time dateTime={item.created_at}>{formatCompactDateTime(item.created_at)}</time>
                    </div>
                    <em>{item.customer_name}</em>
                    <small>{item.machine_label}</small>
                    <div className="dispatcher-list-footline">
                      <small>{item.latest_event_title}</small>
                      <b>{urgencyLabel(item.urgency)}</b>
                    </div>
                  </button>
                ))
              ) : (
                <p className="dispatcher-empty">Заявок по выбранным фильтрам нет.</p>
              )}
            </aside>

            {detail ? (
              <section className="dispatcher-detail">
                <div className="dispatcher-card dispatcher-summary-card">
                  <div>
                    <span className="status-pill">{statusLabel(detail.status)}</span>
                    <h2>{detail.request_number}</h2>
                    <p>{detail.problem}</p>
                    <div className="dispatcher-focus-row" aria-label="Ключевые сигналы заявки">
                      <span>{urgencyLabel(detail.urgency)}</span>
                      <span>{detail.assignment.technician_name ? "Мастер назначен" : "Нужен мастер"}</span>
                      <span>{detail.clarification?.answer ? "Клиент ответил" : detail.clarification ? "Ждем ответ" : "Уточнений нет"}</span>
                      {notificationFailures.length ? <span className="danger">Ошибка уведомления</span> : null}
                    </div>
                  </div>
                  <dl>
                    <div>
                      <dt>Клиент</dt>
                      <dd>{detail.customer.name}</dd>
                    </div>
                    <div>
                      <dt>Телефон</dt>
                      <dd>{detail.customer.phone}</dd>
                    </div>
                    <div>
                      <dt>Кофемашина</dt>
                      <dd>
                        {detail.machine.brand}
                        {detail.machine.model ? ` ${detail.machine.model}` : ""}
                      </dd>
                    </div>
                    <div>
                      <dt>Адрес</dt>
                      <dd>{detail.address}</dd>
                    </div>
                    <div>
                      <dt>Telegram</dt>
                      <dd>{detail.customer.telegram ?? "не указан"}</dd>
                    </div>
                    <div>
                      <dt>Создана</dt>
                      <dd>
                        <time dateTime={detail.created_at}>{formatCompactDateTime(detail.created_at)}</time>
                      </dd>
                    </div>
                  </dl>
                </div>

                <details className="dispatcher-card ai-suggestions-panel">
                  <summary className="ai-suggestions-heading">
                    <span className="ai-suggestions-badge" aria-hidden="true">AI</span>
                    <div className="ai-suggestions-copy">
                      <h3>AI-подсказки</h3>
                      <p>Нажмите, чтобы открыть AI-ассистента</p>
                    </div>
                    <div className="ai-suggestions-meta">
                      <span>
                        {pendingAiSuggestions.length
                          ? `${pendingAiSuggestions.length} на проверке`
                          : "Нет активных подсказок"}
                      </span>
                    </div>
                  </summary>
                  <div className="ai-suggestions-body">
                    <button className="secondary-status-button" type="button" onClick={() => void generateAiSuggestions()} disabled={loading}>
                      Сгенерировать
                    </button>
                    {visibleAiSuggestions.length ? (
                      <div className="ai-suggestion-list">
                        {visibleAiSuggestions.map((suggestion) => (
                          <article className="ai-suggestion-item" key={suggestion.suggestion_id}>
                            <div className="ai-suggestion-titleline">
                              <span>{aiSuggestionKindLabel(suggestion.kind)}</span>
                              <strong>{suggestion.title}</strong>
                              <em>{aiSuggestionStatusLabel(suggestion.status)}</em>
                            </div>
                            <p className="ai-suggestion-content">{suggestion.content}</p>
                            <details className="ai-suggestion-details">
                              <summary>Подробнее</summary>
                              <small>{suggestion.rationale}</small>
                              <span>Уверенность: {Math.round(suggestion.confidence * 100)}%</span>
                              {suggestion.source_chunks.length ? (
                                <div className="ai-source-list">
                                  {suggestion.source_chunks.map((source) => (
                                    <span key={`${source.chunk_id}-${source.document_title}`}>
                                      {source.document_title} · {Math.round(source.score * 100)}%
                                    </span>
                                  ))}
                                </div>
                              ) : null}
                            </details>
                            {suggestion.status === "pending" ? (
                              <div className="ai-suggestion-actions">
                                {suggestion.kind === "diagnostic_question" ? (
                                  <button type="button" onClick={() => void acceptAiClarification(suggestion.suggestion_id)}>
                                    Принять как вопрос
                                  </button>
                                ) : null}
                                <button type="button" onClick={() => void ignoreAiSuggestion(suggestion.suggestion_id)}>
                                  Игнорировать
                                </button>
                              </div>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p>Подсказок пока нет. Сгенерируйте их после проверки описания заявки.</p>
                    )}
                    {archivedAiSuggestions.length ? (
                      <details className="ai-archive">
                        <summary>Архив AI ({archivedAiSuggestions.length})</summary>
                        <div className="ai-archive-list">
                          {archivedAiSuggestions.map((suggestion) => (
                            <span key={suggestion.suggestion_id}>
                              {aiSuggestionStatusLabel(suggestion.status)} · {suggestion.title}
                            </span>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </div>
                </details>

                <div className="dispatcher-grid">
                  <section className="dispatcher-card">
                    <div className="dispatcher-card-heading">
                      <h3>Последние события</h3>
                      <span>{detail.timeline.length}</span>
                    </div>
                    <div className="timeline compact-timeline">
                      {visibleTimeline.map((event) => (
                        <article className="timeline-item" key={`${event.title}-${event.created_at}`}>
                          <span />
                          <div>
                            <small>{statusLabel(event.status)}</small>
                            <h3>{event.title}</h3>
                            <p>{event.description}</p>
                            <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                          </div>
                        </article>
                      ))}
                    </div>
                    {hiddenTimelineCount ? (
                      <details className="dispatcher-extra-events">
                        <summary>Остальные события ({hiddenTimelineCount})</summary>
                        <div className="technical-log-section">
                          {hiddenTimeline.map((event) => (
                            <p key={`${event.title}-${event.created_at}-hidden`}>
                              <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                              <span>{event.title}</span>
                            </p>
                          ))}
                        </div>
                      </details>
                    ) : null}
                    {detail.notification_deliveries?.length ? (
                      <details className="dispatcher-technical-log">
                        <summary>Технический лог ({technicalLogCount})</summary>
                        <div className="technical-log-section">
                          <strong>Уведомления</strong>
                          {detail.notification_deliveries?.length ? (
                            detail.notification_deliveries.map((delivery) => (
                              <p key={delivery.event_id}>
                                <time dateTime={delivery.updated_at ?? delivery.created_at ?? undefined}>
                                  {formatCompactDateTime(delivery.updated_at ?? delivery.created_at)}
                                </time>
                                <span>
                                  {delivery.event_type} · {delivery.status} · {delivery.channel ?? "канал не указан"} · попытка {delivery.attempt_count}
                                  {delivery.error ? ` · ${delivery.error}` : ""}
                                </span>
                              </p>
                            ))
                          ) : (
                            <p>Событий доставки нет.</p>
                          )}
                        </div>
                      </details>
                    ) : null}
                  </section>

                  <section className="dispatcher-card">
                    <h3>Вопрос клиенту</h3>
                    {detail.clarification ? (
                      <p>
                        {detail.clarification.question}
                        {detail.clarification.answer ? ` Ответ: ${detail.clarification.answer}` : ""}
                      </p>
                    ) : (
                      <p>Открытых уточнений нет.</p>
                    )}
                    <form className="dispatcher-form" onSubmit={submitQuestion}>
                      <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Новый вопрос клиенту" required rows={3} />
                      <button className="submit-button" type="submit">Задать вопрос клиенту</button>
                    </form>
                  </section>

                  <section className="dispatcher-card">
                    <h3>Обновить статус</h3>
                    <p>Клиент увидит эти заголовок и описание в истории статуса.</p>
                    <form className="dispatcher-form" onSubmit={submitStatus}>
                      <select value={statusValue} onChange={(event) => setStatusValue(event.target.value as RequestStatus)}>
                        {[
                          "awaiting_assignment",
                          "technician_assigned",
                          "visit_scheduled",
                          "diagnostics",
                          "waiting_for_parts",
                          "repair_in_progress",
                          "completed",
                          "closed",
                          "cancelled",
                        ].map((status) => (
                          <option key={status} value={status}>
                            {statusLabel(status as RequestStatus)}
                          </option>
                        ))}
                      </select>
                      <input value={statusTitle} onChange={(event) => setStatusTitle(event.target.value)} placeholder="Заголовок для клиента" required />
                      <textarea value={statusDescription} onChange={(event) => setStatusDescription(event.target.value)} placeholder="Описание для клиента" required rows={2} />
                      <button className="submit-button" type="submit">Обновить статус</button>
                    </form>
                  </section>

                  <section className="dispatcher-card">
                    <h3>Назначение</h3>
                    <p>
                      {detail.assignment.technician_name
                        ? `${detail.assignment.technician_name}${detail.assignment.technician_phone ? ` · ${detail.assignment.technician_phone}` : ""}`
                        : "Мастер еще не назначен."}
                    </p>
                    {detail.assignment.visit_window ? <p>{detail.assignment.visit_window}</p> : null}
                    <div className="technician-candidates" aria-label="Кандидаты мастеров">
                      <strong>Кандидаты мастеров</strong>
                      {technicianCandidates.map((candidate) => (
                        <button
                          key={candidate.name}
                          type="button"
                          onClick={() => selectTechnicianCandidate(candidate)}
                        >
                          <span>{candidate.name}</span>
                          <small>
                            {candidate.skills} · {candidate.region}
                          </small>
                        </button>
                      ))}
                    </div>
                    <form className="dispatcher-form" onSubmit={submitAssignment}>
                      <input value={technicianName} onChange={(event) => setTechnicianName(event.target.value)} placeholder="Имя мастера" required />
                      <input value={technicianPhone} onChange={(event) => setTechnicianPhone(event.target.value)} placeholder="Телефон мастера" />
                      <input value={technicianRegion} onChange={(event) => setTechnicianRegion(event.target.value)} placeholder="Регион" />
                      <input value={visitWindow} onChange={(event) => setVisitWindow(event.target.value)} placeholder="Окно визита" />
                      <button className="submit-button" type="submit">Назначить мастера</button>
                    </form>
                  </section>

                  <section className="dispatcher-card">
                    <h3>Внутренние заметки</h3>
                    <div className="internal-note-list">
                      {detail.internal_notes.length ? (
                        detail.internal_notes.map((note) => (
                          <article key={`${note.created_at}-${note.note}`}>
                            <p>{note.note}</p>
                            <small>
                              {note.actor} · <time dateTime={note.created_at}>{formatCompactDateTime(note.created_at)}</time>
                            </small>
                          </article>
                        ))
                      ) : (
                        <p>Заметок пока нет.</p>
                      )}
                    </div>
                    <form className="dispatcher-form" onSubmit={submitInternalNote}>
                      <textarea value={internalNote} onChange={(event) => setInternalNote(event.target.value)} placeholder="Внутренняя заметка" required rows={3} />
                      <button className="submit-button" type="submit">Сохранить заметку</button>
                    </form>
                  </section>
                </div>
              </section>
            ) : (
              <section className="dispatcher-detail dispatcher-card">
                <h2>Выберите заявку</h2>
                <p>Откройте заявку из списка слева, чтобы увидеть детали и действия.</p>
              </section>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export function StaffLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function requestedNextPath(): string | null {
    if (typeof window === "undefined") return "/dispatcher";
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    return next?.startsWith("/") ? next : null;
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}/staff/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!response.ok) throw new Error(`Staff login failed with ${response.status}`);
      const body = (await response.json()) as {
        access_token: string;
        staff: { username: string; roles: StaffRole[] };
      };
      storeStaffSession({
        accessToken: body.access_token,
        username: body.staff.username,
        roles: body.staff.roles,
      });
      if (typeof window !== "undefined") window.location.href = resolveStaffLandingPath(body.staff, requestedNextPath());
    } catch {
      setMessage("Не удалось войти. Проверьте логин и пароль.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-page staff-login-page">
      <WorkspaceHeader />
      <main className="staff-login-main">
        <section className="staff-login-card">
          <div className="staff-login-badge">
            <Shield aria-hidden="true" />
          </div>
          <span>Внутренний контур</span>
          <h1>Вход для сотрудников</h1>
          <p>Доступ к диспетчерской и другим рабочим зонам открыт только сотрудникам с ролью.</p>
          <form className="staff-login-form" onSubmit={submitLogin}>
            <label>
              <span>Логин</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="name@company.example"
                required
                type="email"
              />
            </label>
            <label>
              <span>Пароль</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Введите пароль"
                required
                type="password"
              />
            </label>
            <button className="submit-button" type="submit" disabled={submitting}>
              <LogIn aria-hidden="true" />
              {submitting ? "Входим" : "Войти"}
            </button>
          </form>
          {message ? <p className="submit-error">{message}</p> : null}
        </section>
      </main>
    </div>
  );
}

export function ProtectedDispatcherPage({
  hasSession,
  initialSession,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    if (typeof hasSession === "boolean") {
      return hasSession ? { accessToken: "test-token", username: "dispatcher@coffeefix.local", roles: ["dispatcher"] } : null;
    }
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined) return;
    if (typeof hasSession === "boolean") return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if ((!stored || !staffHasRole(stored, "dispatcher")) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(window.location.pathname);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/dispatcher");
  }

  if (!staffHasRole(session, "dispatcher")) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>{isAuthenticated ? "Для диспетчерской нужна роль dispatcher." : "Диспетчерская находится во внутреннем контуре."}</p>
              <a className="submit-button" href={buildStaffLoginPath("/dispatcher")}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <DispatcherPage session={session} onLogout={logout} />;
}

const staffRoleOptions: StaffRole[] = ["admin", "dispatcher", "technician", "inventory"];

export function AdminPage({
  initialSession,
  initialStaff,
  initialAudit,
  onLogout,
}: {
  initialSession?: StaffSession | null;
  initialStaff?: StaffAccountListResponse;
  initialAudit?: StaffAuditListResponse;
  onLogout?: () => void;
}) {
  const session = initialSession ?? getStoredStaffSession();
  const [staff, setStaff] = useState<StaffAccountListResponse>(initialStaff ?? { items: [] });
  const [audit, setAudit] = useState<StaffAuditListResponse>(initialAudit ?? { items: [] });
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [createRoles, setCreateRoles] = useState<StaffRole[]>(["dispatcher"]);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, StaffRole[]>>(() =>
    Object.fromEntries((initialStaff?.items ?? []).map((item) => [item.username, item.roles])),
  );
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadStaff() {
    const response = await fetch(`${apiBaseUrl()}${buildAdminStaffPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Admin staff list failed with ${response.status}`);
    const body = (await response.json()) as StaffAccountListResponse;
    setStaff(body);
    setRoleDrafts(Object.fromEntries(body.items.map((item) => [item.username, item.roles])));
    return body;
  }

  async function loadAudit() {
    const response = await fetch(`${apiBaseUrl()}${buildAdminStaffAuditPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Admin audit list failed with ${response.status}`);
    const body = (await response.json()) as StaffAuditListResponse;
    setAudit(body);
  }

  async function refresh() {
    setLoading(true);
    setMessage(null);
    try {
      await loadStaff();
      await loadAudit();
    } catch {
      setMessage("Не удалось обновить учетные записи сотрудников.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialStaff || initialAudit) return;
    void refresh();
  }, [initialStaff, initialAudit]);

  function toggleRole(roles: StaffRole[], role: StaffRole): StaffRole[] {
    const next = roles.includes(role) ? roles.filter((item) => item !== role) : [...roles, role];
    return next.length ? staffRoleOptions.filter((item) => next.includes(item)) : roles;
  }

  async function submitCreateStaff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setTemporaryPassword(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildAdminStaffPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          username: username.trim(),
          display_name: displayName.trim(),
          password,
          roles: createRoles,
        }),
      });
      if (!response.ok) throw new Error(`Create staff failed with ${response.status}`);
      setUsername("");
      setDisplayName("");
      setPassword("");
      setCreateRoles(["dispatcher"]);
      await refresh();
      setMessage("Сотрудник создан.");
    } catch {
      setMessage("Не удалось создать сотрудника.");
    } finally {
      setLoading(false);
    }
  }

  async function postAdminAction(path: string, body: object, successMessage: string) {
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`Admin action failed with ${response.status}`);
      if (path.endsWith("/reset-password")) {
        const resetBody = (await response.json()) as { temporary_password: string };
        setTemporaryPassword(resetBody.temporary_password);
      } else {
        setTemporaryPassword(null);
      }
      await refresh();
      setMessage(successMessage);
    } catch {
      setMessage("Не удалось сохранить действие администратора.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-page dispatcher-page admin-page">
      <WorkspaceHeader session={session} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Административный контур</span>
              <h1>Администрирование</h1>
              <p>Учетные записи сотрудников, роли, жизненный цикл доступа и аудит действий.</p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void refresh()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          {temporaryPassword ? (
            <p className="temporary-password-result">
              Временный пароль: <strong>{temporaryPassword}</strong>
            </p>
          ) : null}
          <div className="admin-workspace">
            <section className="dispatcher-card admin-staff-card">
              <div className="admin-section-heading">
                <h2>Учетные записи сотрудников</h2>
                <span>{staff.items.length} записей</span>
              </div>
              <div className="admin-staff-table">
                {staff.items.length ? (
                  staff.items.map((account) => {
                    const draftRoles = roleDrafts[account.username] ?? account.roles;
                    return (
                      <article className={account.active ? "admin-staff-row" : "admin-staff-row inactive"} key={account.username}>
                        <div>
                          <strong>{account.display_name}</strong>
                          <span>{account.username}</span>
                          <small>
                            {account.active ? "Активен" : "Отключен"} · обновлен{" "}
                            <time dateTime={account.updated_at}>{formatCompactDateTime(account.updated_at)}</time>
                          </small>
                        </div>
                        <div className="role-chip-row" aria-label={`Роли ${account.username}`}>
                          {staffRoleOptions.map((role) => (
                            <button
                              className={draftRoles.includes(role) ? "role-chip selected" : "role-chip"}
                              key={role}
                              type="button"
                              onClick={() =>
                                setRoleDrafts((current) => ({
                                  ...current,
                                  [account.username]: toggleRole(draftRoles, role),
                                }))
                              }
                            >
                              {role}
                            </button>
                          ))}
                        </div>
                        <div className="admin-row-actions">
                          <button
                            type="button"
                            onClick={() =>
                              void postAdminAction(
                                buildAdminStaffRolesPath(account.username),
                                { roles: draftRoles },
                                "Роли сотрудника обновлены.",
                              )
                            }
                          >
                            Сохранить роли
                          </button>
                          {account.active ? (
                            <button
                              type="button"
                              onClick={() =>
                                void postAdminAction(buildAdminStaffDeactivatePath(account.username), {}, "Сотрудник отключен.")
                              }
                            >
                              Отключить
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() =>
                                void postAdminAction(buildAdminStaffActivatePath(account.username), {}, "Сотрудник активирован.")
                              }
                            >
                              Активировать
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() =>
                              void postAdminAction(buildAdminStaffResetPasswordPath(account.username), {}, "Пароль сброшен.")
                            }
                          >
                            Сбросить пароль
                          </button>
                        </div>
                      </article>
                    );
                  })
                ) : (
                  <p>Сотрудники пока не добавлены.</p>
                )}
              </div>
            </section>

            <section className="dispatcher-card admin-create-card">
              <h2>Новый сотрудник</h2>
              <form className="dispatcher-form" onSubmit={submitCreateStaff}>
                <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="email сотрудника" required type="email" />
                <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Имя в интерфейсе" required />
                <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Временный пароль" required type="password" minLength={8} />
                <div className="admin-role-control">
                  <span>Роли сотрудника</span>
                  <div className="role-chip-row">
                    {staffRoleOptions.map((role) => (
                      <button
                        className={createRoles.includes(role) ? "role-chip selected" : "role-chip"}
                        key={role}
                        type="button"
                        onClick={() => setCreateRoles((current) => toggleRole(current, role))}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
                <button className="submit-button" type="submit" disabled={loading}>
                  Создать сотрудника
                </button>
              </form>
            </section>

            <section className="dispatcher-card admin-audit-card">
              <div className="admin-section-heading">
                <h2>Аудит действий</h2>
                <span>{audit.items.length} событий</span>
              </div>
              <div className="admin-audit-list">
                {audit.items.length ? (
                  audit.items.map((event) => (
                    <article key={`${event.created_at}-${event.action}-${event.target_username}`}>
                      <strong>{event.action}</strong>
                      <span>{event.target_username}</span>
                      <small>
                        {event.actor_username} · <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                      </small>
                    </article>
                  ))
                ) : (
                  <p>Событий аудита пока нет.</p>
                )}
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

export function ProtectedAdminPage({
  hasSession,
  initialSession,
  initialStaff,
  initialAudit,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialStaff?: StaffAccountListResponse;
  initialAudit?: StaffAuditListResponse;
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    if (typeof hasSession === "boolean") {
      return hasSession ? { accessToken: "test-token", username: "admin@coffeefix.local", roles: ["admin"] } : null;
    }
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined || typeof hasSession === "boolean") return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if ((!stored || !staffHasRole(stored, "admin")) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(window.location.pathname);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/admin");
  }

  if (!staffHasRole(session, "admin")) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>{isAuthenticated ? "Для управления сотрудниками нужна роль admin." : "Администрирование находится во внутреннем контуре."}</p>
              <a className="submit-button" href={buildStaffLoginPath("/admin")}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <AdminPage initialSession={session} onLogout={logout} initialStaff={initialStaff} initialAudit={initialAudit} />;
}

export function TechnicianPage({
  initialList,
  initialDetail,
  session,
  onLogout,
}: {
  initialList?: TechnicianListResponse;
  initialDetail?: TechnicianRequestDetail;
  session?: StaffSession | null;
  onLogout?: () => void;
}) {
  const [list, setList] = useState<TechnicianListResponse>(initialList ?? { items: [] });
  const [selected, setSelected] = useState(initialDetail?.request_number ?? initialList?.items[0]?.request_number ?? "");
  const [detail, setDetail] = useState<TechnicianRequestDetail | null>(initialDetail ?? null);
  const [diagnosisSummary, setDiagnosisSummary] = useState("");
  const [resultSummary, setResultSummary] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [partId, setPartId] = useState("");
  const [partQuantity, setPartQuantity] = useState("1");
  const [partNote, setPartNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadList() {
    const response = await fetch(`${apiBaseUrl()}${buildTechnicianListPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Technician list failed with ${response.status}`);
    const body = (await response.json()) as TechnicianListResponse;
    setList(body);
    if (!selected && body.items[0]) setSelected(body.items[0].request_number);
    return body;
  }

  async function loadDetail(requestNumber: string) {
    if (!requestNumber) return;
    const response = await fetch(`${apiBaseUrl()}${buildTechnicianDetailPath(requestNumber)}`, {
      headers: staffAuthHeaders(session),
    });
    if (!response.ok) throw new Error(`Technician detail failed with ${response.status}`);
    const body = (await response.json()) as TechnicianRequestDetail;
    setDetail(body);
    setSelected(body.request_number);
  }

  async function refresh(requestNumber = selected) {
    setLoading(true);
    setMessage(null);
    try {
      await loadList();
      if (requestNumber) await loadDetail(requestNumber);
    } catch {
      setMessage("Не удалось обновить выезды мастера.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialList || initialDetail) return;
    void refresh();
  }, [initialList, initialDetail]);

  useEffect(() => {
    if (!selected || selected === detail?.request_number) return;
    void loadDetail(selected).catch(() => setMessage("Не удалось открыть выезд."));
  }, [selected, detail?.request_number]);

  async function postTechnicianAction(path: string, body: object, successMessage: string, afterSuccess: () => void = () => undefined) {
    if (!detail) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`Technician action failed with ${response.status}`);
      afterSuccess();
      await refresh(detail.request_number);
      setMessage(successMessage);
    } catch {
      setMessage("Не удалось сохранить действие мастера.");
    } finally {
      setLoading(false);
    }
  }

  async function submitDiagnosis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postTechnicianAction(
      buildTechnicianDiagnosisPath(detail.request_number),
      {
        machine_powered_on: true,
        water_supply_checked: true,
        leak_checked: false,
        error_code_checked: true,
        summary: diagnosisSummary.trim(),
      },
      "Диагностика сохранена.",
      () => setDiagnosisSummary(""),
    );
  }

  async function submitResult(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postTechnicianAction(
      buildTechnicianResultPath(detail.request_number),
      {
        result: "waiting_for_parts",
        summary: resultSummary.trim(),
        next_step: nextStep.trim() || undefined,
      },
      "Результат выезда сохранен.",
      () => {
        setResultSummary("");
        setNextStep("");
      },
    );
  }

  async function submitPartsUsed(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postTechnicianAction(
      buildTechnicianPartsUsedPath(detail.request_number),
      {
        part_id: Number(partId),
        quantity: Number(partQuantity),
        note: partNote.trim() || undefined,
      },
      "Запчасти списаны по заявке.",
      () => {
        setPartId("");
        setPartQuantity("1");
        setPartNote("");
      },
    );
  }

  return (
    <div className="app-page dispatcher-page technician-page">
      <WorkspaceHeader session={session} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Мобильный контур</span>
              <h1>Выезды мастера</h1>
              <p>Назначенные заявки, диагностика, результат ремонта и списание запчастей.</p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void refresh()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          <div className="dispatcher-workspace technician-workspace">
            <aside className="dispatcher-list">
              {list.items.length ? (
                list.items.map((item) => (
                  <button
                    className={selected === item.request_number ? "dispatcher-list-item active" : "dispatcher-list-item"}
                    key={item.request_number}
                    type="button"
                    onClick={() => setSelected(item.request_number)}
                  >
                    <span>{statusLabel(item.status)}</span>
                    <strong>{item.request_number}</strong>
                    <em>{item.customer_name}</em>
                    <small>{item.machine_label}</small>
                    <small>{item.visit_window ?? item.latest_event_title}</small>
                  </button>
                ))
              ) : (
                <p className="dispatcher-empty">Назначенных выездов нет.</p>
              )}
            </aside>
            {detail ? (
              <section className="dispatcher-detail">
                <div className="dispatcher-card dispatcher-summary-card">
                  <div>
                    <span className="status-pill">{statusLabel(detail.status)}</span>
                    <h2>{detail.request_number}</h2>
                    <p>{detail.problem}</p>
                  </div>
                  <dl>
                    <div>
                      <dt>Клиент</dt>
                      <dd>{detail.customer_name}</dd>
                    </div>
                    <div>
                      <dt>Телефон</dt>
                      <dd>{detail.customer_phone}</dd>
                    </div>
                    <div>
                      <dt>Кофемашина</dt>
                      <dd>{detail.machine_label}</dd>
                    </div>
                    <div>
                      <dt>Окно визита</dt>
                      <dd>{detail.visit_window ?? "Не указано"}</dd>
                    </div>
                    <div>
                      <dt>Адрес</dt>
                      <dd>{detail.address}</dd>
                    </div>
                    <div>
                      <dt>Срочность</dt>
                      <dd>{urgencyLabel(detail.urgency)}</dd>
                    </div>
                  </dl>
                </div>

                <div className="dispatcher-grid technician-action-grid">
                  <section className="dispatcher-card technician-card">
                    <h3>Чеклист диагностики</h3>
                    <ul className="checklist-preview">
                      <li><CheckSquare aria-hidden="true" /> Питание включается</li>
                      <li><Droplets aria-hidden="true" /> Подача воды проверена</li>
                      <li><Eye aria-hidden="true" /> Протечки осмотрены</li>
                      <li><Monitor aria-hidden="true" /> Код ошибки проверен</li>
                    </ul>
                    {detail.diagnosis ? <p>{detail.diagnosis.summary}</p> : null}
                    <form className="dispatcher-form" onSubmit={submitDiagnosis}>
                      <textarea value={diagnosisSummary} onChange={(event) => setDiagnosisSummary(event.target.value)} placeholder="Итог диагностики" required rows={3} />
                      <button className="submit-button" type="submit">Сохранить диагностику</button>
                    </form>
                  </section>

                  <section className="dispatcher-card technician-card">
                    <h3>Результат ремонта</h3>
                    {detail.repair_result ? <p>{detail.repair_result.summary}</p> : <p>Результат еще не зафиксирован.</p>}
                    <form className="dispatcher-form" onSubmit={submitResult}>
                      <textarea value={resultSummary} onChange={(event) => setResultSummary(event.target.value)} placeholder="Что сделано или что требуется" required rows={3} />
                      <input value={nextStep} onChange={(event) => setNextStep(event.target.value)} placeholder="Следующий шаг" />
                      <button className="submit-button" type="submit">Сохранить результат</button>
                    </form>
                  </section>

                  <section className="dispatcher-card technician-card">
                    <h3>Использованные запчасти</h3>
                    <p>Списание уменьшает остаток на складе и добавляет событие в историю заявки.</p>
                    <form className="dispatcher-form compact-form" onSubmit={submitPartsUsed}>
                      <input value={partId} onChange={(event) => setPartId(event.target.value)} placeholder="ID запчасти" required type="number" min="1" />
                      <input value={partQuantity} onChange={(event) => setPartQuantity(event.target.value)} placeholder="Количество" required type="number" min="1" />
                      <input value={partNote} onChange={(event) => setPartNote(event.target.value)} placeholder="Комментарий" />
                      <button className="submit-button" type="submit">Списать запчасть</button>
                    </form>
                  </section>
                </div>
              </section>
            ) : (
              <section className="dispatcher-detail dispatcher-card">
                <h2>Выберите выезд</h2>
                <p>Откройте назначенную заявку, чтобы зафиксировать работу.</p>
              </section>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export function ProtectedTechnicianPage({
  hasSession,
  initialSession,
  initialList,
  initialDetail,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialList?: TechnicianListResponse;
  initialDetail?: TechnicianRequestDetail;
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    if (typeof hasSession === "boolean") {
      return hasSession ? { accessToken: "test-token", username: "technician@coffeefix.local", roles: ["technician"] } : null;
    }
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined || typeof hasSession === "boolean") return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if ((!stored || !staffHasRole(stored, "technician")) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(window.location.pathname);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/technician");
  }

  if (!staffHasRole(session, "technician")) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>{isAuthenticated ? "Для выездов нужна роль technician." : "Выезды мастера находятся во внутреннем контуре."}</p>
              <a className="submit-button" href={buildStaffLoginPath("/technician")}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <TechnicianPage session={session} onLogout={logout} initialList={initialList} initialDetail={initialDetail} />;
}

export function InventoryPage({
  initialParts,
  session,
  onLogout,
}: {
  initialParts?: InventoryPartListResponse;
  session?: StaffSession | null;
  onLogout?: () => void;
}) {
  const [parts, setParts] = useState<InventoryPartListResponse>(initialParts ?? { items: [] });
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [unit, setUnit] = useState("pcs");
  const [stockPartId, setStockPartId] = useState("");
  const [stockCount, setStockCount] = useState("0");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadParts() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryPartsPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Inventory parts failed with ${response.status}`);
    const body = (await response.json()) as InventoryPartListResponse;
    setParts(body);
  }

  useEffect(() => {
    if (initialParts) return;
    void loadParts().catch(() => setMessage("Не удалось загрузить склад."));
  }, [initialParts]);

  async function submitPart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryPartsPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          sku: sku.trim(),
          name: name.trim(),
          brand: brand.trim() || undefined,
          model: model.trim() || undefined,
          unit: unit.trim(),
        }),
      });
      if (!response.ok) throw new Error(`Create part failed with ${response.status}`);
      setSku("");
      setName("");
      setBrand("");
      setModel("");
      setUnit("pcs");
      await loadParts();
      setMessage("Позиция добавлена.");
    } catch {
      setMessage("Не удалось добавить позицию.");
    } finally {
      setLoading(false);
    }
  }

  async function submitStock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryStockPath(Number(stockPartId))}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({ quantity_on_hand: Number(stockCount) }),
      });
      if (!response.ok) throw new Error(`Stock update failed with ${response.status}`);
      setStockPartId("");
      setStockCount("0");
      await loadParts();
      setMessage("Остаток обновлен.");
    } catch {
      setMessage("Не удалось обновить остаток.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-page dispatcher-page inventory-page">
      <WorkspaceHeader session={session} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Складской контур</span>
              <h1>Склад запчастей</h1>
              <p>Каталог, совместимость и базовые остатки для ремонтных выездов.</p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void loadParts()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          <div className="inventory-workspace">
            <section className="dispatcher-card inventory-table-card">
              <h2>Каталог</h2>
              <div className="inventory-table">
                {parts.items.length ? (
                  parts.items.map((part) => (
                    <article key={part.part_id}>
                      <strong>{part.sku}</strong>
                      <span>{part.name}</span>
                      <small>
                        {[part.brand, part.model].filter(Boolean).join(" ") || "Без привязки к модели"}
                      </small>
                      <em>Остаток: {part.quantity_on_hand} {part.unit}</em>
                      {part.stock_updated_at ? (
                        <small>
                          обновлен <time dateTime={part.stock_updated_at}>{formatCompactDateTime(part.stock_updated_at)}</time>
                        </small>
                      ) : null}
                    </article>
                  ))
                ) : (
                  <p>Каталог пока пуст.</p>
                )}
              </div>
            </section>
            <section className="dispatcher-card">
              <h2>Новая позиция</h2>
              <form className="dispatcher-form" onSubmit={submitPart}>
                <input value={sku} onChange={(event) => setSku(event.target.value)} placeholder="SKU" required />
                <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Название" required />
                <input value={brand} onChange={(event) => setBrand(event.target.value)} placeholder="Бренд" />
                <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="Модель" />
                <input value={unit} onChange={(event) => setUnit(event.target.value)} placeholder="Единица" required />
                <button className="submit-button" type="submit">Добавить позицию</button>
              </form>
            </section>
            <section className="dispatcher-card">
              <h2>Обновить остаток</h2>
              <form className="dispatcher-form compact-form" onSubmit={submitStock}>
                <input value={stockPartId} onChange={(event) => setStockPartId(event.target.value)} placeholder="ID позиции" type="number" min="1" required />
                <input value={stockCount} onChange={(event) => setStockCount(event.target.value)} placeholder="Остаток" type="number" min="0" required />
                <button className="submit-button" type="submit">Обновить остаток</button>
              </form>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

export function ProtectedInventoryPage({
  hasSession,
  initialSession,
  initialParts,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialParts?: InventoryPartListResponse;
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    if (typeof hasSession === "boolean") {
      return hasSession ? { accessToken: "test-token", username: "inventory@coffeefix.local", roles: ["inventory"] } : null;
    }
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined || typeof hasSession === "boolean") return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if ((!stored || !staffHasRole(stored, "inventory")) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(window.location.pathname);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/inventory");
  }

  if (!staffHasRole(session, "inventory")) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>{isAuthenticated ? "Для склада нужна роль inventory." : "Склад находится во внутреннем контуре."}</p>
              <a className="submit-button" href={buildStaffLoginPath("/inventory")}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <InventoryPage session={session} onLogout={logout} initialParts={initialParts} />;
}

function RequestForm() {
  const [form, setForm] = useState<IntakeFormState>(initialForm);
  const [step, setStep] = useState<FormStep>(1);
  const [requestNumber, setRequestNumber] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (key: keyof IntakeFormState) => (value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    setValidationWarning(null);
  };

  function requireCurrentStepFields(): boolean {
    const missingFields = validateIntakeStep(form, step);
    if (missingFields.length === 0) {
      setValidationWarning(null);
      return true;
    }
    setValidationWarning(`Заполните: ${missingFields.join(", ")}`);
    return false;
  }

  function goToNextStep() {
    setSubmitError(null);
    if (!requireCurrentStepFields()) return;
    setStep(getNextFormStep(step));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    if (step < 3) {
      goToNextStep();
      return;
    }

    if (!requireCurrentStepFields()) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl()}/service-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildServiceRequestPayload(form)),
      });
      if (!response.ok) throw new Error(`Request failed with ${response.status}`);
      const body = (await response.json()) as { request_number: string };
      setRequestNumber(body.request_number);
    } catch {
      setSubmitError("Не удалось отправить заявку. Проверьте данные и попробуйте еще раз.");
    } finally {
      setSubmitting(false);
    }
  }

  function startNewRequest() {
    setForm(initialForm);
    setStep(1);
    setRequestNumber(null);
    setSubmitError(null);
    setValidationWarning(null);
  }

  if (requestNumber) {
    return (
      <section className="request-section request-section-success" id="request-form">
        <SuccessState requestNumber={requestNumber} onCreateNew={startNewRequest} />
      </section>
    );
  }

  return (
    <section className="request-section" id="request-form">
      <form className="request-card" onSubmit={handleSubmit}>
        <div className="request-heading">
          <h2>Заявка на ремонт кофемашины</h2>
          <p>Заполните форму - диспетчер уточнит детали и предложит ближайшее время выезда.</p>
          <div className="stepper" aria-label="Шаги формы">
            {([1, 2, 3] as FormStep[]).map((item) => (
              <button
                className={step === item ? "step active" : step > item ? "step complete" : "step"}
                key={item}
                type="button"
                onClick={() => {
                  if (item < step) {
                    setValidationWarning(null);
                    setStep(item);
                  }
                }}
              >
                <span>{step > item ? "✓" : item}</span>
                <strong>{item === 1 ? "Контакты" : item === 2 ? "Кофемашина и проблема" : "Адрес и время"}</strong>
              </button>
            ))}
          </div>
        </div>

        {step === 1 ? (
          <div className="form-stack">
            <Field label="Имя">
              <input value={form.name} onChange={(event) => set("name")(event.target.value)} placeholder="Как вас зовут?" required />
            </Field>
            <Field label="Телефон">
              <input
                value={form.phone}
                onChange={(event) => set("phone")(event.target.value)}
                placeholder="+7 (___) ___-__-__"
                required
                type="tel"
              />
            </Field>
            <Field label="Telegram" optional>
              <input value={form.telegram} onChange={(event) => set("telegram")(event.target.value)} placeholder="@username" />
            </Field>
            <div className="control-group">
              <span className="field-label">Тип клиента</span>
              <ChipGroup value={form.clientType} options={clientTypes} onChange={(value) => set("clientType")(value)} />
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="form-stack">
            <Field label="Бренд кофемашины">
              <select value={form.brand} onChange={(event) => set("brand")(event.target.value)} required>
                <option value="" disabled>
                  Выберите бренд
                </option>
                {["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli", "Другое"].map((brand) => (
                  <option key={brand} value={brand}>
                    {brand}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Модель" optional>
              <input value={form.model} onChange={(event) => set("model")(event.target.value)} placeholder="Например: Jura E6, Saeco Xelsis" />
            </Field>
            <div className="control-group">
              <span className="field-label">Где находится кофемашина</span>
              <ChipGroup value={form.locationType} options={locations} onChange={(value) => set("locationType")(value)} />
            </div>
            <Field label="Что случилось?">
              <textarea
                value={form.problem}
                onChange={(event) => set("problem")(event.target.value)}
                placeholder="Например: не мелет кофе, течет вода, ошибка на дисплее, не включается"
                required
                rows={3}
              />
            </Field>
            <div className="control-group">
              <span className="field-label">Срочность</span>
              <ChipGroup value={form.urgency} options={urgencies} onChange={(value) => set("urgency")(value)} />
            </div>
          </div>
        ) : null}

        {step === 3 ? (
          <div className="form-stack">
            <Field label="Район или адрес">
              <input value={form.address} onChange={(event) => set("address")(event.target.value)} placeholder="Например: м. Тверская, ул. Пушкина, 10" required />
            </Field>
            <Field label="Удобное время визита" optional>
              <input value={form.visitTime} onChange={(event) => set("visitTime")(event.target.value)} placeholder="Например: завтра после 14:00" />
            </Field>
            <Field label="Фото или видео" optional>
              <div className="attachment-grid">
                <input value={form.attachmentFilename} onChange={(event) => set("attachmentFilename")(event.target.value)} placeholder="leak.jpg" />
                <input value={form.attachmentContentType} onChange={(event) => set("attachmentContentType")(event.target.value)} placeholder="image/jpeg" />
                <input inputMode="numeric" value={form.attachmentSizeBytes} onChange={(event) => set("attachmentSizeBytes")(event.target.value)} placeholder="34822" />
              </div>
            </Field>
            <Field label="Комментарий" optional>
              <textarea value={form.comment} onChange={(event) => set("comment")(event.target.value)} placeholder="Любые дополнительные сведения" rows={2} />
            </Field>
          </div>
        ) : null}

        <div className="form-navigation">
          {step > 1 ? (
            <button
              className="back-button"
              type="button"
              onClick={() => {
                setValidationWarning(null);
                setStep((current) => (current - 1) as FormStep);
              }}
            >
              ← Назад
            </button>
          ) : (
            <span />
          )}
          {step < 3 ? (
            <button className="next-button" type="button" onClick={goToNextStep}>
              Далее
              <ChevronRight aria-hidden="true" />
            </button>
          ) : (
            <button className="submit-button" disabled={submitting} type="submit">
              <Send aria-hidden="true" />
              {submitting ? "Отправляем" : "Отправить заявку"}
            </button>
          )}
        </div>
        {step === 3 ? <p className="consent-copy">Нажимая кнопку, вы соглашаетесь с обработкой персональных данных.</p> : null}
        {validationWarning ? (
          <p className="validation-warning" role="alert">
            {validationWarning}
          </p>
        ) : null}
        {submitError ? <p className="submit-error">{submitError}</p> : null}
      </form>
    </section>
  );
}

function BrandsSection() {
  return (
    <section className="section white-section" id="brands">
      <div className="section-inner">
        <SectionHeading
          title="Какие кофемашины ремонтируем"
          copy="Работаем с домашними, офисными и профессиональными кофемашинами всех ведущих брендов."
        />
        <div className="brand-grid">
          {brands.map((brand) => (
            <div key={brand}>{brand}</div>
          ))}
        </div>
        <div className="machine-types">
          <p>Типы кофемашин</p>
          <div>
            {machineTypes.map((type) => (
              <span key={type}>{type}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function IssuesSection() {
  return (
    <section className="section warm-section" id="services">
      <div className="section-inner">
        <SectionHeading
          title="Частые неисправности"
          copy="Опытные мастера диагностируют и устраняют любые неполадки - от механических до электронных."
        />
        <div className="issue-grid">
          {issues.map((issue) => {
            const Icon = issue.icon;
            return (
              <article className="info-card" key={issue.title}>
                <span className="info-icon">
                  <Icon aria-hidden="true" />
                </span>
                <h3>{issue.title}</h3>
                <p>{issue.desc}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section white-section" id="how-it-works">
      <div className="section-inner">
        <SectionHeading title="Как проходит ремонт" copy="Простой и прозрачный процесс - от заявки до готовой кофемашины." />
        <div className="steps-grid">
          {repairSteps.map((item, index) => {
            const Icon = item.icon;
            return (
              <article className="repair-step" key={item.title}>
                <div>
                  <span className="step-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <small>Шаг {index + 1}</small>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            );
          })}
        </div>
        <p className="note-box">
          <strong>Примечание:</strong> Если для ремонта нужна деталь, мы проверим наличие на складе и согласуем срок поставки.
        </p>
      </div>
    </section>
  );
}

function TrustSection() {
  return (
    <section className="section warm-section" id="trust">
      <div className="section-inner">
        <SectionHeading title="Почему выбирают нас" copy="Работаем честно, быстро и с гарантией результата." />
        <div className="trust-grid">
          {trustCards.map((card) => {
            const Icon = card.icon;
            return (
              <article className="info-card trust-card" key={card.title}>
                <span className={card.tone === "green" ? "info-icon green" : "info-icon"}>
                  <Icon aria-hidden="true" />
                </span>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer" id="footer">
      <div className="footer-cta">
        <div className="section-inner footer-cta-inner">
          <div>
            <p>Кофемашина не работает?</p>
            <span>Оставьте заявку - мастер приедет в день обращения</span>
          </div>
          <a href="/#request-form">
            Оставить заявку на ремонт
            <ArrowRight aria-hidden="true" />
          </a>
        </div>
      </div>
      <div className="section-inner footer-main">
        <FooterColumn title="Услуги" items={footerServices.map((label) => ({ label, href: "#services" }))} />
        <FooterColumn title="Бренды" items={footerBrands.map((label) => ({ label, href: "#brands" }))} />
        <FooterColumn title="Клиентам" items={footerClientLinks} />
        <div>
          <h3>Контакты</h3>
          <ul className="footer-contacts">
            <li>
              <Phone aria-hidden="true" />
              <a href="tel:+74950000000">+7 (495) 000-00-00</a>
            </li>
            <li>
              <MessageCircle aria-hidden="true" />
              <a href="https://t.me/coffeefixpro">@coffeefixpro</a>
            </li>
            <li>
              <Mail aria-hidden="true" />
              <a href="mailto:info@coffeefixpro.ru">info@coffeefixpro.ru</a>
            </li>
            <li>
              <Clock aria-hidden="true" />
              <span>Пн-Вс 08:00-22:00</span>
            </li>
            <li>
              <MapPin aria-hidden="true" />
              <span>Москва и МО</span>
            </li>
          </ul>
        </div>
      </div>
      <div className="section-inner footer-bottom">
        <Logo />
        <p>© 2026 CoffeeFix Pro. Ремонт и обслуживание кофемашин.</p>
        <div>
          <a href="#top">Политика конфиденциальности</a>
          <a href="#top">Публичная оферта</a>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ title, items }: { title: string; items: Array<{ label: string; href: string }> }) {
  return (
    <div>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item.label}>
            <a href={item.href}>{item.label}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SectionHeading({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="section-heading">
      <h2>{title}</h2>
      <p>{copy}</p>
    </div>
  );
}

export function App() {
  const isDispatcherRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/dispatcher");
  const isTechnicianRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/technician");
  const isInventoryRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/inventory");
  const isAdminRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/admin");
  const isStaffLoginRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/staff/login");
  const isStatusRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/status");
  if (isStaffLoginRoute) return <StaffLoginPage />;
  if (isAdminRoute) return <ProtectedAdminPage />;
  if (isDispatcherRoute) return <ProtectedDispatcherPage />;
  if (isTechnicianRoute) return <ProtectedTechnicianPage />;
  if (isInventoryRoute) return <ProtectedInventoryPage />;
  if (isStatusRoute) return <StatusPage />;

  return (
    <div className="app-page">
      <ServiceBar />
      <Header />
      <main>
        <HeroSection />
        <RequestForm />
        <BrandsSection />
        <IssuesSection />
        <HowItWorks />
        <TrustSection />
      </main>
      <Footer />
      <div className="mobile-sticky-cta">
        <a href="tel:+74950000000" aria-label="Позвонить">
          <Phone aria-hidden="true" />
        </a>
        <a href="/#request-form">Оставить заявку</a>
      </div>
    </div>
  );
}

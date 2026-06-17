import type { AiSuggestionKind, AiSuggestionStatus, AppointmentStatus, InventoryCompatibility, InventoryMovement, InventoryPartItem, RequestStatus, Urgency } from "./types";

const inventoryTermLabels: Record<string, string> = {
  application: "применение",
  "automatic thermoblock": "автоматический термоблок",
  boiler: "бойлер",
  "boiler probe": "датчик бойлера",
  "commercial steam valve": "паровой клапан коммерческой линейки",
  connector: "соединение",
  diameter: "диаметр",
  "e series": "серия E",
  "e61 group": "группа E61",
  "flow meter": "датчик протока",
  gasket: "прокладка",
  group: "группа",
  length: "длина",
  model: "модель",
  probe: "датчик",
  "philips/saeco automatic": "автоматические Philips/Saeco",
  pump: "насос",
  screen: "сетка",
  seal: "уплотнитель",
  "seal kit": "комплект уплотнителей",
  series: "серия",
  thread: "резьба",
  "thread/length": "резьба/длина",
  "steam valve seal": "уплотнитель парового клапана",
};

const inventoryUnitLabels: Record<string, string> = {
  inch: "дюйм",
  kit: "компл.",
  m: "м",
  ml: "мл",
  mm: "мм",
  pcs: "шт.",
  set: "набор",
};

function inventoryTermLabel(value: string | null | undefined): string | null {
  const text = value?.trim();
  if (!text) return null;
  return inventoryTermLabels[text.toLowerCase()] ?? text;
}

function inventoryUnitLabel(value: string | null | undefined): string | null {
  const text = value?.trim();
  if (!text) return null;
  return inventoryUnitLabels[text.toLowerCase()] ?? text;
}

export function buildInventoryPartSpecLabel(part: Pick<InventoryPartItem, "part_type" | "parameter_label" | "parameter_value" | "parameter_unit">): string {
  const type = inventoryTermLabel(part.part_type);
  const parameter = inventoryTermLabel(part.parameter_label);
  const value = [part.parameter_value, inventoryUnitLabel(part.parameter_unit)].filter(Boolean).join(" ");
  if (type && parameter && value) return `${type} · ${parameter}: ${value}`;
  if (type && value) return `${type} · ${value}`;
  if (type) return type;
  if (value) return value;
  return "Тип и параметры не заданы";
}

export function formatInventoryQuantity(quantity: number, unit: string): string {
  return `${quantity} ${inventoryUnitLabel(unit) ?? unit}`;
}

export function buildInventoryCompatibilityLabel(item: InventoryCompatibility): string {
  if (item.compatibility_level === "exact_model") {
    return `Модель: ${[item.brand, item.model].filter(Boolean).join(" · ")}`;
  }
  if (item.compatibility_level === "series") {
    return `Серия: ${[item.brand, inventoryTermLabel(item.series)].filter(Boolean).join(" · ")}`;
  }
  return `Группа: ${inventoryTermLabel(item.machine_family) ?? "не указана"}`;
}

export function inventoryMovementLabel(type: InventoryMovement["movement_type"]): string {
  const labels: Record<InventoryMovement["movement_type"], string> = {
    manual_adjustment: "Корректировка остатка",
    reservation_created: "Резерв создан",
    reservation_adjusted: "Резерв изменен",
    release: "Резерв снят",
    consumption: "Списание",
  };
  return labels[type];
}

export function statusLabel(status: RequestStatus): string {
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

export function urgencyLabel(urgency: Urgency): string {
  const labels: Record<Urgency, string> = {
    today: "Сегодня",
    one_two_days: "1-2 дня",
    planned: "Планово",
  };
  return labels[urgency];
}

export function appointmentStatusLabel(status: AppointmentStatus): string {
  const labels: Record<AppointmentStatus, string> = {
    scheduled: "Запланировано",
    rescheduled: "Перенесено",
    cancelled: "Отменено",
  };
  return labels[status];
}

export function toApiDateTime(value: string): string {
  if (!value.trim()) return "";
  if (value.includes("T") && /([+-]\d\d:\d\d|Z)$/.test(value)) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toISOString();
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

export function aiSuggestionKindLabel(kind: AiSuggestionKind): string {
  const labels: Record<AiSuggestionKind, string> = {
    intake_classification: "Классификация",
    diagnostic_question: "Вопрос",
    likely_cause: "Причина",
    parts: "Запчасти",
    customer_reply: "Ответ клиенту",
  };
  return labels[kind];
}

export function aiSuggestionStatusLabel(status: AiSuggestionStatus): string {
  const labels: Record<AiSuggestionStatus, string> = {
    pending: "На проверке",
    accepted: "Принято",
    ignored: "Игнорировано",
  };
  return labels[status];
}

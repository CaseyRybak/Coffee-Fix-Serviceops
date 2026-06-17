import type { ClientType, LocationType, Urgency } from "./types";

export const clientTypes: Array<{ value: ClientType; label: string }> = [
  { value: "private", label: "Частный клиент" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

export const locations: Array<{ value: LocationType; label: string }> = [
  { value: "home", label: "Дом" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

export const urgencies: Array<{ value: Urgency; label: string }> = [
  { value: "today", label: "Сегодня" },
  { value: "one_two_days", label: "В ближайшие 1-2 дня" },
  { value: "planned", label: "Плановое обслуживание" },
];

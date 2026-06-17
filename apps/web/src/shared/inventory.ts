import type { InventoryPartItem } from "./types";

export function normalizeInventoryIdentity(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase().replace(/\s+/g, " ");
}

export function buildInventoryFactualKey(
  partType: string | null | undefined,
  brand: string | null | undefined,
  parameterLabel: string | null | undefined,
  parameterValue: string | null | undefined,
  parameterUnit: string | null | undefined,
): string | null {
  const normalized = [
    normalizeInventoryIdentity(partType),
    normalizeInventoryIdentity(brand),
    normalizeInventoryIdentity(parameterLabel),
    normalizeInventoryIdentity(parameterValue),
    normalizeInventoryIdentity(parameterUnit),
  ];
  if (!normalized[0] || !normalized[3]) return null;
  return normalized.join("|");
}

function skuSegment(value: string | null | undefined): string | null {
  const segment = (value ?? "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return segment || null;
}

export function buildInventorySkuSuggestion({
  brand,
  model,
  partType,
  parameterLabel,
  parameterValue,
  parameterUnit,
}: {
  brand?: string | null;
  model?: string | null;
  partType?: string | null;
  parameterLabel?: string | null;
  parameterValue?: string | null;
  parameterUnit?: string | null;
}): string {
  return [brand, model, partType, parameterLabel, parameterValue, parameterUnit]
    .map(skuSegment)
    .filter(Boolean)
    .join("-");
}

export function uniqueInventoryValues(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.map((value) => value?.trim()).filter(Boolean) as string[])).sort((left, right) =>
    left.localeCompare(right),
  );
}

export function inventoryPartSearchText(part: InventoryPartItem): string {
  return [
    part.sku,
    part.name,
    part.brand,
    part.model,
    part.part_type,
    part.compatibility_note,
    ...(part.compatibility ?? []).flatMap((item) => [item.brand, item.model, item.series, item.machine_family, item.note]),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function partMatchesMachine(part: InventoryPartItem, machineLabel: string): boolean {
  const machine = normalizeInventoryIdentity(machineLabel);
  if (!machine) return false;
  return [part.brand, part.model].some((value) => value && machine.includes(normalizeInventoryIdentity(value)))
    || (part.compatibility ?? []).some((item) =>
      [item.brand, item.model, item.series, item.machine_family].some(
        (value) => value && machine.includes(normalizeInventoryIdentity(value)),
      ),
    );
}

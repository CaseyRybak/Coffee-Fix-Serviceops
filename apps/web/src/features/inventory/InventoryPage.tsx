import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { CheckCircle2, CircleSlash, FilePlus2, LogIn, PackageCheck, Send, Shield, Truck, XCircle } from "lucide-react";

import {
  apiBaseUrl,
  buildInventoryMovementsPath,
  buildInventoryPartCompatibilityPath,
  buildInventoryPartsPath,
  buildInventoryProcurementLowStockDraftPath,
  buildInventoryProcurementPurchaseRequestApprovePath,
  buildInventoryProcurementPurchaseRequestCancelPath,
  buildInventoryProcurementPurchaseRequestItemsPath,
  buildInventoryProcurementPurchaseRequestMarkOrderedPath,
  buildInventoryProcurementPurchaseRequestReceivePath,
  buildInventoryProcurementPurchaseRequestsPath,
  buildInventoryProcurementPurchaseRequestSubmitPath,
  buildInventoryProcurementSuppliersPath,
  buildInventoryReservationReleasePath,
  buildInventoryReservationsPath,
  buildInventoryStockPath,
} from "../../shared/api";
import { buildInventoryCompatibilityLabel, buildInventoryPartSpecLabel, formatCompactDateTime, formatInventoryQuantity, inventoryMovementLabel } from "../../shared/formatters";
import { buildInventoryFactualKey, buildInventorySkuSuggestion, inventoryPartSearchText, normalizeInventoryIdentity, uniqueInventoryValues } from "../../shared/inventory";
import { buildStaffLoginPath, clearStaffSession, getStoredStaffSession, redirectOnStaffAuthFailure, staffAuthHeaders, staffHasRole } from "../../shared/staffAuth";
import type {
  InventoryCompatibilityLevel,
  InventoryMovementListResponse,
  InventoryPartItem,
  InventoryPartListResponse,
  InventoryReservationListResponse,
  ProcurementSupplierListResponse,
  PurchaseRequest,
  PurchaseRequestListResponse,
  StaffSession,
} from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const procurementStatusLabels: Record<PurchaseRequest["status"], string> = {
  draft: "Черновик",
  pending_approval: "На согласовании",
  approved: "Согласовано",
  ordered: "Заказано",
  received: "Принято",
  cancelled: "Отменено",
};

const procurementStatusTones: Record<PurchaseRequest["status"], string> = {
  draft: "draft",
  pending_approval: "pending",
  approved: "approved",
  ordered: "ordered",
  received: "received",
  cancelled: "cancelled",
};
const inventoryCatalogPageSizes = [10, 50, 100] as const;

export function InventoryPage({
  initialParts,
  initialSuppliers,
  initialPurchaseRequests,
  session,
  onLogout,
  procurementOnly = false,
}: {
  initialParts?: InventoryPartListResponse;
  initialSuppliers?: ProcurementSupplierListResponse;
  initialPurchaseRequests?: PurchaseRequestListResponse;
  session?: StaffSession | null;
  onLogout?: () => void;
  procurementOnly?: boolean;
}) {
  const [parts, setParts] = useState<InventoryPartListResponse>(initialParts ?? { items: [] });
  const [reservations, setReservations] = useState<InventoryReservationListResponse>({ items: [] });
  const [movements, setMovements] = useState<InventoryMovementListResponse>({ items: [] });
  const [suppliers, setSuppliers] = useState<ProcurementSupplierListResponse>(initialSuppliers ?? { items: [] });
  const [purchaseRequests, setPurchaseRequests] = useState<PurchaseRequestListResponse>(initialPurchaseRequests ?? { items: [] });
  const [sku, setSku] = useState("");
  const [skuEdited, setSkuEdited] = useState(false);
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [unit, setUnit] = useState("pcs");
  const [initialStockCount, setInitialStockCount] = useState("0");
  const [initialLowStockThreshold, setInitialLowStockThreshold] = useState("");
  const [partType, setPartType] = useState("");
  const [parameterLabel, setParameterLabel] = useState("");
  const [parameterValue, setParameterValue] = useState("");
  const [parameterUnit, setParameterUnit] = useState("");
  const [compatibilityNote, setCompatibilityNote] = useState("");
  const [compatibilityPartId, setCompatibilityPartId] = useState("");
  const [compatibilityLevel, setCompatibilityLevel] = useState<InventoryCompatibilityLevel>("exact_model");
  const [compatibilityBrand, setCompatibilityBrand] = useState("");
  const [compatibilityModel, setCompatibilityModel] = useState("");
  const [compatibilitySeries, setCompatibilitySeries] = useState("");
  const [compatibilityFamily, setCompatibilityFamily] = useState("");
  const [compatibilityRowNote, setCompatibilityRowNote] = useState("");
  const [stockPartId, setStockPartId] = useState("");
  const [stockCount, setStockCount] = useState("0");
  const [lowStockThreshold, setLowStockThreshold] = useState("");
  const [reservationRequest, setReservationRequest] = useState("");
  const [reservationPartId, setReservationPartId] = useState("");
  const [reservationQuantity, setReservationQuantity] = useState("1");
  const [reservationNote, setReservationNote] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [supplierContact, setSupplierContact] = useState("");
  const [supplierPhone, setSupplierPhone] = useState("");
  const [supplierEmail, setSupplierEmail] = useState("");
  const [supplierNote, setSupplierNote] = useState("");
  const [purchaseSupplierId, setPurchaseSupplierId] = useState("");
  const [purchasePartId, setPurchasePartId] = useState("");
  const [purchaseQuantity, setPurchaseQuantity] = useState("1");
  const [purchaseNote, setPurchaseNote] = useState("");
  const [editPurchaseRequestId, setEditPurchaseRequestId] = useState<number | null>(null);
  const [editPartId, setEditPartId] = useState("");
  const [editQuantity, setEditQuantity] = useState("1");
  const [editNote, setEditNote] = useState("");
  const [inventorySearch, setInventorySearch] = useState("");
  const [inventoryPageSize, setInventoryPageSize] = useState<(typeof inventoryCatalogPageSizes)[number]>(10);
  const [inventoryPage, setInventoryPage] = useState(1);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const isInventoryStaff = staffHasRole(session ?? null, "inventory");
  const isAdminStaff = staffHasRole(session ?? null, "admin");
  const cabinetPath = procurementOnly ? "/procurement" : "/inventory";

  const brandOptions = uniqueInventoryValues(parts.items.map((part) => part.brand));
  const modelOptions = uniqueInventoryValues(
    parts.items
      .filter((part) => !brand.trim() || normalizeInventoryIdentity(part.brand) === normalizeInventoryIdentity(brand))
      .map((part) => part.model),
  );
  const partTypeOptions = uniqueInventoryValues(parts.items.map((part) => part.part_type));
  const parameterLabelOptions = uniqueInventoryValues(parts.items.map((part) => part.parameter_label));
  const parameterUnitOptions = uniqueInventoryValues(parts.items.map((part) => part.parameter_unit));
  const compatibilitySeriesOptions = uniqueInventoryValues(parts.items.flatMap((part) => (part.compatibility ?? []).map((item) => item.series)));
  const compatibilityFamilyOptions = uniqueInventoryValues(
    parts.items.flatMap((part) => (part.compatibility ?? []).map((item) => item.machine_family)),
  );
  const proposedFactualKey = buildInventoryFactualKey(partType, brand, parameterLabel, parameterValue, parameterUnit);
  const suggestedSku = buildInventorySkuSuggestion({ brand, model, partType, parameterLabel, parameterValue, parameterUnit });
  const duplicatePart = proposedFactualKey
    ? parts.items.find((part) => part.factual_key === proposedFactualKey)
    : undefined;
  const inventorySearchTerm = inventorySearch.trim().toLowerCase();
  const visibleParts = inventorySearchTerm
    ? parts.items.filter((part) => inventoryPartSearchText(part).includes(inventorySearchTerm))
    : parts.items;
  const inventoryTotalPages = Math.max(1, Math.ceil(visibleParts.length / inventoryPageSize));
  const currentInventoryPage = Math.min(inventoryPage, inventoryTotalPages);
  const inventoryStartIndex = visibleParts.length ? (currentInventoryPage - 1) * inventoryPageSize : 0;
  const inventoryEndIndex = Math.min(inventoryStartIndex + inventoryPageSize, visibleParts.length);
  const paginatedParts = visibleParts.slice(inventoryStartIndex, inventoryEndIndex);
  const inventoryRangeLabel = visibleParts.length
    ? `Показано ${inventoryStartIndex + 1}-${inventoryEndIndex} из ${visibleParts.length}`
    : "Показано 0 из 0";
  const lowStockCount = parts.items.filter((part) => part.is_low_stock).length;
  const reservedPartsCount = parts.items.filter((part) => part.reserved_quantity > 0).length;

  function ensureStaffResponse(response: Response, context: string): void {
    if (redirectOnStaffAuthFailure(response.status, cabinetPath)) {
      throw new Error("Staff session expired");
    }
    if (!response.ok) throw new Error(`${context} failed with ${response.status}`);
  }

  async function loadParts() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryPartsPath()}`, { headers: staffAuthHeaders(session) });
    ensureStaffResponse(response, "Inventory parts");
    const body = (await response.json()) as InventoryPartListResponse;
    setParts(body);
  }

  async function loadReservations() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryReservationsPath()}`, { headers: staffAuthHeaders(session) });
    ensureStaffResponse(response, "Inventory reservations");
    const body = (await response.json()) as InventoryReservationListResponse;
    setReservations(body);
  }

  async function loadMovements() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryMovementsPath()}`, { headers: staffAuthHeaders(session) });
    ensureStaffResponse(response, "Inventory movements");
    const body = (await response.json()) as InventoryMovementListResponse;
    setMovements(body);
  }

  async function loadSuppliers() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementSuppliersPath()}`, { headers: staffAuthHeaders(session) });
    ensureStaffResponse(response, "Procurement suppliers");
    const body = (await response.json()) as ProcurementSupplierListResponse;
    setSuppliers(body);
  }

  async function loadPurchaseRequests() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementPurchaseRequestsPath()}`, { headers: staffAuthHeaders(session) });
    ensureStaffResponse(response, "Purchase requests");
    const body = (await response.json()) as PurchaseRequestListResponse;
    setPurchaseRequests(body);
  }

  async function refreshInventory() {
    const loaders = [loadParts()];
    if (isInventoryStaff) loaders.push(loadReservations(), loadMovements());
    if (isInventoryStaff || isAdminStaff) loaders.push(loadSuppliers(), loadPurchaseRequests());
    await Promise.all(loaders);
  }

  useEffect(() => {
    if (initialParts) return;
    void refreshInventory().catch(() => setMessage("Не удалось загрузить склад."));
  }, [initialParts]);

  useEffect(() => {
    if (skuEdited) return;
    setSku(suggestedSku);
  }, [skuEdited, suggestedSku]);

  useEffect(() => {
    setInventoryPage(1);
  }, [inventorySearchTerm, inventoryPageSize, parts.items.length]);

  useEffect(() => {
    if (!procurementOnly) return;
    if (purchaseSupplierId && suppliers.items.some((supplier) => String(supplier.supplier_id) === purchaseSupplierId)) return;
    if (suppliers.items.length === 1) setPurchaseSupplierId(String(suppliers.items[0].supplier_id));
  }, [procurementOnly, purchaseSupplierId, suppliers.items]);

  async function submitPart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (duplicatePart) {
      setMessage(`Такая запчасть уже есть в каталоге: ${duplicatePart.sku}.`);
      return;
    }
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
          compatibility_note: compatibilityNote.trim() || undefined,
          part_type: partType.trim() || undefined,
          parameter_label: parameterLabel.trim() || undefined,
          parameter_value: parameterValue.trim() || undefined,
          parameter_unit: parameterUnit.trim() || undefined,
        }),
      });
      if (response.status === 409) {
        setMessage("Позиция не добавлена: такая фактическая запчасть уже есть или была в каталоге.");
        return;
      }
      ensureStaffResponse(response, "Create part");
      const createdPart = (await response.json()) as InventoryPartItem;
      if (Number(initialStockCount) > 0 || initialLowStockThreshold.trim()) {
        const stockResponse = await fetch(`${apiBaseUrl()}${buildInventoryStockPath(createdPart.part_id)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
          body: JSON.stringify({
            quantity_on_hand: Number(initialStockCount),
            low_stock_threshold: initialLowStockThreshold ? Number(initialLowStockThreshold) : undefined,
          }),
        });
        ensureStaffResponse(stockResponse, "Initial stock");
      }
      setSku("");
      setSkuEdited(false);
      setName("");
      setBrand("");
      setModel("");
      setUnit("pcs");
      setInitialStockCount("0");
      setInitialLowStockThreshold("");
      setPartType("");
      setParameterLabel("");
      setParameterValue("");
      setParameterUnit("");
      setCompatibilityNote("");
      await refreshInventory();
      setMessage("Позиция добавлена.");
    } catch {
      setMessage("Не удалось добавить позицию.");
    } finally {
      setLoading(false);
    }
  }

  async function submitCompatibility(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryPartCompatibilityPath(Number(compatibilityPartId))}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          compatibility_level: compatibilityLevel,
          brand: compatibilityBrand.trim() || undefined,
          model: compatibilityModel.trim() || undefined,
          series: compatibilitySeries.trim() || undefined,
          machine_family: compatibilityFamily.trim() || undefined,
          note: compatibilityRowNote.trim() || undefined,
        }),
      });
      ensureStaffResponse(response, "Compatibility");
      setCompatibilityPartId("");
      setCompatibilityLevel("exact_model");
      setCompatibilityBrand("");
      setCompatibilityModel("");
      setCompatibilitySeries("");
      setCompatibilityFamily("");
      setCompatibilityRowNote("");
      await refreshInventory();
      setMessage("Совместимость добавлена.");
    } catch {
      setMessage("Не удалось добавить совместимость.");
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
        body: JSON.stringify({
          quantity_on_hand: Number(stockCount),
          low_stock_threshold: lowStockThreshold ? Number(lowStockThreshold) : undefined,
        }),
      });
      ensureStaffResponse(response, "Stock update");
      setStockPartId("");
      setStockCount("0");
      setLowStockThreshold("");
      await refreshInventory();
      setMessage("Остаток обновлен.");
    } catch {
      setMessage("Не удалось обновить остаток.");
    } finally {
      setLoading(false);
    }
  }

  async function submitReservation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryReservationsPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          request_number: reservationRequest.trim(),
          part_id: Number(reservationPartId),
          quantity: Number(reservationQuantity),
          note: reservationNote.trim() || undefined,
        }),
      });
      ensureStaffResponse(response, "Reservation");
      setReservationRequest("");
      setReservationPartId("");
      setReservationQuantity("1");
      setReservationNote("");
      await refreshInventory();
      setMessage("Резерв создан.");
    } catch {
      setMessage("Не удалось создать резерв.");
    } finally {
      setLoading(false);
    }
  }

  async function releaseReservation(reservationId: number) {
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryReservationReleasePath(reservationId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({ note: "Released from inventory workspace" }),
      });
      ensureStaffResponse(response, "Release reservation");
      await refreshInventory();
      setMessage("Резерв снят.");
    } catch {
      setMessage("Не удалось снять резерв.");
    } finally {
      setLoading(false);
    }
  }

  async function submitSupplier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementSuppliersPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          name: supplierName.trim(),
          contact_name: supplierContact.trim() || undefined,
          phone: supplierPhone.trim() || undefined,
          email: supplierEmail.trim() || undefined,
          note: supplierNote.trim() || undefined,
        }),
      });
      ensureStaffResponse(response, "Create supplier");
      const createdSupplier = (await response.json()) as { supplier_id: number };
      setSupplierName("");
      setSupplierContact("");
      setSupplierPhone("");
      setSupplierEmail("");
      setSupplierNote("");
      setPurchaseSupplierId(String(createdSupplier.supplier_id));
      await refreshInventory();
      setMessage("Поставщик добавлен.");
    } catch {
      setMessage("Не удалось добавить поставщика.");
    } finally {
      setLoading(false);
    }
  }

  async function submitPurchaseRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementPurchaseRequestsPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({
          supplier_id: Number(purchaseSupplierId),
          items: [{ part_id: Number(purchasePartId), quantity: Number(purchaseQuantity), note: purchaseNote.trim() || undefined }],
          note: purchaseNote.trim() || undefined,
        }),
      });
      if (!response.ok) {
        ensureStaffResponse(response, "Create purchase request");
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail || `Create purchase request failed with ${response.status}`);
      }
      setPurchaseSupplierId("");
      setPurchasePartId("");
      setPurchaseQuantity("1");
      setPurchaseNote("");
      await refreshInventory();
      setMessage("Черновик закупки создан.");
    } catch {
      setMessage("Не удалось создать закупку.");
    } finally {
      setLoading(false);
    }
  }

  async function createLowStockDraft() {
    if (!purchaseSupplierId) {
      setMessage("Выберите поставщика для черновика закупки.");
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementLowStockDraftPath()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify({ supplier_id: Number(purchaseSupplierId), note: "Черновик из низких остатков" }),
      });
      if (!response.ok) {
        ensureStaffResponse(response, "Low-stock draft");
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail || `Low-stock draft failed with ${response.status}`);
      }
      await refreshInventory();
      setMessage("Черновик из низких остатков создан.");
    } catch (error) {
      const reason = error instanceof Error ? error.message : "";
      setMessage(reason.includes("No low-stock")
        ? "Низких остатков сейчас нет: черновик не создан."
        : "Не удалось создать черновик из низких остатков.");
    } finally {
      setLoading(false);
    }
  }

  async function runPurchaseAction(purchaseRequest: PurchaseRequest, path: string, successMessage: string, body: object = {}) {
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify(body),
      });
      ensureStaffResponse(response, "Purchase action");
      await refreshInventory();
      setMessage(`${successMessage}: PR-${purchaseRequest.purchase_request_id}.`);
    } catch {
      setMessage("Не удалось обновить закупку.");
    } finally {
      setLoading(false);
    }
  }

  async function submitDraftItems(event: FormEvent<HTMLFormElement>, purchaseRequest: PurchaseRequest) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildInventoryProcurementPurchaseRequestItemsPath(purchaseRequest.purchase_request_id)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
        body: JSON.stringify([{ part_id: Number(editPartId), quantity: Number(editQuantity), note: editNote.trim() || undefined }]),
      });
      ensureStaffResponse(response, "Draft item update");
      setEditPurchaseRequestId(null);
      setEditPartId("");
      setEditQuantity("1");
      setEditNote("");
      await refreshInventory();
      setMessage(`Строки PR-${purchaseRequest.purchase_request_id} обновлены.`);
    } catch {
      setMessage("Не удалось обновить строки закупки.");
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
              <span>{procurementOnly ? "Закупочный контур" : "Складской контур"}</span>
              <h1>{procurementOnly ? "Согласование закупок" : "Склад запчастей"}</h1>
              <p>
                {procurementOnly
                  ? "Поставщики, заявки на закупку, согласование и приемка."
                  : "Каталог, совместимость и базовые остатки для ремонтных выездов."}
              </p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void refreshInventory()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          <div className="inventory-workspace">
            {!procurementOnly ? (
            <section className="dispatcher-card inventory-table-card inventory-catalog-card compact-catalog">
              <div className="inventory-catalog-heading">
                <div>
                  <h2>Каталог</h2>
                  <p>Компактный список позиций, остатков и совместимости.</p>
                </div>
              </div>
              <div className="inventory-catalog-toolbar">
                <div className="inventory-catalog-metrics" aria-label="Сводка склада">
                  <span>{parts.items.length} позиций</span>
                  <span>{lowStockCount} низкий остаток</span>
                  <span>{reservedPartsCount} с резервом</span>
                </div>
                <div className="inventory-catalog-controls">
                  <input
                    value={inventorySearch}
                    onChange={(event) => {
                      setInventorySearch(event.target.value);
                      setInventoryPage(1);
                    }}
                    placeholder="Поиск по SKU, названию, бренду или совместимости"
                  />
                </div>
              </div>
              <div className="inventory-table">
                {paginatedParts.length ? (
                  paginatedParts.map((part) => (
                    <article key={part.part_id} className="inventory-part-card">
                      <div className="inventory-part-identity">
                        <strong>{part.sku}</strong>
                        <span>{part.name}</span>
                      </div>
                      <div className="inventory-part-stock">
                        <em>{formatInventoryQuantity(part.available_quantity, part.unit)}</em>
                        <small>Склад {part.quantity_on_hand} · Резерв {part.reserved_quantity}</small>
                        <small className={part.is_low_stock ? "inventory-low-stock" : undefined}>
                          Минимум: {part.low_stock_threshold ?? "не задан"}{part.is_low_stock ? " · низкий остаток" : ""}
                        </small>
                      </div>
                      <div className="inventory-part-model">
                        <strong>{[part.brand, part.model].filter(Boolean).join(" ") || "Без модели"}</strong>
                        <small>{buildInventoryPartSpecLabel(part)}</small>
                      </div>
                      {part.compatibility?.length ? (
                        <div className="inventory-compatibility-list">
                          {part.compatibility.slice(0, 2).map((item) => (
                            <small key={item.compatibility_id}>
                              {buildInventoryCompatibilityLabel(item)}
                            </small>
                          ))}
                          {part.compatibility.length > 2 ? <small>+{part.compatibility.length - 2}</small> : null}
                        </div>
                      ) : null}
                      <details className="inventory-part-details">
                        <summary>Подробности</summary>
                        <dl>
                          <div>
                            <dt>Модель/бренд</dt>
                            <dd>{[part.brand, part.model].filter(Boolean).join(" ") || "Без привязки к модели"}</dd>
                          </div>
                          <div>
                            <dt>Характеристика</dt>
                            <dd>{buildInventoryPartSpecLabel(part)}</dd>
                          </div>
                          {part.compatibility_note ? (
                            <div>
                              <dt>Комментарий</dt>
                              <dd>{part.compatibility_note}</dd>
                            </div>
                          ) : null}
                          {part.stock_updated_at ? (
                            <div>
                              <dt>Обновлено</dt>
                              <dd><time dateTime={part.stock_updated_at}>{formatCompactDateTime(part.stock_updated_at)}</time></dd>
                            </div>
                          ) : null}
                        </dl>
                      </details>
                    </article>
                  ))
                ) : (
                  <p>{parts.items.length ? "По этому поиску позиций нет." : "Каталог пока пуст."}</p>
                )}
              </div>
              <div className="inventory-catalog-footer">
                <strong>{inventoryRangeLabel}</strong>
                <div className="inventory-page-size-control" aria-label="Количество позиций на странице">
                  <span>На странице</span>
                  {inventoryCatalogPageSizes.map((pageSize) => (
                    <button
                      aria-label={`Показывать ${pageSize} позиций`}
                      className={inventoryPageSize === pageSize ? "active" : undefined}
                      key={pageSize}
                      onClick={() => {
                        setInventoryPageSize(pageSize);
                        setInventoryPage(1);
                      }}
                      type="button"
                    >
                      {pageSize}
                    </button>
                  ))}
                </div>
                <div className="inventory-pagination-bar" aria-label="Пагинация каталога">
                  <button
                    className="secondary-status-button"
                    disabled={currentInventoryPage <= 1}
                    onClick={() => setInventoryPage((page) => Math.max(1, page - 1))}
                    type="button"
                  >
                    Предыдущая
                  </button>
                  <span>
                    Страница {currentInventoryPage} из {inventoryTotalPages}
                  </span>
                  <button
                    className="secondary-status-button"
                    disabled={currentInventoryPage >= inventoryTotalPages}
                    onClick={() => setInventoryPage((page) => Math.min(inventoryTotalPages, page + 1))}
                    type="button"
                  >
                    Следующая
                  </button>
                </div>
              </div>
            </section>
            ) : null}
            {!procurementOnly && isInventoryStaff ? (
            <section className="dispatcher-card inventory-actions-card">
              <div className="inventory-actions-heading">
                <div>
                  <h2>Складские действия</h2>
                  <p>Редкие операции свернуты, чтобы каталог оставался главным рабочим экраном.</p>
                </div>
              </div>
              <div className="inventory-action-stack">
                <details className="inventory-action-panel">
                  <summary>
                    <span>Добавить позицию</span>
                    <small>Новая запчасть, стартовый остаток и минимум.</small>
                  </summary>
              <form className="dispatcher-form" onSubmit={submitPart}>
                <label className="form-field">
                  <span>Артикул / SKU</span>
                  <input
                    value={sku}
                    onChange={(event) => {
                      setSkuEdited(true);
                      setSku(event.target.value);
                    }}
                    placeholder={suggestedSku || "Например: GAGGIA-CLASSIC-GASKET-MODEL-4-MM"}
                    required
                  />
                  <small>
                    Уникальный внутренний код позиции. Заполняется автоматически из полей ниже, можно поправить вручную.
                    Например: GAGGIA-CLASSIC-GASKET-MODEL-4-MM.
                  </small>
                </label>
                <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Название" required />
                <input value={brand} onChange={(event) => setBrand(event.target.value)} placeholder="Бренд" list="inventory-brand-options" />
                <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="Модель" list="inventory-model-options" />
                <input value={partType} onChange={(event) => setPartType(event.target.value)} placeholder="Тип детали" list="inventory-part-type-options" />
                <input
                  value={parameterLabel}
                  onChange={(event) => setParameterLabel(event.target.value)}
                  placeholder="Ключевой параметр"
                  list="inventory-parameter-label-options"
                />
                <input value={parameterValue} onChange={(event) => setParameterValue(event.target.value)} placeholder="Значение параметра" />
                <input
                  value={parameterUnit}
                  onChange={(event) => setParameterUnit(event.target.value)}
                  placeholder="Единица параметра"
                  list="inventory-parameter-unit-options"
                />
                <label className="form-field">
                  <span>Единица учета</span>
                  <input value={unit} onChange={(event) => setUnit(event.target.value)} placeholder="pcs, kit, set" list="inventory-unit-options" required />
                  <small>Как считать позицию на складе: штуки, комплект, набор. Не количество.</small>
                </label>
                <label className="form-field">
                  <span>Начальный остаток</span>
                  <input
                    value={initialStockCount}
                    onChange={(event) => setInitialStockCount(event.target.value)}
                    placeholder="0"
                    type="number"
                    min="0"
                    required
                  />
                </label>
                <label className="form-field">
                  <span>Минимум на складе</span>
                  <input
                    value={initialLowStockThreshold}
                    onChange={(event) => setInitialLowStockThreshold(event.target.value)}
                    placeholder="Например: 2"
                    type="number"
                    min="0"
                  />
                </label>
                <input
                  value={compatibilityNote}
                  onChange={(event) => setCompatibilityNote(event.target.value)}
                  placeholder="Комментарий по совместимости"
                />
                {duplicatePart ? (
                  <p className="inventory-warning">
                    Такая фактическая запчасть уже есть в каталоге: {duplicatePart.sku} · {duplicatePart.name}
                  </p>
                ) : null}
                <datalist id="inventory-brand-options">
                  {brandOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-model-options">
                  {modelOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-part-type-options">
                  {partTypeOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-parameter-label-options">
                  {parameterLabelOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-parameter-unit-options">
                  {parameterUnitOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-unit-options">
                  <option value="pcs" />
                  <option value="kit" />
                  <option value="set" />
                  <option value="m" />
                  <option value="ml" />
                </datalist>
                <button className="submit-button" type="submit" disabled={loading || Boolean(duplicatePart)}>Добавить позицию</button>
              </form>
                </details>
                <details className="inventory-action-panel">
                  <summary>
                    <span>Добавить совместимость</span>
                    <small>Привязка детали к модели, серии или узлу.</small>
                  </summary>
              <form className="dispatcher-form" onSubmit={submitCompatibility}>
                <select value={compatibilityPartId} onChange={(event) => setCompatibilityPartId(event.target.value)} required>
                  <option value="">Позиция каталога</option>
                  {parts.items.map((part) => (
                    <option key={part.part_id} value={part.part_id}>
                      {part.sku} · {part.name}
                    </option>
                  ))}
                </select>
                <select
                  value={compatibilityLevel}
                  onChange={(event) => setCompatibilityLevel(event.target.value as InventoryCompatibilityLevel)}
                  required
                >
                  <option value="exact_model">Точная модель</option>
                  <option value="series">Серия</option>
                  <option value="generic_group">Узел / группа машин</option>
                </select>
                <input
                  value={compatibilityBrand}
                  onChange={(event) => setCompatibilityBrand(event.target.value)}
                  placeholder="Бренд"
                  list="inventory-brand-options"
                  required={compatibilityLevel === "exact_model"}
                />
                <input
                  value={compatibilityModel}
                  onChange={(event) => setCompatibilityModel(event.target.value)}
                  placeholder="Модель"
                  list="inventory-model-options"
                  required={compatibilityLevel === "exact_model"}
                />
                <input
                  value={compatibilitySeries}
                  onChange={(event) => setCompatibilitySeries(event.target.value)}
                  placeholder="Серия"
                  list="inventory-compatibility-series-options"
                  required={compatibilityLevel === "series"}
                />
                <input
                  value={compatibilityFamily}
                  onChange={(event) => setCompatibilityFamily(event.target.value)}
                  placeholder="Узел / группа"
                  list="inventory-compatibility-family-options"
                  required={compatibilityLevel === "generic_group"}
                />
                <input
                  value={compatibilityRowNote}
                  onChange={(event) => setCompatibilityRowNote(event.target.value)}
                  placeholder="Условие или примечание"
                />
                <datalist id="inventory-compatibility-series-options">
                  {compatibilitySeriesOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <datalist id="inventory-compatibility-family-options">
                  {compatibilityFamilyOptions.map((option) => <option key={option} value={option} />)}
                </datalist>
                <button className="submit-button" type="submit" disabled={loading}>Добавить совместимость</button>
              </form>
                </details>
                <details className="inventory-action-panel">
                  <summary>
                    <span>Обновить остаток</span>
                    <small>Корректировка количества и минимального порога.</small>
                  </summary>
              <form className="dispatcher-form compact-form" onSubmit={submitStock}>
                <select value={stockPartId} onChange={(event) => setStockPartId(event.target.value)} required>
                  <option value="">Позиция для остатка</option>
                  {parts.items.map((part) => (
                    <option key={part.part_id} value={part.part_id}>
                      {part.sku} · {part.name} · сейчас {formatInventoryQuantity(part.quantity_on_hand, part.unit)}
                    </option>
                  ))}
                </select>
	                <input value={stockCount} onChange={(event) => setStockCount(event.target.value)} placeholder="Остаток" type="number" min="0" required />
	                <input value={lowStockThreshold} onChange={(event) => setLowStockThreshold(event.target.value)} placeholder="Минимум" type="number" min="0" />
	                <button className="submit-button" type="submit">Обновить остаток</button>
	              </form>
                </details>
                <details className="inventory-action-panel">
                  <summary>
                    <span>Создать резерв</span>
                    <small>Закрепить запчасть под конкретную заявку.</small>
                  </summary>
	              <form className="dispatcher-form compact-form" onSubmit={submitReservation}>
	                <input value={reservationRequest} onChange={(event) => setReservationRequest(event.target.value)} placeholder="Номер заявки" required />
	                <select value={reservationPartId} onChange={(event) => setReservationPartId(event.target.value)} required>
	                  <option value="">Позиция для резерва</option>
	                  {parts.items.map((part) => (
	                    <option key={part.part_id} value={part.part_id}>
	                      {part.sku} · {part.name} · доступно {formatInventoryQuantity(part.available_quantity, part.unit)}
	                    </option>
	                  ))}
	                </select>
	                <input value={reservationQuantity} onChange={(event) => setReservationQuantity(event.target.value)} placeholder="Количество" type="number" min="1" required />
	                <input value={reservationNote} onChange={(event) => setReservationNote(event.target.value)} placeholder="Заметка" />
	                <button className="submit-button" type="submit">Создать резерв</button>
	              </form>
                </details>
              </div>
	            </section>
            ) : null}
            {procurementOnly ? (
            <section className="dispatcher-card inventory-procurement-card" id="procurement">
              <div className="inventory-actions-heading procurement-command-heading">
                <div>
                  <h2>Рабочий поток закупок</h2>
                  <p>Черновик, согласование, заказ и приемка в одном кабинете.</p>
                </div>
                <div className="inventory-catalog-metrics procurement-command-metrics">
                  <span>{suppliers.items.length} поставщиков</span>
                  <span>{purchaseRequests.items.length} заявок</span>
                  <span>{lowStockCount} низкий остаток</span>
                </div>
              </div>
              <div className="procurement-layout">
                <details className="procurement-suppliers-panel">
                  <summary>
                    <span>Поставщики</span>
                    <small>{suppliers.items.length ? `${suppliers.items.length} в справочнике` : "Справочник пуст"}</small>
                  </summary>
                  <div className="procurement-suppliers-body">
                    <div className="compact-inventory-list inventory-table procurement-supplier-list">
                      {suppliers.items.length ? (
                        suppliers.items.map((supplier) => (
                          <article key={supplier.supplier_id}>
                            <strong>{supplier.name}</strong>
                            <span>{supplier.contact_name ?? "Контакт не указан"}</span>
                            <small>{supplier.phone ?? supplier.email ?? "Без связи"}</small>
                            <em>{supplier.active ? "активен" : "выключен"}</em>
                          </article>
                        ))
                      ) : (
                        <p>Поставщики пока не добавлены.</p>
                      )}
                    </div>
                    {isInventoryStaff ? (
                      <form className="dispatcher-form compact-form procurement-form procurement-supplier-form" onSubmit={submitSupplier}>
                        <input value={supplierName} onChange={(event) => setSupplierName(event.target.value)} placeholder="Название поставщика" required />
                        <input value={supplierContact} onChange={(event) => setSupplierContact(event.target.value)} placeholder="Контакт" />
                        <input value={supplierPhone} onChange={(event) => setSupplierPhone(event.target.value)} placeholder="Телефон" />
                        <input value={supplierEmail} onChange={(event) => setSupplierEmail(event.target.value)} placeholder="Email" />
                        <input className="wide-field" value={supplierNote} onChange={(event) => setSupplierNote(event.target.value)} placeholder="Заметка" />
                        <button className="submit-button" type="submit" disabled={loading}>
                          <FilePlus2 aria-hidden="true" />
                          Добавить поставщика
                        </button>
                      </form>
                    ) : null}
                  </div>
                </details>
                <section className="procurement-panel procurement-draft-panel">
                  <div>
                    <h3>Новый черновик</h3>
                    <p>Выберите поставщика один раз, затем создайте заявку вручную или из текущих низких остатков.</p>
                  </div>
                  {isInventoryStaff ? (
                    <div className="procurement-draft-stack">
                      <form className="dispatcher-form compact-form procurement-form" onSubmit={submitPurchaseRequest}>
                        <select value={purchaseSupplierId} onChange={(event) => setPurchaseSupplierId(event.target.value)} required>
                          <option value="">Поставщик</option>
                          {suppliers.items.map((supplier) => (
                            <option key={supplier.supplier_id} value={supplier.supplier_id}>{supplier.name}</option>
                          ))}
                        </select>
                        <select value={purchasePartId} onChange={(event) => setPurchasePartId(event.target.value)} required>
                          <option value="">Запчасть</option>
                          {parts.items.map((part) => (
                            <option key={part.part_id} value={part.part_id}>
                              {part.sku} · {part.name} · доступно {formatInventoryQuantity(part.available_quantity, part.unit)}
                            </option>
                          ))}
                        </select>
                        <input value={purchaseQuantity} onChange={(event) => setPurchaseQuantity(event.target.value)} placeholder="Количество" type="number" min="1" required />
                        <input value={purchaseNote} onChange={(event) => setPurchaseNote(event.target.value)} placeholder="Комментарий" />
                        <div className="procurement-draft-actions">
                          <button className="submit-button" type="submit" disabled={loading}>
                            <FilePlus2 aria-hidden="true" />
                            Создать черновик
                          </button>
                          <button
                            className="secondary-status-button procurement-low-stock-button"
                            type="button"
                            onClick={() => void createLowStockDraft()}
                            disabled={loading || !suppliers.items.length}
                          >
                            <PackageCheck aria-hidden="true" />
                            Создать из низких остатков
                          </button>
                        </div>
                      </form>
                      <small>
                        {purchaseSupplierId
                          ? lowStockCount
                            ? `Будут взяты позиции с низким остатком: ${lowStockCount}.`
                            : "Если низких остатков нет, система покажет понятное сообщение."
                          : "Сначала выберите поставщика."}
                      </small>
                    </div>
                  ) : (
                    <p>Создание закупок доступно роли inventory.</p>
                  )}
                </section>
                <section className="procurement-panel procurement-requests-panel">
                  <div className="procurement-board-heading">
                    <div>
                      <h3>Заявки на закупку</h3>
                      <p>Карточки показывают текущий статус и доступное следующее действие.</p>
                    </div>
                  </div>
                  <div className="procurement-board procurement-request-list">
                    {purchaseRequests.items.length ? (
                      purchaseRequests.items.map((request) => (
                        <article key={request.purchase_request_id} className="procurement-request-card">
                          <div className="procurement-request-main">
                            <div>
                              <strong>PR-{request.purchase_request_id}</strong>
                              <small>{request.supplier_name}</small>
                            </div>
                            <span>{request.items.map((item) => `${item.sku} x ${item.quantity}`).join(", ")}</span>
                          </div>
                          <em className={`procurement-status-badge ${procurementStatusTones[request.status]}`}>
                            {procurementStatusLabels[request.status]}
                          </em>
                          <div className="procurement-actions">
                            {isInventoryStaff && request.status === "draft" ? (
                              <button
                                className="secondary-status-button procurement-primary-action"
                                type="button"
                                onClick={() => void runPurchaseAction(request, buildInventoryProcurementPurchaseRequestSubmitPath(request.purchase_request_id), "Отправлено на согласование")}
                                disabled={loading}
                              >
                                <Send aria-hidden="true" />
                                Отправить на согласование
                              </button>
                            ) : null}
                            {isAdminStaff && request.status === "pending_approval" ? (
                              <button
                                className="secondary-status-button procurement-primary-action"
                                type="button"
                                onClick={() => void runPurchaseAction(request, buildInventoryProcurementPurchaseRequestApprovePath(request.purchase_request_id), "Согласовано")}
                                disabled={loading}
                              >
                                <CheckCircle2 aria-hidden="true" />
                                Согласовать
                              </button>
                            ) : null}
                            {isInventoryStaff && request.status === "approved" ? (
                              <button
                                className="secondary-status-button procurement-primary-action"
                                type="button"
                                onClick={() => void runPurchaseAction(request, buildInventoryProcurementPurchaseRequestMarkOrderedPath(request.purchase_request_id), "Отмечено заказанным")}
                                disabled={loading}
                              >
                                <Truck aria-hidden="true" />
                                Отметить заказанным
                              </button>
                            ) : null}
                            {isInventoryStaff && request.status === "ordered" ? (
                              <button
                                className="secondary-status-button procurement-primary-action"
                                type="button"
                                onClick={() => void runPurchaseAction(request, buildInventoryProcurementPurchaseRequestReceivePath(request.purchase_request_id), "Принято на склад", { note: "Принято из интерфейса склада" })}
                                disabled={loading}
                              >
                                <PackageCheck aria-hidden="true" />
                                Принять на склад
                              </button>
                            ) : null}
                            {isInventoryStaff && ["draft", "pending_approval", "approved", "ordered"].includes(request.status) ? (
                              <button
                                className="secondary-status-button procurement-danger-action"
                                type="button"
                                onClick={() => void runPurchaseAction(request, buildInventoryProcurementPurchaseRequestCancelPath(request.purchase_request_id), "Отменено")}
                                disabled={loading}
                              >
                                <XCircle aria-hidden="true" />
                                Отменить заявку
                              </button>
                            ) : null}
                            {request.status === "received" || request.status === "cancelled" ? (
                              <span className="procurement-terminal-action">
                                <CircleSlash aria-hidden="true" />
                                Действий нет
                              </span>
                            ) : null}
                          </div>
                          {isInventoryStaff && request.status === "draft" ? (
                            <form className="dispatcher-form compact-form procurement-edit-form" onSubmit={(event) => submitDraftItems(event, request)}>
                              <select
                                value={editPurchaseRequestId === request.purchase_request_id ? editPartId : ""}
                                onChange={(event) => {
                                  setEditPurchaseRequestId(request.purchase_request_id);
                                  setEditPartId(event.target.value);
                                }}
                                required
                              >
                                <option value="">Строка для замены</option>
                                {parts.items.map((part) => (
                                  <option key={part.part_id} value={part.part_id}>
                                    {part.sku} · {part.name}
                                  </option>
                                ))}
                              </select>
                              <input
                                value={editPurchaseRequestId === request.purchase_request_id ? editQuantity : "1"}
                                onChange={(event) => {
                                  setEditPurchaseRequestId(request.purchase_request_id);
                                  setEditQuantity(event.target.value);
                                }}
                                placeholder="Количество"
                                type="number"
                                min="1"
                                required
                              />
                              <input
                                value={editPurchaseRequestId === request.purchase_request_id ? editNote : ""}
                                onChange={(event) => {
                                  setEditPurchaseRequestId(request.purchase_request_id);
                                  setEditNote(event.target.value);
                                }}
                                placeholder="Заметка к строке"
                              />
                              <button className="secondary-status-button" type="submit" disabled={loading}>
                                <PackageCheck aria-hidden="true" />
                                Заменить строки
                              </button>
                            </form>
                          ) : null}
                        </article>
                      ))
                    ) : (
                      <p>Заявок на закупку пока нет.</p>
                    )}
                  </div>
                </section>
              </div>
            </section>
            ) : null}
	            {!procurementOnly && isInventoryStaff ? (
	            <section className="dispatcher-card">
	              <h2>Активные резервы</h2>
	              <div className="inventory-table compact-inventory-list">
	                {reservations.items.length ? (
	                  reservations.items.map((reservation) => (
	                    <article key={reservation.reservation_id}>
	                      <strong>{reservation.request_number}</strong>
	                      <span>{reservation.part_name}</span>
	                      <em>{reservation.quantity} · {reservation.status}</em>
	                      {reservation.status === "active" ? (
	                        <button className="secondary-status-button" type="button" onClick={() => void releaseReservation(reservation.reservation_id)} disabled={loading}>
	                          Снять резерв
	                        </button>
	                      ) : null}
	                    </article>
	                  ))
	                ) : (
	                  <p>Активных резервов нет.</p>
	                )}
	              </div>
	            </section>
	            ) : null}
	            {!procurementOnly && isInventoryStaff ? (
	            <section className="dispatcher-card inventory-table-card">
	              <h2>Движения склада</h2>
	              <div className="inventory-table compact-inventory-list">
	                {movements.items.length ? (
	                  movements.items.slice(0, 8).map((movement) => (
	                    <article key={movement.movement_id}>
	                      <strong>{inventoryMovementLabel(movement.movement_type)}</strong>
	                      <span>{movement.part_name}</span>
	                      <small>{movement.request_number ?? "Без заявки"}</small>
	                      <em>
	                        {movement.quantity > 0 ? "+" : ""}{movement.quantity} · доступно {movement.available_quantity_after}
	                      </em>
	                    </article>
	                  ))
	                ) : (
	                  <p>Движений пока нет.</p>
	                )}
	              </div>
	            </section>
	            ) : null}
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
  initialSuppliers,
  initialPurchaseRequests,
  procurementOnly = false,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialParts?: InventoryPartListResponse;
  initialSuppliers?: ProcurementSupplierListResponse;
  initialPurchaseRequests?: PurchaseRequestListResponse;
  procurementOnly?: boolean;
}) {
  const cabinetPath = procurementOnly ? "/procurement" : "/inventory";

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
    if ((!stored || (!staffHasRole(stored, "inventory") && !staffHasRole(stored, "admin"))) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(window.location.pathname);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath(cabinetPath);
  }

  if (!staffHasRole(session, "inventory") && !staffHasRole(session, "admin")) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>
                {isAuthenticated
                  ? procurementOnly
                    ? "Для закупок нужна роль inventory или admin."
                    : "Для склада нужна роль inventory или admin."
                  : procurementOnly
                    ? "Закупки находятся во внутреннем контуре."
                    : "Склад находится во внутреннем контуре."}
              </p>
              <a className="submit-button" href={buildStaffLoginPath(cabinetPath)}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <InventoryPage
      session={session}
      onLogout={logout}
      initialParts={initialParts}
      initialSuppliers={initialSuppliers}
      initialPurchaseRequests={initialPurchaseRequests}
      procurementOnly={procurementOnly}
    />
  );
}

export function ProtectedProcurementPage(props: Omit<Parameters<typeof ProtectedInventoryPage>[0], "procurementOnly">) {
  return <ProtectedInventoryPage {...props} procurementOnly />;
}

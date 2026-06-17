import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { LogIn, Shield } from "lucide-react";

import {
  apiBaseUrl,
  buildInventoryMovementsPath,
  buildInventoryPartCompatibilityPath,
  buildInventoryPartsPath,
  buildInventoryReservationReleasePath,
  buildInventoryReservationsPath,
  buildInventoryStockPath,
} from "../../shared/api";
import { buildInventoryCompatibilityLabel, buildInventoryPartSpecLabel, formatCompactDateTime, formatInventoryQuantity, inventoryMovementLabel } from "../../shared/formatters";
import { buildInventoryFactualKey, buildInventorySkuSuggestion, inventoryPartSearchText, normalizeInventoryIdentity, uniqueInventoryValues } from "../../shared/inventory";
import { buildStaffLoginPath, clearStaffSession, getStoredStaffSession, staffAuthHeaders, staffHasRole } from "../../shared/staffAuth";
import type {
  InventoryCompatibilityLevel,
  InventoryMovementListResponse,
  InventoryPartItem,
  InventoryPartListResponse,
  InventoryReservationListResponse,
  StaffSession,
} from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

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
  const [reservations, setReservations] = useState<InventoryReservationListResponse>({ items: [] });
  const [movements, setMovements] = useState<InventoryMovementListResponse>({ items: [] });
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
  const [inventorySearch, setInventorySearch] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
  const lowStockCount = parts.items.filter((part) => part.is_low_stock).length;
  const reservedPartsCount = parts.items.filter((part) => part.reserved_quantity > 0).length;

  async function loadParts() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryPartsPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Inventory parts failed with ${response.status}`);
    const body = (await response.json()) as InventoryPartListResponse;
    setParts(body);
  }

  async function loadReservations() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryReservationsPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Inventory reservations failed with ${response.status}`);
    const body = (await response.json()) as InventoryReservationListResponse;
    setReservations(body);
  }

  async function loadMovements() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryMovementsPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Inventory movements failed with ${response.status}`);
    const body = (await response.json()) as InventoryMovementListResponse;
    setMovements(body);
  }

  async function refreshInventory() {
    await Promise.all([loadParts(), loadReservations(), loadMovements()]);
  }

  useEffect(() => {
    if (initialParts) return;
    void refreshInventory().catch(() => setMessage("Не удалось загрузить склад."));
  }, [initialParts]);

  useEffect(() => {
    if (skuEdited) return;
    setSku(suggestedSku);
  }, [skuEdited, suggestedSku]);

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
      if (!response.ok) throw new Error(`Create part failed with ${response.status}`);
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
        if (!stockResponse.ok) throw new Error(`Initial stock failed with ${stockResponse.status}`);
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
      if (!response.ok) throw new Error(`Compatibility failed with ${response.status}`);
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
      if (!response.ok) throw new Error(`Stock update failed with ${response.status}`);
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
      if (!response.ok) throw new Error(`Reservation failed with ${response.status}`);
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
      if (!response.ok) throw new Error(`Release reservation failed with ${response.status}`);
      await refreshInventory();
      setMessage("Резерв снят.");
    } catch {
      setMessage("Не удалось снять резерв.");
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
            <button className="secondary-status-button" type="button" onClick={() => void refreshInventory()} disabled={loading}>
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>
          {message ? <p className="status-message">{message}</p> : null}
          <div className="inventory-workspace">
            <section className="dispatcher-card inventory-table-card">
              <h2>Каталог</h2>
              <div className="inventory-catalog-toolbar">
                <div className="inventory-catalog-metrics" aria-label="Сводка склада">
                  <span>{parts.items.length} позиций</span>
                  <span>{lowStockCount} низкий остаток</span>
                  <span>{reservedPartsCount} с резервом</span>
                </div>
                <input
                  value={inventorySearch}
                  onChange={(event) => setInventorySearch(event.target.value)}
                  placeholder="Поиск по SKU, названию, бренду или совместимости"
                />
              </div>
              <div className="inventory-table">
                {visibleParts.length ? (
                  visibleParts.map((part) => (
                    <article key={part.part_id} className="inventory-part-card">
                      <div className="inventory-part-identity">
                        <strong>{part.sku}</strong>
                        <span>{part.name}</span>
                      </div>
                      <div className="inventory-part-stock">
                        <em>Доступно: {formatInventoryQuantity(part.available_quantity, part.unit)}</em>
                        <small>На складе: {part.quantity_on_hand} · Резерв: {part.reserved_quantity}</small>
                        <small className={part.is_low_stock ? "inventory-low-stock" : undefined}>
                          Минимум: {part.low_stock_threshold ?? "не задан"}{part.is_low_stock ? " · низкий остаток" : ""}
                        </small>
                      </div>
                      {part.compatibility?.length ? (
                        <div className="inventory-compatibility-list">
                          <strong>Совместимость</strong>
                          {part.compatibility.map((item) => (
                            <small key={item.compatibility_id}>
                              {buildInventoryCompatibilityLabel(item)}
                            </small>
                          ))}
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
            </section>
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

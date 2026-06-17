import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { CheckSquare, Droplets, Eye, LogIn, Monitor, Shield } from "lucide-react";

import {
  apiBaseUrl,
  buildInventoryPartsPath,
  buildTechnicianDetailPath,
  buildTechnicianDiagnosisPath,
  buildTechnicianListPath,
  buildTechnicianPartsUsedPath,
  buildTechnicianResultPath,
  buildTechnicianSchedulePath,
} from "../../shared/api";
import { appointmentStatusLabel, formatInventoryQuantity, statusLabel, urgencyLabel } from "../../shared/formatters";
import { inventoryPartSearchText, partMatchesMachine } from "../../shared/inventory";
import { buildStaffLoginPath, clearStaffSession, getStoredStaffSession, staffAuthHeaders, staffHasRole } from "../../shared/staffAuth";
import type { InventoryPartListResponse, ScheduleListResponse, StaffSession, TechnicianListResponse, TechnicianRequestDetail } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

export function TechnicianPage({
  initialList,
  initialDetail,
  initialSchedule,
  initialParts,
  session,
  onLogout,
}: {
  initialList?: TechnicianListResponse;
  initialDetail?: TechnicianRequestDetail;
  initialSchedule?: ScheduleListResponse;
  initialParts?: InventoryPartListResponse;
  session?: StaffSession | null;
  onLogout?: () => void;
}) {
  const [list, setList] = useState<TechnicianListResponse>(initialList ?? { items: [] });
  const [schedule, setSchedule] = useState<ScheduleListResponse>(initialSchedule ?? { items: [] });
  const [parts, setParts] = useState<InventoryPartListResponse>(initialParts ?? { items: [] });
  const [selected, setSelected] = useState(initialDetail?.request_number ?? initialList?.items[0]?.request_number ?? "");
  const [detail, setDetail] = useState<TechnicianRequestDetail | null>(initialDetail ?? null);
  const [diagnosisSummary, setDiagnosisSummary] = useState("");
  const [resultSummary, setResultSummary] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [partId, setPartId] = useState("");
  const [partQuantity, setPartQuantity] = useState("1");
  const [partNote, setPartNote] = useState("");
  const [partSearch, setPartSearch] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const selectedPart = parts.items.find((part) => String(part.part_id) === partId);
  const matchingParts = detail ? parts.items.filter((part) => partMatchesMachine(part, detail.machine_label)) : [];
  const trimmedPartSearch = partSearch.trim().toLowerCase();
  const filteredParts = trimmedPartSearch
    ? parts.items.filter((part) => inventoryPartSearchText(part).includes(trimmedPartSearch))
    : matchingParts;
  const selectorParts = filteredParts.length ? filteredParts : parts.items;

  async function loadList() {
    const response = await fetch(`${apiBaseUrl()}${buildTechnicianListPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Technician list failed with ${response.status}`);
    const body = (await response.json()) as TechnicianListResponse;
    setList(body);
    if (!selected && body.items[0]) setSelected(body.items[0].request_number);
    return body;
  }

  async function loadSchedule() {
    const response = await fetch(`${apiBaseUrl()}${buildTechnicianSchedulePath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Technician schedule failed with ${response.status}`);
    const body = (await response.json()) as ScheduleListResponse;
    setSchedule(body);
    return body;
  }

  async function loadParts() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryPartsPath()}`, { headers: staffAuthHeaders(session) });
    if (!response.ok) throw new Error(`Technician parts catalog failed with ${response.status}`);
    const body = (await response.json()) as InventoryPartListResponse;
    setParts(body);
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
      await Promise.all([loadList(), loadSchedule(), loadParts()]);
      if (requestNumber) await loadDetail(requestNumber);
    } catch {
      setMessage("Не удалось обновить выезды мастера.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialList || initialDetail || initialSchedule || initialParts) return;
    void refresh();
  }, [initialList, initialDetail, initialSchedule, initialParts]);

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
              <div className="schedule-panel technician-schedule-panel" aria-label="Мое расписание">
                <div className="schedule-panel-heading">
                  <strong>Мое расписание</strong>
                  <span>{schedule.items.length}</span>
                </div>
                {schedule.items.length ? (
                  schedule.items.map((item) => (
                    <button
                      className="schedule-row"
                      key={item.appointment.appointment_id}
                      type="button"
                      onClick={() => setSelected(item.appointment.request_number)}
                    >
                      <span>{item.appointment.window_label}</span>
                      <strong>{appointmentStatusLabel(item.appointment.status)}</strong>
                      <small>{item.appointment.request_number}</small>
                      <em>{item.customer_name} · {item.address}</em>
                    </button>
                  ))
                ) : (
                  <p className="dispatcher-empty">Запланированных окон нет.</p>
                )}
              </div>
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
                    <small>{item.appointment?.window_label ?? item.visit_window ?? item.latest_event_title}</small>
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
                      <dd>{detail.appointment?.window_label ?? detail.visit_window ?? "Не указано"}</dd>
                    </div>
                    {detail.appointment ? (
                      <div>
                        <dt>Состояние визита</dt>
                        <dd>{appointmentStatusLabel(detail.appointment.status)}</dd>
                      </div>
                    ) : null}
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
                    {!parts.items.length ? (
                      <p>Каталог запчастей пока недоступен.</p>
                    ) : null}
                    <form className="dispatcher-form compact-form" onSubmit={submitPartsUsed}>
                      <input
                        className="wide-field"
                        value={partSearch}
                        onChange={(event) => setPartSearch(event.target.value)}
                        placeholder="Поиск по SKU, названию или бренду"
                      />
                      {matchingParts.length ? (
                        <div className="technician-parts-preview wide-field">
                          <strong>Подходит к этой машине</strong>
                          {matchingParts.slice(0, 4).map((part) => (
                            <button key={part.part_id} type="button" onClick={() => setPartId(String(part.part_id))}>
                              {part.sku} · {part.name} · доступно {formatInventoryQuantity(part.available_quantity, part.unit)}
                            </button>
                          ))}
                        </div>
                      ) : (
                        <p className="wide-field technician-part-hint">Совместимых позиций для этой машины пока нет. Используйте поиск по каталогу.</p>
                      )}
                      <select className="wide-field" value={partId} onChange={(event) => setPartId(event.target.value)} required>
                        <option value="">{trimmedPartSearch ? "Результаты поиска" : "Запчасть из каталога"}</option>
                        {selectorParts.map((part) => (
                          <option key={part.part_id} value={part.part_id}>
                            {part.sku} · {part.name}
                          </option>
                        ))}
                      </select>
                      <input value={partQuantity} onChange={(event) => setPartQuantity(event.target.value)} placeholder="Количество" required type="number" min="1" />
                      <input className="wide-field" value={partNote} onChange={(event) => setPartNote(event.target.value)} placeholder="Комментарий" />
                      {selectedPart ? (
                        <small className="technician-part-stock">
                          Доступно: {formatInventoryQuantity(selectedPart.available_quantity, selectedPart.unit)} · резерв: {selectedPart.reserved_quantity}
                        </small>
                      ) : null}
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
  initialSchedule,
  initialParts,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialList?: TechnicianListResponse;
  initialDetail?: TechnicianRequestDetail;
  initialSchedule?: ScheduleListResponse;
  initialParts?: InventoryPartListResponse;
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

  return (
    <TechnicianPage
      session={session}
      onLogout={logout}
      initialList={initialList}
      initialDetail={initialDetail}
      initialSchedule={initialSchedule}
      initialParts={initialParts}
    />
  );
}

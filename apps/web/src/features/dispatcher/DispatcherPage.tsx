import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Clock, Droplets, Eye, HelpCircle, LogIn, Monitor, Send, Shield } from "lucide-react";

import {
  apiBaseUrl,
  buildAcceptAiClarificationPath,
  buildDispatcherAppointmentCancelPath,
  buildDispatcherAppointmentPath,
  buildDispatcherAppointmentReschedulePath,
  buildDispatcherAssignmentPath,
  buildDispatcherClarificationPath,
  buildDispatcherDetailPath,
  buildDispatcherInternalNotePath,
  buildDispatcherListPath,
  buildDispatcherSchedulePath,
  buildDispatcherStatusPath,
  buildDispatcherTechnicianCandidatesPath,
  buildGenerateAiSuggestionsPath,
  buildIgnoreAiSuggestionPath,
  buildInventoryLowStockPath,
} from "../../shared/api";
import { aiSuggestionKindLabel, aiSuggestionStatusLabel, appointmentStatusLabel, formatCompactDateTime, formatInventoryQuantity, statusLabel, toApiDateTime, urgencyLabel } from "../../shared/formatters";
import { urgencies } from "../../shared/options";
import {
  buildStaffLoginPath,
  clearStaffSession,
  getStoredStaffSession,
  isStaffAuthFailureStatus,
  staffAuthHeaders,
  staffHasRole,
} from "../../shared/staffAuth";
import type {
  DispatcherListItem,
  DispatcherListResponse,
  DispatcherRequestDetail,
  DispatcherStatusFilter,
  DispatcherUrgencyFilter,
  InventoryPartListResponse,
  RequestStatus,
  ScheduleListResponse,
  StaffSession,
  TechnicianCandidate,
  TechnicianCandidateListResponse,
} from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

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

export function DispatcherPage({
  initialList,
  initialDetail,
  initialSchedule,
  initialTechnicianCandidates,
  session,
  onLogout,
}: {
  initialList?: DispatcherListResponse;
  initialDetail?: DispatcherRequestDetail;
  initialSchedule?: ScheduleListResponse;
  initialTechnicianCandidates?: TechnicianCandidateListResponse;
  session?: StaffSession | null;
  onLogout?: () => void;
}) {
  const [list, setList] = useState<DispatcherListResponse>(initialList ?? { items: [] });
  const [schedule, setSchedule] = useState<ScheduleListResponse>(initialSchedule ?? { items: [] });
  const [technicianCandidates, setTechnicianCandidates] = useState<TechnicianCandidateListResponse>(
    initialTechnicianCandidates ?? { items: [] },
  );
  const [lowStock, setLowStock] = useState<InventoryPartListResponse>({ items: [] });
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
  const [appointmentTechnician, setAppointmentTechnician] = useState("technician@coffeefix.local");
  const [appointmentName, setAppointmentName] = useState("");
  const [appointmentStart, setAppointmentStart] = useState("");
  const [appointmentEnd, setAppointmentEnd] = useState("");
  const [appointmentLabel, setAppointmentLabel] = useState("");
  const [rescheduleStart, setRescheduleStart] = useState("");
  const [rescheduleEnd, setRescheduleEnd] = useState("");
  const [rescheduleLabel, setRescheduleLabel] = useState("");
  const [rescheduleReason, setRescheduleReason] = useState("");
  const [cancelReason, setCancelReason] = useState("");
  const [internalNote, setInternalNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<DispatcherStatusFilter>("all");
  const [urgencyFilter, setUrgencyFilter] = useState<DispatcherUrgencyFilter>("all");
  const filteredItems = filterDispatcherItems(list.items, statusFilter, urgencyFilter);

  function assertStaffResponse(response: Response, label: string) {
    if (isStaffAuthFailureStatus(response.status)) {
      onLogout?.();
      throw new Error(`${label} failed with ${response.status}`);
    }
    if (!response.ok) throw new Error(`${label} failed with ${response.status}`);
  }

  async function loadList() {
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherListPath()}`, {
      headers: staffAuthHeaders(session),
    });
    assertStaffResponse(response, "Dispatcher list");
    const body = (await response.json()) as DispatcherListResponse;
    setList(body);
    if (!selected && body.items[0]) setSelected(body.items[0].request_number);
    return body;
  }

  async function loadSchedule() {
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherSchedulePath()}`, {
      headers: staffAuthHeaders(session),
    });
    assertStaffResponse(response, "Dispatcher schedule");
    const body = (await response.json()) as ScheduleListResponse;
    setSchedule(body);
    return body;
  }

  async function loadTechnicianCandidates() {
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherTechnicianCandidatesPath()}`, {
      headers: staffAuthHeaders(session),
    });
    assertStaffResponse(response, "Technician candidates");
    const body = (await response.json()) as TechnicianCandidateListResponse;
    setTechnicianCandidates(body);
    return body;
  }

  async function loadLowStock() {
    const response = await fetch(`${apiBaseUrl()}${buildInventoryLowStockPath()}`, {
      headers: staffAuthHeaders(session),
    });
    assertStaffResponse(response, "Low-stock inventory");
    const body = (await response.json()) as InventoryPartListResponse;
    setLowStock(body);
    return body;
  }

  async function loadDetail(requestNumber: string) {
    if (!requestNumber) return;
    const response = await fetch(`${apiBaseUrl()}${buildDispatcherDetailPath(requestNumber)}`, {
      headers: staffAuthHeaders(session),
    });
    assertStaffResponse(response, "Dispatcher detail");
    const body = (await response.json()) as DispatcherRequestDetail;
    setDetail(body);
    setSelected(body.request_number);
  }

  async function refresh(requestNumber = selected) {
    setLoading(true);
    setMessage(null);
    try {
      await Promise.all([loadList(), loadSchedule(), loadLowStock()]);
      await loadTechnicianCandidates();
      if (requestNumber) await loadDetail(requestNumber);
    } catch {
      setMessage("Не удалось обновить диспетчерские данные.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialList || initialDetail || initialSchedule) return;
    void refresh();
  }, [initialList, initialDetail, initialSchedule]);

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

  async function submitAppointment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    await postAction(
      buildDispatcherAppointmentPath(detail.request_number),
      {
        technician_identifier: appointmentTechnician.trim(),
        technician_name: appointmentName.trim() || undefined,
        starts_at: toApiDateTime(appointmentStart),
        ends_at: toApiDateTime(appointmentEnd),
        window_label: appointmentLabel.trim() || undefined,
      },
      () => {
        setAppointmentName("");
        setAppointmentStart("");
        setAppointmentEnd("");
        setAppointmentLabel("");
      },
      "Визит запланирован.",
    );
  }

  async function submitReschedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail?.appointment) return;
    await postAction(
      buildDispatcherAppointmentReschedulePath(detail.request_number, detail.appointment.appointment_id),
      {
        starts_at: toApiDateTime(rescheduleStart),
        ends_at: toApiDateTime(rescheduleEnd),
        window_label: rescheduleLabel.trim() || undefined,
        reason: rescheduleReason.trim() || undefined,
      },
      () => {
        setRescheduleStart("");
        setRescheduleEnd("");
        setRescheduleLabel("");
        setRescheduleReason("");
      },
      "Визит перенесен.",
    );
  }

  async function submitCancelAppointment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail?.appointment) return;
    await postAction(
      buildDispatcherAppointmentCancelPath(detail.request_number, detail.appointment.appointment_id),
      { reason: cancelReason.trim() || undefined },
      () => setCancelReason(""),
      "Визит отменен.",
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

  function selectTechnicianCandidate(candidate: TechnicianCandidate) {
    setTechnicianName(candidate.username);
    setTechnicianPhone(candidate.phone);
    setTechnicianRegion("");
    setAppointmentTechnician(candidate.username);
    setAppointmentName(candidate.display_name);
  }

  function selectTechnicianCandidateByUsername(username: string) {
    const candidate = technicianCandidates.items.find((item) => item.username === username);
    if (candidate) {
      selectTechnicianCandidate(candidate);
      return;
    }
    setTechnicianName(username);
    setAppointmentTechnician(username);
  }

  const pendingAiSuggestions = detail?.ai_suggestions?.filter((suggestion) => suggestion.status === "pending") ?? [];
  const archivedAiSuggestions = detail?.ai_suggestions?.filter((suggestion) => suggestion.status !== "pending") ?? [];
  const visibleAiSuggestions = pendingAiSuggestions.length ? pendingAiSuggestions : detail?.ai_suggestions?.slice(0, 3) ?? [];
  const visibleTimeline = detail?.timeline.slice(-2) ?? [];
  const hiddenTimeline = detail?.timeline.slice(0, Math.max((detail?.timeline.length ?? 0) - 2, 0)) ?? [];
  const hiddenTimelineCount = hiddenTimeline.length;
  const notificationFailures = detail?.notification_deliveries?.filter((delivery) => delivery.status === "failed") ?? [];
  const technicalLogCount = detail?.notification_deliveries?.length ?? 0;
  const clarificationHistory = detail?.clarification_history ?? (detail?.clarification ? [detail.clarification] : []);

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
              <div className="schedule-panel" aria-label="Расписание">
                <div className="schedule-panel-heading">
                  <strong>Расписание</strong>
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
                      <strong>{item.appointment.request_number}</strong>
                      <small>{item.appointment.technician_identifier}</small>
                      <em>{item.customer_name} · {item.machine_label}</em>
                    </button>
                  ))
                ) : (
                  <p className="dispatcher-empty">Активных визитов нет.</p>
                )}
              </div>
              <div className="schedule-panel" aria-label="Низкие остатки">
                <div className="schedule-panel-heading">
                  <strong>Низкие остатки</strong>
                  <span>{lowStock.items.length}</span>
                </div>
                {lowStock.items.length ? (
                  lowStock.items.slice(0, 4).map((part) => (
                    <div className="schedule-row passive-row" key={part.part_id}>
                      <span>{part.sku}</span>
                      <strong>{part.name}</strong>
                      <small>Доступно {formatInventoryQuantity(part.available_quantity, part.unit)} · минимум {part.low_stock_threshold ?? 0}</small>
                    </div>
                  ))
                ) : (
                  <p className="dispatcher-empty">Критичных остатков нет.</p>
                )}
              </div>
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
                    <details className="customer-thread">
                      <summary>Переписка с клиентом</summary>
                      <div className="customer-thread-list">
                        {clarificationHistory.length ? (
                          clarificationHistory.map((item) => (
                            <div className="customer-thread-pair" key={item.question_id}>
                              <article className="customer-message staff-message">
                                <strong>Вопрос сотрудника</strong>
                                <p>{item.question}</p>
                              </article>
                              {item.answer ? (
                                <article className="customer-message customer-message-answer">
                                  <strong>Ответ клиента</strong>
                                  <p>{item.answer}</p>
                                  {item.answered_at ? (
                                    <time dateTime={item.answered_at}>{formatCompactDateTime(item.answered_at)}</time>
                                  ) : null}
                                </article>
                              ) : (
                                <small>Ответ клиента еще не получен.</small>
                              )}
                            </div>
                          ))
                        ) : (
                          <small>Переписки по уточнениям пока нет.</small>
                        )}
                      </div>
                    </details>
                  </section>

                  <section className="dispatcher-card appointment-card visit-card">
                    <div className="dispatcher-card-heading">
                      <h3>Визит</h3>
                      {detail.appointment ? <span>{appointmentStatusLabel(detail.appointment.status)}</span> : null}
                    </div>
                    <div className="visit-current">
                      <div>
                        <span>Мастер</span>
                        <strong>
                          {detail.assignment.technician_name || detail.appointment?.technician_identifier || "Не назначен"}
                        </strong>
                        <small>
                          {detail.assignment.technician_phone || detail.appointment?.technician_identifier || "Выберите мастера и окно визита."}
                        </small>
                      </div>
                      <div>
                        <span>Окно</span>
                        <strong>{detail.appointment?.window_label || detail.assignment.visit_window || "Не создано"}</strong>
                        <small>
                          {detail.appointment
                            ? `${formatCompactDateTime(detail.appointment.starts_at)} - ${formatCompactDateTime(detail.appointment.ends_at)}`
                            : detail.assignment.visit_window
                              ? "Окно из назначения, без точного интервала расписания"
                              : "Укажите дату и время ниже."}
                        </small>
                      </div>
                    </div>
                    <div className="visit-workspace">
                      <div className="visit-panel">
                        <strong>Мастер и первичное окно</strong>
                        <form className="dispatcher-form" onSubmit={submitAssignment}>
                          <label className="technician-picker">
                            <span>Мастер</span>
                            <select
                              aria-label="Кандидат мастера"
                              value={technicianName}
                              onChange={(event) => selectTechnicianCandidateByUsername(event.target.value)}
                            >
                              <option value="">Выберите мастера из списка</option>
                              {technicianCandidates.items.map((candidate) => (
                                <option key={candidate.username} value={candidate.username}>
                                  {candidate.display_name} · {candidate.username}
                                  {candidate.phone ? ` · ${candidate.phone}` : ""}
                                </option>
                              ))}
                            </select>
                            {technicianCandidates.items.length ? (
                              <small>
                                {technicianName
                                  ? technicianCandidates.items.find((candidate) => candidate.username === technicianName)?.phone ?? "Телефон не указан"
                                  : "Список содержит активных сотрудников с ролью technician."}
                              </small>
                            ) : (
                              <small>Активных сотрудников с ролью technician пока нет.</small>
                            )}
                          </label>
                          <input value={technicianName} onChange={(event) => setTechnicianName(event.target.value)} placeholder="Логин мастера" required />
                          <input value={technicianPhone} onChange={(event) => setTechnicianPhone(event.target.value)} placeholder="Телефон мастера" />
                          <input value={technicianRegion} onChange={(event) => setTechnicianRegion(event.target.value)} placeholder="Регион" />
                          <input value={visitWindow} onChange={(event) => setVisitWindow(event.target.value)} placeholder="Окно визита" />
                          <button className="submit-button" type="submit">Назначить мастера</button>
                        </form>
                      </div>
                      <div className="visit-panel">
                        <strong>Точное расписание</strong>
                        <form className="dispatcher-form compact-form" onSubmit={submitAppointment}>
                          <input value={appointmentTechnician} onChange={(event) => setAppointmentTechnician(event.target.value)} placeholder="Логин мастера" required />
                          <input value={appointmentName} onChange={(event) => setAppointmentName(event.target.value)} placeholder="Имя для расписания" />
                          <input value={appointmentStart} onChange={(event) => setAppointmentStart(event.target.value)} aria-label="Начало визита" required type="datetime-local" />
                          <input value={appointmentEnd} onChange={(event) => setAppointmentEnd(event.target.value)} aria-label="Конец визита" required type="datetime-local" />
                          <input value={appointmentLabel} onChange={(event) => setAppointmentLabel(event.target.value)} placeholder="Метка окна" />
                          <button className="submit-button" type="submit">{detail.appointment ? "Создать новое окно" : "Создать визит"}</button>
                        </form>
                        {detail.appointment ? (
                          <>
                            <form className="dispatcher-form compact-form" onSubmit={submitReschedule}>
                              <input value={rescheduleStart} onChange={(event) => setRescheduleStart(event.target.value)} aria-label="Новое начало визита" required type="datetime-local" />
                              <input value={rescheduleEnd} onChange={(event) => setRescheduleEnd(event.target.value)} aria-label="Новый конец визита" required type="datetime-local" />
                              <input value={rescheduleLabel} onChange={(event) => setRescheduleLabel(event.target.value)} placeholder="Новая метка" />
                              <input value={rescheduleReason} onChange={(event) => setRescheduleReason(event.target.value)} placeholder="Причина переноса" />
                              <button className="submit-button" type="submit">Перенести визит</button>
                            </form>
                            <form className="dispatcher-form compact-form" onSubmit={submitCancelAppointment}>
                              <input value={cancelReason} onChange={(event) => setCancelReason(event.target.value)} placeholder="Причина отмены" />
                              <button className="secondary-status-button" type="submit">Отменить визит</button>
                            </form>
                          </>
                        ) : null}
                      </div>
                    </div>
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

                  <section className="dispatcher-card appointment-card history-card">
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

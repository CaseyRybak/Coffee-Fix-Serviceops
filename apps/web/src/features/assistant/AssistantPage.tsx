import { useEffect, useState } from "react";
import { Bot, CheckCircle2, Loader2, LogIn, Send, Shield, Sparkles, Wrench, XCircle } from "lucide-react";

import { apiBaseUrl, buildAssistantConfirmPath, buildAssistantRunsPath } from "../../shared/api";
import {
  buildStaffLoginPath,
  clearStaffSession,
  getStoredStaffSession,
  redirectOnStaffAuthFailure,
  staffAuthHeaders,
  staffHasRole,
} from "../../shared/staffAuth";
import type { AssistantRunListResponse, AssistantRunResponse, AssistantToolCall, StaffSession } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const assistantRoles = ["dispatcher", "admin", "inventory"] as const;

export function AssistantPage({
  initialSession,
  initialRuns,
  onLogout,
}: {
  initialSession: StaffSession;
  initialRuns?: AssistantRunResponse[];
  onLogout?: () => void;
}) {
  const [runs, setRuns] = useState<AssistantRunResponse[]>(initialRuns ?? []);
  const [message, setMessage] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmingRunId, setConfirmingRunId] = useState<number | null>(null);

  useEffect(() => {
    if (initialRuns !== undefined) return;
    let cancelled = false;
    async function loadRuns() {
      const response = await fetch(`${apiBaseUrl()}${buildAssistantRunsPath()}`, {
        headers: staffAuthHeaders(initialSession),
      });
      if (shouldRedirectAssistantResponse(response.status) && redirectOnStaffAuthFailure(response.status, "/assistant")) return;
      if (!response.ok) {
        setStatusMessage("Не удалось загрузить историю помощника.");
        return;
      }
      const body = (await response.json()) as AssistantRunListResponse;
      if (!cancelled) setRuns(body.items);
    }
    void loadRuns();
    return () => {
      cancelled = true;
    };
  }, [initialRuns, initialSession]);

  async function submitPrompt() {
    const trimmed = message.trim();
    if (!trimmed) return;
    setIsSubmitting(true);
    setStatusMessage("");
    const response = await fetch(`${apiBaseUrl()}${buildAssistantRunsPath()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...staffAuthHeaders(initialSession) },
      body: JSON.stringify({ message: trimmed }),
    });
    setIsSubmitting(false);
    if (shouldRedirectAssistantResponse(response.status) && redirectOnStaffAuthFailure(response.status, "/assistant")) return;
    if (!response.ok) {
      setStatusMessage(response.status === 403 ? "Недостаточно прав для этого инструмента." : "Помощник не смог обработать запрос.");
      return;
    }
    const run = (await response.json()) as AssistantRunResponse;
    setRuns((current) => [run, ...current]);
    setMessage("");
  }

  async function confirmRun(runId: number) {
    if (confirmingRunId !== null) return;
    setConfirmingRunId(runId);
    setStatusMessage("");
    const response = await fetch(`${apiBaseUrl()}${buildAssistantConfirmPath(runId)}`, {
      method: "POST",
      headers: staffAuthHeaders(initialSession),
    });
    setConfirmingRunId(null);
    if (shouldRedirectAssistantResponse(response.status) && redirectOnStaffAuthFailure(response.status, "/assistant")) return;
    if (!response.ok) {
      setStatusMessage(response.status === 403 ? "Недостаточно прав для подтверждения действия." : "Не удалось подтвердить действие.");
      return;
    }
    const confirmed = (await response.json()) as AssistantRunResponse;
    setRuns((current) => current.map((run) => (run.run_id === confirmed.run_id ? confirmed : run)));
  }

  return (
    <div className="app-page dispatcher-page assistant-page">
      <WorkspaceHeader session={initialSession} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell assistant-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Внутренний контур</span>
              <h1>AI-помощник</h1>
              <p>Инструменты для заявок, расписания, сервиса, базы знаний, склада, закупок и мастеров.</p>
            </div>
          </div>

          <div className="assistant-layout">
            <section className="dispatcher-card assistant-compose">
              <div className="assistant-panel-title">
                <Bot aria-hidden="true" />
                <h2>Запрос сотрудника</h2>
              </div>
              <label className="form-field">
                <span className="field-label">Что нужно проверить</span>
                <textarea
                  rows={5}
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Например: Сколько новых заявок за сегодня? или Какие закупки завершены за последние 7 дней?"
                />
              </label>
              <button className="submit-button" type="button" onClick={submitPrompt} disabled={isSubmitting}>
                <Send aria-hidden="true" />
                {isSubmitting ? "Выполняем" : "Спросить"}
              </button>
              {statusMessage ? <p className="status-message error">{statusMessage}</p> : null}
            </section>

            <section className="assistant-runs" aria-live="polite">
              {runs.length === 0 ? (
                <div className="dispatcher-card assistant-empty">
                  <Sparkles aria-hidden="true" />
                  <h2>История пуста</h2>
                  <p>Здесь появятся безопасные результаты инструментов и запросы на подтверждение.</p>
                </div>
              ) : (
                runs.map((run) => (
                  <AssistantRunCard
                    key={run.run_id}
                    run={run}
                    confirming={confirmingRunId === run.run_id}
                    onConfirm={confirmRun}
                  />
                ))
              )}
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

function AssistantRunCard({
  run,
  confirming,
  onConfirm,
}: {
  run: AssistantRunResponse;
  confirming: boolean;
  onConfirm: (runId: number) => void;
}) {
  const needsConfirmation = run.status === "confirmation_required";
  const isExecuting = run.status === "executing";
  return (
    <article className={`dispatcher-card assistant-run assistant-run-${run.status}`}>
      <div className="assistant-run-head">
        <div>
          <span>{assistantRunStatusLabel(run.status)}</span>
          <h2>{assistantRunTitle(run)}</h2>
        </div>
        {needsConfirmation ? (
          <Wrench aria-hidden="true" />
        ) : isExecuting ? (
          <Loader2 aria-hidden="true" />
        ) : run.status === "failed" ? (
          <XCircle aria-hidden="true" />
        ) : (
          <CheckCircle2 aria-hidden="true" />
        )}
      </div>
      <p>{run.assistant_message}</p>
      <div className="assistant-tool-list">
        {run.tool_calls.map((toolCall) => (
          <AssistantToolCallCard key={toolCall.tool_call_id} toolCall={toolCall} />
        ))}
      </div>
      {needsConfirmation ? (
        <button
          className="submit-button assistant-confirm-button"
          type="button"
          disabled={confirming}
          onClick={() => onConfirm(run.run_id)}
        >
          <CheckCircle2 aria-hidden="true" />
          {confirming ? "Подтверждаем" : "Подтвердить действие"}
        </button>
      ) : null}
    </article>
  );
}

function AssistantToolCallCard({ toolCall }: { toolCall: AssistantToolCall }) {
  return (
    <details className="assistant-tool-card" open={toolCall.status === "confirmation_required"}>
      <summary>
        <span>{toolCall.tool_name}</span>
        <em>
          {toolCall.policy === "requires_confirmation" ? "с подтверждением" : "только чтение"}
          {toolCall.status === "executing" ? " · выполняется" : ""}
        </em>
      </summary>
      <p>{toolCall.result_summary}</p>
      {toolCall.result_refs.length ? (
        <div className="assistant-ref-list">
          {toolCall.result_refs.map((ref) => {
            const href = safeAssistantHref(ref.href);
            return href ? (
              <a href={href} key={`${ref.target_type}:${ref.target_id}`}>
                {ref.label}
              </a>
            ) : (
              <span key={`${ref.target_type}:${ref.target_id}`}>{ref.label}</span>
            );
          })}
        </div>
      ) : null}
    </details>
  );
}

function assistantRunStatusLabel(status: AssistantRunResponse["status"]): string {
  if (status === "confirmation_required") return "Требует подтверждения";
  if (status === "executing") return "Выполняется";
  if (status === "failed") return "Ошибка";
  return "Выполнено";
}

function assistantRunTitle(run: AssistantRunResponse): string {
  const questionTitle = safeQuestionTitle(run.safe_message);
  if (questionTitle) return questionTitle;
  if (!run.safe_message.startsWith("tool=")) return run.safe_message;
  const answerTitle = assistantAnswerTitle(run.assistant_message);
  if (answerTitle) return answerTitle;
  const toolName = run.tool_calls[0]?.tool_name ?? run.safe_message.replace("tool=", "").split(";", 1)[0];
  return assistantToolTitle(toolName);
}

function safeQuestionTitle(safeMessage: string): string | null {
  if (!safeMessage.startsWith("Вопрос:")) return null;
  const question = safeMessage.replace("Вопрос:", "").split(";", 1)[0]?.trim();
  return question || null;
}

function assistantAnswerTitle(message: string): string | null {
  const totalRequests = message.match(/Всего заявок:\s*\d+/i)?.[0];
  if (totalRequests) return totalRequests;
  const overdue = message.match(/Overdue requests:\s*\d+/i)?.[0];
  if (overdue) return overdue.replace("Overdue requests", "Просроченные заявки");
  const requestNumber = message.match(/CFX-\d{8}-\d{6}/i)?.[0];
  if (requestNumber) return requestNumber.toUpperCase();
  return null;
}

function assistantToolTitle(toolName: string): string {
  const titles: Record<string, string> = {
    find_request: "Заявка",
    answer_requests: "Заявки",
    answer_schedule: "Расписание",
    answer_technicians: "Мастера",
    answer_database_query: "Аналитика БД",
    answer_capabilities: "Возможности помощника",
    answer_service_catalog: "Сервис и сайт",
    answer_staff_contacts: "Контакты сотрудников",
    answer_procurement: "Закупки",
    assistant_self_check: "Самопроверка",
    list_overdue_requests: "Просроченные заявки",
    search_knowledge_base: "База знаний",
    check_part_stock: "Склад",
    recommend_technician: "Рекомендация техника",
    generate_daily_report: "Дневной отчет",
    create_purchase_request_draft: "Черновик закупки",
  };
  return titles[toolName] ?? "Ответ помощника";
}

export function ProtectedAssistantPage({
  initialSession,
  initialRuns,
}: {
  initialSession?: StaffSession | null;
  initialRuns?: AssistantRunResponse[];
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined) return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if (!canUseAssistant(stored) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath("/assistant");
    }
  }, [initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/assistant");
  }

  if (!canUseAssistant(session)) {
    const isAuthenticated = Boolean(session);
    return (
      <div className="app-page dispatcher-page assistant-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>{isAuthenticated ? "Недостаточно прав" : "Требуется вход сотрудника"}</h1>
              <p>{isAuthenticated ? "Для помощника нужна роль dispatcher, admin или inventory." : "AI-помощник находится во внутреннем контуре."}</p>
              <a className="submit-button" href={buildStaffLoginPath("/assistant")}>
                <LogIn aria-hidden="true" />
                {isAuthenticated ? "Войти другим сотрудником" : "Войти"}
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <AssistantPage initialSession={session} initialRuns={initialRuns} onLogout={logout} />;
}

export function shouldRedirectAssistantResponse(status: number): boolean {
  return status === 401;
}

function canUseAssistant(session: StaffSession | null): session is StaffSession {
  return Boolean(session && assistantRoles.some((role) => staffHasRole(session, role)));
}

function safeAssistantHref(href: string | null): string | null {
  if (!href) return null;
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  try {
    const parsed = new URL(href);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") return href;
  } catch {
    return null;
  }
  return null;
}

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, BarChart3, Clock3, LogIn, PackageSearch, RefreshCw, Shield, UsersRound } from "lucide-react";

import { apiBaseUrl, buildOwnerDashboardPath } from "../../shared/api";
import { formatCompactDateTime } from "../../shared/formatters";
import {
  buildStaffLoginPath,
  clearStaffSession,
  getStoredStaffSession,
  isStaffAuthFailureStatus,
  staffAuthHeaders,
  staffHasRole,
} from "../../shared/staffAuth";
import type { OwnerDashboardMetrics, OwnerDashboardResponse, OwnerSlaRiskItem, StaffSession } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const emptyDashboard: OwnerDashboardResponse = {
  generated_at: "",
  metrics: {
    total_requests: 0,
    new_requests: 0,
    in_progress_requests: 0,
    waiting_for_parts_requests: 0,
    completed_requests: 0,
    overdue_requests: 0,
    near_deadline_requests: 0,
  },
  sla_risks: [],
  technician_workload: [],
  top_issue_groups: [],
  low_stock_risk: [],
};

const metricLabels: Array<{ key: keyof OwnerDashboardMetrics; label: string; tone: string }> = [
  { key: "total_requests", label: "Всего заявок", tone: "total" },
  { key: "new_requests", label: "Новые заявки", tone: "fresh" },
  { key: "in_progress_requests", label: "В работе", tone: "work" },
  { key: "waiting_for_parts_requests", label: "Ждут запчасти", tone: "parts" },
  { key: "completed_requests", label: "Завершены", tone: "done" },
  { key: "overdue_requests", label: "Просрочены", tone: "danger" },
  { key: "near_deadline_requests", label: "Близко к сроку", tone: "warn" },
];

export function OwnerDashboardPage({
  initialSession,
  initialDashboard,
  onLogout,
}: {
  initialSession?: StaffSession | null;
  initialDashboard?: OwnerDashboardResponse;
  onLogout?: () => void;
}) {
  const session = initialSession ?? getStoredStaffSession();
  const [dashboard, setDashboard] = useState<OwnerDashboardResponse>(initialDashboard ?? emptyDashboard);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildOwnerDashboardPath()}`, {
        headers: staffAuthHeaders(session),
      });
      if (isStaffAuthFailureStatus(response.status)) {
        clearStaffSession();
        if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/owner");
        return;
      }
      if (!response.ok) throw new Error(`Owner dashboard failed with ${response.status}`);
      setDashboard((await response.json()) as OwnerDashboardResponse);
    } catch {
      setMessage("Не удалось обновить панель владельца.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialDashboard) return;
    if (!session || !staffHasRole(session, "admin")) return;
    void loadDashboard();
  }, [initialDashboard, session?.accessToken]);

  return (
    <div className="app-page dispatcher-page owner-page">
      <WorkspaceHeader session={session} onLogout={onLogout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell owner-shell">
          <div className="dispatcher-topline owner-topline">
            <div>
              <span>Внутренний контур</span>
              <h1>Панель владельца</h1>
              <p>Операционная сводка по SLA, загрузке мастеров, ожиданию запчастей и складским рискам.</p>
            </div>
            <button className="secondary-status-button" type="button" onClick={() => void loadDashboard()} disabled={loading}>
              <RefreshCw aria-hidden="true" />
              {loading ? "Обновляем" : "Обновить"}
            </button>
          </div>

          {message ? <p className="owner-alert">{message}</p> : null}

          <section className="owner-metrics-grid" aria-label="Метрики владельца">
            {metricLabels.map((metric) => (
              <article className={`owner-metric owner-metric-${metric.tone}`} key={metric.key}>
                <span>{metric.label}</span>
                <strong>{dashboard.metrics[metric.key]}</strong>
              </article>
            ))}
          </section>

          <section className="owner-dashboard-layout">
            <article className="owner-panel owner-panel-wide">
              <PanelTitle icon={<AlertTriangle aria-hidden="true" />} title="SLA риск" />
              {dashboard.sla_risks.length ? (
                <div className="owner-risk-list">
                  {dashboard.sla_risks.map((risk) => (
                    <SlaRiskRow key={risk.request_number} risk={risk} />
                  ))}
                </div>
              ) : (
                <p className="owner-empty">Активных SLA рисков нет.</p>
              )}
            </article>

            <article className="owner-panel">
              <PanelTitle icon={<UsersRound aria-hidden="true" />} title="Загрузка мастеров" />
              {dashboard.technician_workload.length ? (
                <div className="owner-compact-list">
                  {dashboard.technician_workload.map((item) => (
                    <div className="owner-compact-row" key={item.technician_identifier}>
                      <strong>{item.technician_identifier}</strong>
                      <span>
                        {item.active_requests} активных · {item.scheduled_visits} визитов · {item.waiting_for_parts} ждут запчасти
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="owner-empty">Нет активной загрузки мастеров.</p>
              )}
            </article>

            <article className="owner-panel">
              <PanelTitle icon={<BarChart3 aria-hidden="true" />} title="Группы проблем" />
              {dashboard.top_issue_groups.length ? (
                <div className="owner-compact-list">
                  {dashboard.top_issue_groups.map((item) => (
                    <div className="owner-compact-row owner-count-row" key={item.label}>
                      <strong>{item.label}</strong>
                      <span>{item.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="owner-empty">Пока нет заявок для группировки.</p>
              )}
            </article>

            <article className="owner-panel owner-panel-wide">
              <PanelTitle icon={<PackageSearch aria-hidden="true" />} title="Низкий складской остаток" />
              {dashboard.low_stock_risk.length ? (
                <div className="owner-stock-grid">
                  {dashboard.low_stock_risk.map((part) => (
                    <div className="owner-stock-item" key={part.part_id}>
                      <strong>{part.sku}</strong>
                      <span>{part.name}</span>
                      <small>
                        Доступно {part.available_quantity} {part.unit} · минимум {part.low_stock_threshold ?? 0}
                      </small>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="owner-empty">Низких остатков нет.</p>
              )}
            </article>
          </section>

          {dashboard.generated_at ? (
            <p className="owner-generated">
              <Clock3 aria-hidden="true" />
              Обновлено <time dateTime={dashboard.generated_at}>{formatCompactDateTime(dashboard.generated_at)}</time>
            </p>
          ) : null}
        </section>
      </main>
    </div>
  );
}

export function ProtectedOwnerDashboardPage({ initialSession }: { initialSession?: StaffSession | null }) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined) return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if ((!stored || !staffHasRole(stored, "admin")) && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath("/owner");
    }
  }, [initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath("/owner");
  }

  if (!session || !staffHasRole(session, "admin")) {
    return (
      <div className="app-page dispatcher-page owner-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>Требуется вход администратора</h1>
              <p>Панель владельца доступна только внутреннему административному контуру.</p>
              <a className="submit-button" href={buildStaffLoginPath("/owner")}>
                <LogIn aria-hidden="true" />
                Войти
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return <OwnerDashboardPage initialSession={session} onLogout={logout} />;
}

function PanelTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="owner-panel-title">
      {icon}
      <h2>{title}</h2>
    </div>
  );
}

function SlaRiskRow({ risk }: { risk: OwnerSlaRiskItem }) {
  const stateLabel = risk.sla.state === "overdue" ? "Просрочено" : "Близко к сроку";
  return (
    <div className={`owner-risk-row owner-risk-${risk.sla.state}`}>
      <div>
        <strong>{risk.request_number}</strong>
        <span>
          {risk.customer_name} · {risk.machine_label}
        </span>
      </div>
      <div>
        <em>{stateLabel}</em>
        <small>
          {risk.sla.deadline_at ? `Срок ${formatCompactDateTime(risk.sla.deadline_at)}` : "SLA не активен"}
          {risk.sla.hours_remaining !== null ? ` · ${risk.sla.hours_remaining} ч` : ""}
        </small>
      </div>
    </div>
  );
}

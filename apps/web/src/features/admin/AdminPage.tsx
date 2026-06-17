import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { LogIn, Shield } from "lucide-react";

import {
  apiBaseUrl,
  buildAdminStaffActivatePath,
  buildAdminStaffAuditPath,
  buildAdminStaffDeactivatePath,
  buildAdminStaffPath,
  buildAdminStaffProfilePath,
  buildAdminStaffResetPasswordPath,
  buildAdminStaffRolesPath,
} from "../../shared/api";
import { formatCompactDateTime } from "../../shared/formatters";
import { buildStaffLoginPath, clearStaffSession, getStoredStaffSession, staffAuthHeaders, staffHasRole } from "../../shared/staffAuth";
import type { StaffAccountItem, StaffAccountListResponse, StaffAuditListResponse, StaffRole, StaffSession } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const staffRoleOptions: StaffRole[] = ["admin", "dispatcher", "technician", "inventory"];

interface StaffProfileDraft {
  firstName: string;
  lastName: string;
  phone: string;
}

function staffProfileDraft(account: StaffAccountItem): StaffProfileDraft {
  return {
    firstName: account.first_name,
    lastName: account.last_name,
    phone: account.phone,
  };
}

export function buildAdminStaffChangeRequests(username: string, profile: StaffProfileDraft, roles: StaffRole[]) {
  return [
    {
      path: buildAdminStaffProfilePath(username),
      body: {
        first_name: profile.firstName.trim(),
        last_name: profile.lastName.trim(),
        phone: profile.phone.trim(),
      },
    },
    {
      path: buildAdminStaffRolesPath(username),
      body: { roles },
    },
  ];
}

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
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [createRoles, setCreateRoles] = useState<StaffRole[]>(["dispatcher"]);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, StaffRole[]>>(() =>
    Object.fromEntries((initialStaff?.items ?? []).map((item) => [item.username, item.roles])),
  );
  const [profileDrafts, setProfileDrafts] = useState<Record<string, StaffProfileDraft>>(() =>
    Object.fromEntries((initialStaff?.items ?? []).map((item) => [item.username, staffProfileDraft(item)])),
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
    setProfileDrafts(Object.fromEntries(body.items.map((item) => [item.username, staffProfileDraft(item)])));
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
	          first_name: firstName.trim(),
	          last_name: lastName.trim(),
	          phone: phone.trim(),
	          password,
	          roles: createRoles,
	        }),
	      });
	      if (!response.ok) throw new Error(`Create staff failed with ${response.status}`);
	      setUsername("");
	      setFirstName("");
	      setLastName("");
	      setPhone("");
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

  async function postAdminActions(actions: { path: string; body: object }[], successMessage: string) {
    setLoading(true);
    setMessage(null);
    setTemporaryPassword(null);
    try {
      const responses = await Promise.all(
        actions.map((action) =>
          fetch(`${apiBaseUrl()}${action.path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...staffAuthHeaders(session) },
            body: JSON.stringify(action.body),
          }),
        ),
      );
      if (responses.some((response) => !response.ok)) throw new Error("Admin changes failed");
      await refresh();
      setMessage(successMessage);
    } catch {
      setMessage("Не удалось сохранить изменения сотрудника.");
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
                    const draftProfile = profileDrafts[account.username] ?? staffProfileDraft(account);
                    return (
                      <article className={account.active ? "admin-staff-row" : "admin-staff-row inactive"} key={account.username}>
                        <div className="admin-staff-identity">
                          <strong>{account.display_name}</strong>
                          <span>{account.username}</span>
                          {account.phone ? <span>{account.phone}</span> : null}
                          <small>
                            {account.active ? "Активен" : "Отключен"} · обновлен{" "}
                            <time dateTime={account.updated_at}>{formatCompactDateTime(account.updated_at)}</time>
                          </small>
                        </div>
                        <div className="admin-profile-control" aria-label={`Профиль ${account.username}`}>
                          <input
                            value={draftProfile.firstName}
                            onChange={(event) =>
                              setProfileDrafts((current) => ({
                                ...current,
                                [account.username]: { ...draftProfile, firstName: event.target.value },
                              }))
                            }
                            placeholder="Имя"
                            required
                          />
                          <input
                            value={draftProfile.lastName}
                            onChange={(event) =>
                              setProfileDrafts((current) => ({
                                ...current,
                                [account.username]: { ...draftProfile, lastName: event.target.value },
                              }))
                            }
                            placeholder="Фамилия"
                            required
                          />
                          <input
                            value={draftProfile.phone}
                            onChange={(event) =>
                              setProfileDrafts((current) => ({
                                ...current,
                                [account.username]: { ...draftProfile, phone: event.target.value },
                              }))
                            }
                            placeholder="Телефон"
                            required
                          />
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
                              void postAdminActions(
                                buildAdminStaffChangeRequests(account.username, draftProfile, draftRoles),
                                "Изменения сотрудника сохранены.",
                              )
                            }
                          >
                            Сохранить изменения
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
                <input value={firstName} onChange={(event) => setFirstName(event.target.value)} placeholder="Имя" required />
                <input value={lastName} onChange={(event) => setLastName(event.target.value)} placeholder="Фамилия" required />
                <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Телефон" required />
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

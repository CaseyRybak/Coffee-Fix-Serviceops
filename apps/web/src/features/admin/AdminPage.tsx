import { useEffect, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { ChevronDown, LogIn, Plus, Shield, X } from "lucide-react";

import {
  apiBaseUrl,
  buildAdminStaffActivatePath,
  buildAdminStaffAuditPath,
  buildAdminStaffDeactivatePath,
  buildAdminStaffPath,
  buildAdminStaffProfilePath,
  buildAdminStaffResetPasswordPath,
  buildAdminStaffRolesPath,
  buildAdminTechnicianProfilePath,
  buildAdminTechnicianProfilesPath,
} from "../../shared/api";
import { formatCompactDateTime } from "../../shared/formatters";
import {
  buildStaffLoginPath,
  clearStaffSession,
  getStoredStaffSession,
  redirectOnStaffAuthFailure,
  staffAuthHeaders,
  staffHasRole,
} from "../../shared/staffAuth";
import type {
  StaffAccountItem,
  StaffAccountListResponse,
  StaffAuditListResponse,
  StaffRole,
  StaffSession,
  TechnicianProfileItem,
  TechnicianProfileListResponse,
} from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const staffRoleOptions: StaffRole[] = ["admin", "dispatcher", "technician", "inventory"];

interface StaffProfileDraft {
  firstName: string;
  lastName: string;
  phone: string;
}

interface TechnicianProfileDraft {
  active: boolean;
  skillBrands: string[];
  serviceRegions: string[];
  brandInput: string;
  regionInput: string;
  notes: string;
}

function staffProfileDraft(account: StaffAccountItem): StaffProfileDraft {
  return {
    firstName: account.first_name,
    lastName: account.last_name,
    phone: account.phone,
  };
}

function technicianProfileDraft(profile?: TechnicianProfileItem): TechnicianProfileDraft {
  return {
    active: profile?.active ?? true,
    skillBrands: profile?.skill_brands ?? [],
    serviceRegions: profile?.service_regions ?? [],
    brandInput: "",
    regionInput: "",
    notes: profile?.notes ?? "",
  };
}

function splitProfileText(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeProfileItems(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  values
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((item) => {
      const key = item.toLocaleLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      result.push(item);
    });
  return result;
}

export function buildTechnicianProfilePayload(profile: TechnicianProfileDraft) {
  return {
    active: profile.active,
    skill_brands: normalizeProfileItems(profile.skillBrands),
    service_regions: normalizeProfileItems(profile.serviceRegions),
    notes: profile.notes.trim() || undefined,
  };
}

function formatProfileCount(count: number, one: string, few: string, many: string): string {
  if (count % 10 === 1 && count % 100 !== 11) return `${count} ${one}`;
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return `${count} ${few}`;
  return `${count} ${many}`;
}

function ProfileChipEditor({
  label,
  addLabel,
  placeholder,
  values,
  inputValue,
  onInputChange,
  onAdd,
  onRemove,
}: {
  label: string;
  addLabel: string;
  placeholder: string;
  values: string[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onAdd: () => void;
  onRemove: (value: string) => void;
}) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    onAdd();
  }

  return (
    <div className="technician-profile-chip-editor">
      <span>{label}</span>
      <div className="technician-profile-chip-list" aria-label={label}>
        {values.map((value) => (
          <button
            className="technician-profile-chip"
            key={value}
            type="button"
            aria-label={`Удалить ${label.toLocaleLowerCase().slice(0, -1)} ${value}`}
            onClick={() => onRemove(value)}
          >
            {value}
            <X aria-hidden="true" />
          </button>
        ))}
      </div>
      <div className="technician-profile-add-row">
        <input value={inputValue} onChange={(event) => onInputChange(event.target.value)} onKeyDown={handleKeyDown} placeholder={placeholder} />
        <button type="button" onClick={onAdd} aria-label={addLabel}>
          <Plus aria-hidden="true" />
          {addLabel}
        </button>
      </div>
    </div>
  );
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

export function canEditTechnicianProfile(roles: StaffRole[]): boolean {
  return roles.includes("technician");
}

export function redirectOnAdminAuthFailure(
  status: number,
  storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined,
  location: Pick<Location, "href"> | undefined = typeof window !== "undefined" ? window.location : undefined,
): boolean {
  return redirectOnStaffAuthFailure(status, "/admin", storage, location);
}

export function AdminPage({
  initialSession,
  initialStaff,
  initialAudit,
  initialTechnicianProfiles,
  onLogout,
}: {
  initialSession?: StaffSession | null;
  initialStaff?: StaffAccountListResponse;
  initialAudit?: StaffAuditListResponse;
  initialTechnicianProfiles?: TechnicianProfileListResponse;
  onLogout?: () => void;
}) {
  const session = initialSession ?? getStoredStaffSession();
  const [staff, setStaff] = useState<StaffAccountListResponse>(initialStaff ?? { items: [] });
  const [audit, setAudit] = useState<StaffAuditListResponse>(initialAudit ?? { items: [] });
  const [technicianProfiles, setTechnicianProfiles] = useState<TechnicianProfileListResponse>(
    initialTechnicianProfiles ?? { items: [] },
  );
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
  const [technicianProfileDrafts, setTechnicianProfileDrafts] = useState<Record<string, TechnicianProfileDraft>>(() =>
    Object.fromEntries((initialTechnicianProfiles?.items ?? []).map((item) => [item.staff_username, technicianProfileDraft(item)])),
  );
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadStaff() {
    const response = await fetch(`${apiBaseUrl()}${buildAdminStaffPath()}`, { headers: staffAuthHeaders(session) });
    if (redirectOnAdminAuthFailure(response.status)) throw new Error("Admin session expired");
    if (!response.ok) throw new Error(`Admin staff list failed with ${response.status}`);
    const body = (await response.json()) as StaffAccountListResponse;
    setStaff(body);
    setRoleDrafts(Object.fromEntries(body.items.map((item) => [item.username, item.roles])));
    setProfileDrafts(Object.fromEntries(body.items.map((item) => [item.username, staffProfileDraft(item)])));
    return body;
  }

  async function loadAudit() {
    const response = await fetch(`${apiBaseUrl()}${buildAdminStaffAuditPath()}`, { headers: staffAuthHeaders(session) });
    if (redirectOnAdminAuthFailure(response.status)) throw new Error("Admin session expired");
    if (!response.ok) throw new Error(`Admin audit list failed with ${response.status}`);
    const body = (await response.json()) as StaffAuditListResponse;
    setAudit(body);
  }

  async function loadTechnicianProfiles() {
    const response = await fetch(`${apiBaseUrl()}${buildAdminTechnicianProfilesPath()}`, {
      headers: staffAuthHeaders(session),
    });
    if (redirectOnAdminAuthFailure(response.status)) throw new Error("Admin session expired");
    if (!response.ok) throw new Error(`Technician profiles list failed with ${response.status}`);
    const body = (await response.json()) as TechnicianProfileListResponse;
    setTechnicianProfiles(body);
    setTechnicianProfileDrafts(
      Object.fromEntries(body.items.map((item) => [item.staff_username, technicianProfileDraft(item)])),
    );
    return body;
  }

  async function refresh() {
    setLoading(true);
    setMessage(null);
    try {
      await loadStaff();
      await loadAudit();
      await loadTechnicianProfiles();
    } catch {
      setMessage("Не удалось обновить учетные записи сотрудников.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialStaff || initialAudit || initialTechnicianProfiles) return;
    void refresh();
  }, [initialStaff, initialAudit, initialTechnicianProfiles]);

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
		      if (redirectOnAdminAuthFailure(response.status)) throw new Error("Admin session expired");
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
      if (redirectOnAdminAuthFailure(response.status)) throw new Error("Admin session expired");
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
      if (responses.some((response) => redirectOnAdminAuthFailure(response.status))) {
        throw new Error("Admin session expired");
      }
      if (responses.some((response) => !response.ok)) throw new Error("Admin changes failed");
      await refresh();
      setMessage(successMessage);
    } catch {
      setMessage("Не удалось сохранить изменения сотрудника.");
    } finally {
      setLoading(false);
    }
  }

  async function postTechnicianProfile(username: string, profile: TechnicianProfileDraft) {
    await postAdminAction(
      buildAdminTechnicianProfilePath(username),
      buildTechnicianProfilePayload(profile),
      "Профиль мастера сохранен.",
    );
  }

  function technicianDraftFor(username: string, current: Record<string, TechnicianProfileDraft>) {
    const profile = technicianProfiles.items.find((item) => item.staff_username === username);
    return current[username] ?? technicianProfileDraft(profile);
  }

  function patchTechnicianDraft(username: string, patch: Partial<TechnicianProfileDraft>) {
    setTechnicianProfileDrafts((current) => {
      const draft = technicianDraftFor(username, current);
      return { ...current, [username]: { ...draft, ...patch } };
    });
  }

  function addTechnicianProfileItems(
    username: string,
    valueField: "skillBrands" | "serviceRegions",
    inputField: "brandInput" | "regionInput",
  ) {
    setTechnicianProfileDrafts((current) => {
      const draft = technicianDraftFor(username, current);
      const nextItems = splitProfileText(draft[inputField]);
      if (nextItems.length === 0) return current;
      return {
        ...current,
        [username]: {
          ...draft,
          [valueField]: normalizeProfileItems([...draft[valueField], ...nextItems]),
          [inputField]: "",
        },
      };
    });
  }

  function removeTechnicianProfileItem(username: string, valueField: "skillBrands" | "serviceRegions", value: string) {
    setTechnicianProfileDrafts((current) => {
      const draft = technicianDraftFor(username, current);
      const removedKey = value.toLocaleLowerCase();
      return {
        ...current,
        [username]: {
          ...draft,
          [valueField]: draft[valueField].filter((item) => item.toLocaleLowerCase() !== removedKey),
        },
      };
    });
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
                    const technicianProfile = technicianProfiles.items.find((item) => item.staff_username === account.username);
                    const technicianDraft =
                      technicianProfileDrafts[account.username] ?? technicianProfileDraft(technicianProfile);
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
                        {canEditTechnicianProfile(account.roles) ? (
                          <details className="technician-profile-control" aria-label={`Профиль мастера ${account.username}`}>
                            <summary className="technician-profile-summary">
                              <span>
                                <strong>Профиль мастера</strong>
                                <small>
                                  {formatProfileCount(technicianDraft.skillBrands.length, "бренд", "бренда", "брендов")} ·{" "}
                                  {formatProfileCount(technicianDraft.serviceRegions.length, "район", "района", "районов")}
                                </small>
                              </span>
                              <span className={technicianDraft.active ? "technician-profile-status active" : "technician-profile-status"}>
                                {technicianDraft.active ? "В рекомендациях" : "Выключен"}
                              </span>
                              <ChevronDown aria-hidden="true" />
                            </summary>
                            <div className="technician-profile-panel">
                              <label className="technician-profile-toggle">
                                <input checked={technicianDraft.active} type="checkbox" onChange={(event) => patchTechnicianDraft(account.username, { active: event.target.checked })} />
                                Участвует в рекомендациях
                              </label>
                              <ProfileChipEditor
                                label="Бренды"
                                addLabel="Добавить бренд"
                                placeholder="Jura, Rocket"
                                values={technicianDraft.skillBrands}
                                inputValue={technicianDraft.brandInput}
                                onInputChange={(value) => patchTechnicianDraft(account.username, { brandInput: value })}
                                onAdd={() => addTechnicianProfileItems(account.username, "skillBrands", "brandInput")}
                                onRemove={(value) => removeTechnicianProfileItem(account.username, "skillBrands", value)}
                              />
                              <ProfileChipEditor
                                label="Районы"
                                addLabel="Добавить район"
                                placeholder="ЦАО, Хамовники"
                                values={technicianDraft.serviceRegions}
                                inputValue={technicianDraft.regionInput}
                                onInputChange={(value) => patchTechnicianDraft(account.username, { regionInput: value })}
                                onAdd={() => addTechnicianProfileItems(account.username, "serviceRegions", "regionInput")}
                                onRemove={(value) => removeTechnicianProfileItem(account.username, "serviceRegions", value)}
                              />
                              <textarea
                                className="technician-profile-note"
                                value={technicianDraft.notes}
                                onChange={(event) => patchTechnicianDraft(account.username, { notes: event.target.value })}
                                placeholder="Внутренняя заметка"
                                rows={2}
                              />
                              <div className="technician-profile-actions">
                                <button
                                  className="technician-profile-save"
                                  type="button"
                                  onClick={() => void postTechnicianProfile(account.username, technicianDraft)}
                                >
                                  Сохранить
                                </button>
                              </div>
                            </div>
                          </details>
                        ) : null}
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
  initialTechnicianProfiles,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
  initialStaff?: StaffAccountListResponse;
  initialAudit?: StaffAuditListResponse;
  initialTechnicianProfiles?: TechnicianProfileListResponse;
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

  return (
    <AdminPage
      initialSession={session}
      onLogout={logout}
      initialStaff={initialStaff}
      initialAudit={initialAudit}
      initialTechnicianProfiles={initialTechnicianProfiles}
    />
  );
}

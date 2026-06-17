import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { LogIn, Shield } from "lucide-react";

import { apiBaseUrl } from "../../shared/api";
import {
  buildStaffLoginPath,
  resolveStaffLandingPath,
  storeStaffSession,
} from "../../shared/staffAuth";
import type { StaffRole } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

export function StaffLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function requestedNextPath(): string | null {
    if (typeof window === "undefined") return "/dispatcher";
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    return next?.startsWith("/") ? next : null;
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}/staff/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!response.ok) throw new Error(`Staff login failed with ${response.status}`);
      const body = (await response.json()) as {
        access_token: string;
        staff: { username: string; roles: StaffRole[] };
      };
      storeStaffSession({
        accessToken: body.access_token,
        username: body.staff.username,
        roles: body.staff.roles,
      });
      if (typeof window !== "undefined") window.location.href = resolveStaffLandingPath(body.staff, requestedNextPath());
    } catch {
      setMessage("Не удалось войти. Проверьте логин и пароль.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-page staff-login-page">
      <WorkspaceHeader />
      <main className="staff-login-main">
        <section className="staff-login-card">
          <div className="staff-login-badge">
            <Shield aria-hidden="true" />
          </div>
          <span>Внутренний контур</span>
          <h1>Вход для сотрудников</h1>
          <p>Доступ к диспетчерской и другим рабочим зонам открыт только сотрудникам с ролью.</p>
          <form className="staff-login-form" onSubmit={submitLogin}>
            <label>
              <span>Логин</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="name@company.example"
                required
                type="email"
              />
            </label>
            <label>
              <span>Пароль</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Введите пароль"
                required
                type="password"
              />
            </label>
            <button className="submit-button" type="submit" disabled={submitting}>
              <LogIn aria-hidden="true" />
              {submitting ? "Входим" : "Войти"}
            </button>
          </form>
          {message ? <p className="submit-error">{message}</p> : null}
        </section>
      </main>
    </div>
  );
}

import type { ReactNode } from "react";
import { Coffee, LogOut, Menu } from "lucide-react";

import type { StaffSession } from "./types";
import { staffWorkspacePath } from "./staffAuth";

export function Field({
  label,
  optional,
  children,
}: {
  label: string;
  optional?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="form-field">
      <span className="field-label">
        {label}
        {optional ? <em> - необязательно</em> : null}
      </span>
      {children}
    </label>
  );
}

export function ChipGroup<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}) {
  return (
    <div className="chip-row">
      {options.map((option) => (
        <button
          className={value === option.value ? "chip selected" : "chip"}
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Logo() {
  return (
    <a className="brand" href="/" aria-label="CoffeeFix Pro">
      <span className="brand-mark">
        <Coffee aria-hidden="true" />
      </span>
      <span className="brand-copy">
        <strong>CoffeeFix Pro</strong>
        <small>ремонт и обслуживание кофемашин</small>
      </span>
    </a>
  );
}

export function WorkspaceHeader({ session, onLogout }: { session?: StaffSession | null; onLogout?: () => void }) {
  const canChooseWorkspace = Boolean(session && session.roles.length > 1);

  return (
    <header className="workspace-header">
      <div className="site-header-inner workspace-header-inner">
        <Logo />
        <div className="workspace-session-actions">
          {session ? <span>{session.username}</span> : <span className="workspace-header-label">Рабочий кабинет</span>}
          {canChooseWorkspace ? (
            <a className="workspace-switch-link" href={staffWorkspacePath}>
              <Menu aria-hidden="true" />
              Кабинеты
            </a>
          ) : null}
          {onLogout ? (
            <button type="button" onClick={onLogout} aria-label="Выйти">
              <LogOut aria-hidden="true" />
              Выйти
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}

import { useEffect, useState } from "react";
import { BarChart3, Bot, ChevronRight, ClipboardList, LogIn, Package, Shield, Wrench, type LucideIcon } from "lucide-react";

import {
  buildStaffLoginPath,
  clearStaffSession,
  getStoredStaffSession,
  staffHasRole,
  staffWorkspacePath,
} from "../../shared/staffAuth";
import type { StaffRole, StaffSession } from "../../shared/types";
import { WorkspaceHeader } from "../../shared/ui";

const staffWorkspaceCards: Array<{
  roles: StaffRole[];
  href: string;
  title: string;
  copy: string;
  Icon: LucideIcon;
}> = [
  {
    roles: ["dispatcher"],
    href: "/dispatcher",
    title: "Диспетчерская",
    copy: "Заявки, уточнения, статусы, расписание и назначение мастеров.",
    Icon: ClipboardList,
  },
  {
    roles: ["technician"],
    href: "/technician",
    title: "Кабинет мастера",
    copy: "Назначенные выезды, диагностика, результат ремонта и использованные детали.",
    Icon: Wrench,
  },
  {
    roles: ["inventory"],
    href: "/inventory",
    title: "Склад",
    copy: "Каталог запчастей, остатки, совместимость, резервы и движения.",
    Icon: Package,
  },
  {
    roles: ["admin"],
    href: "/admin",
    title: "Администрирование",
    copy: "Учетные записи сотрудников, роли, доступы и аудит действий.",
    Icon: Shield,
  },
  {
    roles: ["admin"],
    href: "/owner",
    title: "Панель владельца",
    copy: "SLA, просрочки, загрузка мастеров, ожидание запчастей и складские риски.",
    Icon: BarChart3,
  },
  {
    roles: ["dispatcher", "admin", "inventory"],
    href: "/assistant",
    title: "AI-помощник",
    copy: "Ролевые инструменты для заявок, SLA, базы знаний, склада, рекомендаций и закупок.",
    Icon: Bot,
  },
  {
    roles: ["inventory", "admin"],
    href: "/procurement",
    title: "Согласование закупок",
    copy: "Поставщики, заявки на закупку и администраторское согласование.",
    Icon: Package,
  },
];

export function StaffWorkspacePage({
  hasSession,
  initialSession,
}: {
  hasSession?: boolean;
  initialSession?: StaffSession | null;
}) {
  const [session, setSession] = useState<StaffSession | null>(() => {
    if (initialSession !== undefined) return initialSession;
    if (typeof hasSession === "boolean") {
      return hasSession
        ? {
            accessToken: "test-token",
            username: "dispatcher@coffeefix.local",
            roles: ["dispatcher", "technician", "inventory"],
          }
        : null;
    }
    return getStoredStaffSession();
  });

  useEffect(() => {
    if (initialSession !== undefined) return;
    if (typeof hasSession === "boolean") return;
    const stored = getStoredStaffSession();
    setSession(stored);
    if (!stored && typeof window !== "undefined") {
      window.location.href = buildStaffLoginPath(staffWorkspacePath);
    }
  }, [hasSession, initialSession]);

  function logout() {
    clearStaffSession();
    setSession(null);
    if (typeof window !== "undefined") window.location.href = buildStaffLoginPath(staffWorkspacePath);
  }

  const availableCards = staffWorkspaceCards.filter((card) => card.roles.some((role) => staffHasRole(session, role)));

  if (!session) {
    return (
      <div className="app-page dispatcher-page">
        <WorkspaceHeader />
        <main className="dispatcher-main">
          <section className="section-inner dispatcher-shell">
            <div className="dispatcher-card protected-empty">
              <Shield aria-hidden="true" />
              <h1>Требуется вход сотрудника</h1>
              <p>Выбор кабинета доступен только сотрудникам внутреннего контура.</p>
              <a className="submit-button" href={buildStaffLoginPath(staffWorkspacePath)}>
                <LogIn aria-hidden="true" />
                Войти
              </a>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app-page dispatcher-page staff-workspace-page">
      <WorkspaceHeader session={session} onLogout={logout} />
      <main className="dispatcher-main">
        <section className="section-inner dispatcher-shell">
          <div className="dispatcher-topline">
            <div>
              <span>Внутренний контур</span>
              <h1>Выберите кабинет</h1>
              <p>Доступные рабочие зоны для {session.username}.</p>
            </div>
          </div>
          <div className="staff-workspace-grid">
            {availableCards.map(({ href, title, copy, Icon }) => (
              <a className="staff-workspace-card" href={href} key={href}>
                <Icon aria-hidden="true" />
                <strong>{title}</strong>
                <span>{copy}</span>
                <em>
                  Открыть
                  <ChevronRight aria-hidden="true" />
                </em>
              </a>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

import type { StaffRole, StaffSession } from "./types";

const staffSessionStorageKey = "serviceops.staffSession";
export const staffWorkspacePath = "/staff/workspace";

export function buildStaffLoginPath(nextPath = "/dispatcher"): string {
  return `/staff/login?next=${encodeURIComponent(nextPath)}`;
}

export function getStoredStaffSession(storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): StaffSession | null {
  if (!storage) return null;
  const raw = storage.getItem(staffSessionStorageKey);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<StaffSession>;
    if (!parsed.accessToken || !parsed.username || !Array.isArray(parsed.roles)) return null;
    return {
      accessToken: parsed.accessToken,
      username: parsed.username,
      roles: parsed.roles.filter((role): role is StaffRole =>
        ["dispatcher", "admin", "technician", "inventory"].includes(String(role)),
      ),
    };
  } catch {
    return null;
  }
}

export function storeStaffSession(session: StaffSession, storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): void {
  storage?.setItem(staffSessionStorageKey, JSON.stringify(session));
}

export function clearStaffSession(storage: Storage | undefined = typeof window !== "undefined" ? window.localStorage : undefined): void {
  storage?.removeItem(staffSessionStorageKey);
}

export function staffAuthHeaders(session: StaffSession | null = getStoredStaffSession()): Record<string, string> {
  return session ? { Authorization: `Bearer ${session.accessToken}` } : {};
}

export function isStaffAuthFailureStatus(status: number): boolean {
  return status === 401 || status === 403;
}

export function staffHasRole(session: StaffSession | null, role: StaffRole): boolean {
  return Boolean(session?.roles.includes(role));
}

export function resolveStaffLandingPath(staff: { roles: StaffRole[]; username?: string }, requestedNext: string | null): string {
  const routeRoles: Array<{ prefix: string; role: StaffRole }> = [
    { prefix: "/dispatcher", role: "dispatcher" },
    { prefix: "/technician", role: "technician" },
    { prefix: "/inventory", role: "inventory" },
    { prefix: "/admin", role: "admin" },
    { prefix: "/owner", role: "admin" },
  ];
  const safeNext = requestedNext?.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : null;
  const matchingRoute = safeNext ? routeRoles.find((route) => safeNext.startsWith(route.prefix)) : undefined;
  if (safeNext && matchingRoute && staff.roles.includes(matchingRoute.role)) return safeNext;
  if (staff.roles.length > 1) return staffWorkspacePath;
  if (staff.roles.includes("dispatcher")) return "/dispatcher";
  if (staff.roles.includes("technician")) return "/technician";
  if (staff.roles.includes("inventory")) return "/inventory";
  if (staff.roles.includes("admin")) return staffWorkspacePath;
  return "/staff/login";
}

import { ProtectedAdminPage } from "./features/admin/AdminPage";
import { ProtectedDispatcherPage } from "./features/dispatcher/DispatcherPage";
import { ProtectedInventoryPage } from "./features/inventory/InventoryPage";
import { ProtectedOwnerDashboardPage } from "./features/owner/OwnerDashboardPage";
import { PublicLandingPage } from "./features/public/PublicLandingPage";
import { StatusPage } from "./features/public/StatusPage";
import { StaffLoginPage } from "./features/staff-auth/StaffLoginPage";
import { StaffWorkspacePage } from "./features/staff-auth/StaffWorkspacePage";
import { ProtectedTechnicianPage } from "./features/technician/TechnicianPage";
import { staffWorkspacePath } from "./shared/staffAuth";

export { AdminPage, ProtectedAdminPage, buildAdminStaffChangeRequests } from "./features/admin/AdminPage";
export { DispatcherPage, ProtectedDispatcherPage, filterDispatcherItems } from "./features/dispatcher/DispatcherPage";
export { InventoryPage, ProtectedInventoryPage } from "./features/inventory/InventoryPage";
export { OwnerDashboardPage, ProtectedOwnerDashboardPage } from "./features/owner/OwnerDashboardPage";
export { PublicLandingPage, SuccessState, getNextFormStep, validateIntakeStep } from "./features/public/PublicLandingPage";
export { StatusPage } from "./features/public/StatusPage";
export { StaffLoginPage } from "./features/staff-auth/StaffLoginPage";
export { StaffWorkspacePage } from "./features/staff-auth/StaffWorkspacePage";
export { ProtectedTechnicianPage, TechnicianPage } from "./features/technician/TechnicianPage";
export * from "./shared/api";
export * from "./shared/formatters";
export * from "./shared/inventory";
export * from "./shared/staffAuth";
export type * from "./shared/types";

export function App() {
  const pathname = typeof window !== "undefined" ? window.location.pathname : "";
  const isDispatcherRoute = pathname.startsWith("/dispatcher");
  const isTechnicianRoute = pathname.startsWith("/technician");
  const isInventoryRoute = pathname.startsWith("/inventory");
  const isAdminRoute = pathname.startsWith("/admin");
  const isOwnerRoute = pathname.startsWith("/owner");
  const isStaffLoginRoute = pathname.startsWith("/staff/login");
  const isStaffWorkspaceRoute = pathname.startsWith(staffWorkspacePath);
  const isStaffEntryRoute = pathname === "/staff" || pathname === "/staff/";
  const isStatusRoute = pathname.startsWith("/status");

  if (isStaffLoginRoute) return <StaffLoginPage />;
  if (isStaffWorkspaceRoute || isStaffEntryRoute) return <StaffWorkspacePage />;
  if (isAdminRoute) return <ProtectedAdminPage />;
  if (isOwnerRoute) return <ProtectedOwnerDashboardPage />;
  if (isDispatcherRoute) return <ProtectedDispatcherPage />;
  if (isTechnicianRoute) return <ProtectedTechnicianPage />;
  if (isInventoryRoute) return <ProtectedInventoryPage />;
  if (isStatusRoute) return <StatusPage />;

  return <PublicLandingPage />;
}

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { App } from "./App";
import {
  AdminPage,
  ProtectedAdminPage,
  buildAdminStaffChangeRequests,
  buildTechnicianProfilePayload,
  canEditTechnicianProfile,
  redirectOnAdminAuthFailure,
} from "./features/admin/AdminPage";
import { AssistantPage, ProtectedAssistantPage, shouldRedirectAssistantResponse } from "./features/assistant/AssistantPage";
import {
  DispatcherPage,
  ProtectedDispatcherPage,
  buildTechnicianRecommendationSelection,
  buildVisitWindowDateTime,
  filterDispatcherItems,
} from "./features/dispatcher/DispatcherPage";
import { ProtectedInventoryPage, ProtectedProcurementPage } from "./features/inventory/InventoryPage";
import { OwnerDashboardPage, ProtectedOwnerDashboardPage } from "./features/owner/OwnerDashboardPage";
import { StatusPage } from "./features/public/StatusPage";
import { StaffLoginPage } from "./features/staff-auth/StaffLoginPage";
import { StaffWorkspacePage } from "./features/staff-auth/StaffWorkspacePage";
import { ProtectedTechnicianPage } from "./features/technician/TechnicianPage";
import { SuccessState, getNextFormStep, validateIntakeStep } from "./features/public/PublicLandingPage";
import {
  buildAcceptAiClarificationPath,
  buildAdminStaffActivatePath,
  buildAdminStaffAuditPath,
  buildAdminStaffDeactivatePath,
  buildAdminStaffPath,
  buildAdminStaffProfilePath,
  buildAdminStaffResetPasswordPath,
  buildAdminStaffRolesPath,
  buildAdminTechnicianProfilePath,
  buildAdminTechnicianProfilesPath,
  buildAssistantConfirmPath,
  buildAssistantRunsPath,
  buildCustomerAnswerPayload,
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
  buildDispatcherTechnicianRecommendationsPath,
  buildGenerateAiSuggestionsPath,
  buildIgnoreAiSuggestionPath,
  buildInventoryPartCompatibilityPath,
  buildInventoryPartsPath,
  buildInventoryProcurementLowStockDraftPath,
  buildInventoryProcurementPurchaseRequestApprovePath,
  buildInventoryProcurementPurchaseRequestCancelPath,
  buildInventoryProcurementPurchaseRequestItemsPath,
  buildInventoryProcurementPurchaseRequestMarkOrderedPath,
  buildInventoryProcurementPurchaseRequestReceivePath,
  buildInventoryProcurementPurchaseRequestsPath,
  buildInventoryProcurementPurchaseRequestSubmitPath,
  buildInventoryProcurementSuppliersPath,
  buildInventoryStockPath,
  buildOwnerDailyReportPath,
  buildOwnerDashboardPath,
  buildServiceRequestPayload,
  buildStatusLookupPath,
  buildTechnicianDetailPath,
  buildTechnicianDiagnosisPath,
  buildTechnicianListPath,
  buildTechnicianPartsUsedPath,
  buildTechnicianResultPath,
  buildTechnicianSchedulePath,
  buildTelegramOptInPayload,
  normalizeRequestNumber,
  replaceStatusLookupRoute,
  replaceStatusRoute,
  resolveApiBaseUrl,
  statusLookupValueFromPath,
  statusPathFromRequestNumber,
  telegramOptInPathFromRequestNumber,
} from "./shared/api";
import { buildInventoryCompatibilityLabel, buildInventoryPartSpecLabel } from "./shared/formatters";
import { buildInventorySkuSuggestion } from "./shared/inventory";
import type { AssistantRunResponse, OwnerDashboardResponse } from "./shared/types";
import {
  buildStaffLoginPath,
  getStoredStaffSession,
  redirectOnStaffAuthFailure,
  isStaffAuthFailureStatus,
  resolveStaffLandingPath,
  staffAuthHeaders,
} from "./shared/staffAuth";

function mediaQueryRules(css: string, query: string): string {
  const queryStart = css.indexOf(`@media ${query}`);
  assert.notEqual(queryStart, -1);
  const queryEnd = css.indexOf("@media", queryStart + 1);
  return css.slice(queryStart, queryEnd === -1 ? undefined : queryEnd);
}

function cssRuleBody(css: string, selector: string): string {
  const selectorStart = css.indexOf(selector);
  assert.notEqual(selectorStart, -1);
  const bodyStart = css.indexOf("{", selectorStart + selector.length);
  const bodyEnd = css.indexOf("}", bodyStart + 1);
  assert.notEqual(bodyStart, -1);
  assert.notEqual(bodyEnd, -1);
  return css.slice(bodyStart + 1, bodyEnd);
}

describe("App", () => {
  const dispatcherDetail = {
    request_number: "CFX-20260605-000001",
    status: "visit_scheduled" as const,
    customer: {
      name: "Anna Petrova",
      phone: "+7 999 111-22-33",
      telegram: "@anna_fix",
      client_type: "coffee_shop" as const,
    },
    machine: {
      brand: "Jura",
      model: "E8",
      location_type: "coffee_shop" as const,
    },
    problem: "Machine leaks water under the brew group.",
    address: "Tverskaya district",
    urgency: "today" as const,
    created_at: "2026-06-05 10:00:00",
    timeline: [
      {
        status: "new" as const,
        title: "Заявка создана",
        description: "Мы получили обращение.",
        actor: "system",
        created_at: "2026-06-05 10:00:00",
      },
      {
        status: "visit_scheduled" as const,
        title: "Визит запланирован",
        description: "Диспетчер назначил мастера.",
        actor: "dispatcher",
        created_at: "2026-06-05 10:15:00",
      },
      {
        status: "diagnostics" as const,
        title: "Диагностика начата",
        description: "Мастер проверяет кофемашину.",
        actor: "technician",
        created_at: "2026-06-05 10:30:00",
      },
    ],
    clarification: {
      question_id: 4,
      question: "Пришлите фото шильдика с моделью кофемашины.",
      answer: null,
      answered_at: null,
    },
    clarification_history: [
      {
        question_id: 3,
        question: "Когда появилась протечка?",
        answer: "Сегодня утром.",
        answered_at: "2026-06-05 10:18:00",
      },
      {
        question_id: 4,
        question: "Пришлите фото шильдика с моделью кофемашины.",
        answer: null,
        answered_at: null,
      },
    ],
    assignment: {
      technician_name: "Pavel Sokolov",
      technician_phone: "+7 999 222-33-44",
      technician_region: "ЦАО",
      visit_window: "Завтра 14:00-16:00",
    },
    internal_notes: [
      {
        note: "Клиент просит звонить после 12:00.",
        actor: "dispatcher",
        created_at: "2026-06-05 10:20:00",
      },
    ],
    ai_suggestions: [
      {
        suggestion_id: 11,
        kind: "diagnostic_question" as const,
        title: "Уточнить перегрев",
        content: "Когда именно перегревается группа?",
        rationale: "Диспетчер должен подтвердить вопрос.",
        confidence: 0.78,
        status: "pending" as const,
        source_chunks: [
          {
            document_title: "E61 overheating repair guide",
            source_uri: "seed://repair/e61-overheating",
            chunk_id: 5,
            score: 0.82,
          },
        ],
        created_at: "2026-06-05 10:25:00",
        acted_at: null,
      },
      {
        suggestion_id: 12,
        kind: "customer_reply" as const,
        title: "Черновик ответа",
        content: "Спасибо, мы уточним режим перегрева.",
        rationale: "Диспетчер редактирует и отправляет вручную.",
        confidence: 0.7,
        status: "ignored" as const,
        source_chunks: [],
        created_at: "2026-06-05 10:26:00",
        acted_at: "2026-06-05 10:27:00",
      },
    ],
    notification_deliveries: [
      {
        event_id: "CFX-20260605-000001:service_request.created:1",
        event_type: "service_request.created",
        status: "sent",
        channel: "telegram",
        provider_message_id: "tg-123",
        error: null,
        attempt_count: 1,
        created_at: "2026-06-05 10:01:00",
        updated_at: "2026-06-05 10:01:02",
      },
    ],
  };

  it("renders the Figma reference public service page", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /CoffeeFix Pro/);
    assert.match(html, /Москва и МО/);
    assert.match(html, /Пн-Вс 08:00-22:00/);
    assert.match(html, /Ремонт кофемашин<br\/>с выездом мастера/);
    assert.match(html, /Выезд в день обращения/);
    assert.match(html, /Заявка на ремонт кофемашины/);
    assert.match(html, /Имя/);
    assert.match(html, /Телефон/);
    assert.match(html, /Telegram/);
    assert.match(html, /Тип клиента/);
    assert.match(html, /Кофемашина и проблема/);
    assert.match(html, /Адрес и время/);
    assert.match(html, /Какие кофемашины ремонтируем/);
    assert.match(html, /Частые неисправности/);
    assert.match(html, /Как проходит ремонт/);
    assert.match(html, /Почему выбирают нас/);
    assert.match(html, /href="\/status">Статус заявки/);
    assert.doesNotMatch(html, /Пример страницы статуса/);
    assert.doesNotMatch(html, /Есть ли ошибка на дисплее/);
    assert.match(html, /Кофемашина не работает/);
    assert.match(html, /© 2026 CoffeeFix Pro/);
    assert.doesNotMatch(html, /© 2024 CoffeeFix Pro/);
    assert.doesNotMatch(html, /\bAI\b/i);
  });

  it("does not draw connector lines through repair step text", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");

    assert.match(css, /\.repair-step::after/);
    assert.doesNotMatch(css, /\.repair-step:not\(:last-child\)::after/);
    assert.match(css, /top: 54px;/);
    assert.match(css, /left: 0;/);
    assert.match(css, /width: calc\(100% - 68px\);/);
    assert.doesNotMatch(css, /\.repair-step\s*{[^}]*background:/s);
    assert.doesNotMatch(css, /\.repair-step\s*{[^}]*border:/s);
  });

  it("configures nginx to serve React routes directly", () => {
    const dockerfile = readFileSync(new URL("../Dockerfile", import.meta.url), "utf-8");
    const nginxConfig = readFileSync(new URL("../nginx.conf", import.meta.url), "utf-8");

    assert.match(dockerfile, /COPY public \.\/public/);
    assert.match(dockerfile, /COPY nginx\.conf \/etc\/nginx\/conf\.d\/default\.conf/);
    assert.match(nginxConfig, /try_files \/index\.html =404;/);
    assert.match(nginxConfig, /location \/ {\s*return 404;\s*}/);
  });

  it("renders the success state with a request number and a new request action", () => {
    const html = renderToStaticMarkup(<SuccessState requestNumber="CFX-20260605-000001" />);

    assert.match(html, /Заявка CFX-20260605-000001 создана/);
    assert.match(html, /Диспетчер проверит описание/);
    assert.match(html, /Открыть страницу статуса/);
    assert.match(html, /Подключить Telegram-уведомления/);
    assert.match(html, /Создать новую заявку/);
    assert.match(html, /href="\/status\/CFX-20260605-000001"/);
    assert.match(html, /<button class="ghost-action" type="button">/);
    assert.doesNotMatch(html, /href="\/service-requests\/CFX-20260605-000001\/telegram-opt-in"/);
  });

  it("keeps main request actions routable to the home form", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /class="brand" href="\/"/);
    assert.match(html, /class="service-mini-cta" href="\/#request-form"/);
    assert.match(html, /class="header-cta" href="\/#request-form"/);
    assert.match(html, /class="primary-cta" href="\/#request-form"/);
    assert.match(html, /class="secondary-cta" href="\/status"/);
    assert.match(html, /Проверить статус заявки/);
    assert.doesNotMatch(html, /Рассчитать стоимость/);
    assert.match(html, /href="\/#request-form">Оставить заявку<\/a>/);
    assert.doesNotMatch(html, /href="\/staff\/login/);
    assert.doesNotMatch(html, /href="\/dispatcher/);
    assert.doesNotMatch(html, /href="\/admin/);
    assert.doesNotMatch(html, /href="\/technician/);
    assert.doesNotMatch(html, /href="\/inventory/);
  });

  it("uses the wide hero image without cropping it", () => {
    const html = renderToStaticMarkup(<App />);
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");

    assert.match(html, /srcSet="\/assets\/hero-coffee-service-wide-desktop\.webp"/);
    assert.match(html, /srcSet="\/assets\/hero-coffee-service-wide-mobile\.webp"/);
    assert.match(html, /src="\/assets\/hero-coffee-service-wide\.png"/);
    assert.match(css, /\.hero-media img\s*{[^}]*object-fit: contain;/s);
    assert.doesNotMatch(css, /\.hero-media img\s*{[^}]*object-fit: cover;/s);
  });

  it("keeps the footer CTA text readable on hover", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");

    assert.match(css, /\.footer-cta a:hover\s*{[^}]*color: #5a3825;/s);
    assert.match(css, /\.footer-cta a:hover\s*{[^}]*background: #ffffff;/s);
  });

  it("keeps the address step reachable before submit", () => {
    assert.equal(getNextFormStep(1), 2);
    assert.equal(getNextFormStep(2), 3);
    assert.equal(getNextFormStep(3), 3);
  });

  it("does not expose a photo or video block in the intake form", () => {
    const source = readFileSync(new URL("./features/public/PublicLandingPage.tsx", import.meta.url), "utf-8");

    assert.doesNotMatch(source, /Фото или видео/);
    assert.doesNotMatch(source, /leak\.jpg/);
    assert.doesNotMatch(source, /image\/jpeg/);
    assert.doesNotMatch(source, /attachment-grid/);
  });

  it("blocks moving to the next intake step until required fields are filled", () => {
    const emptyForm = {
      name: "",
      phone: "",
      telegram: "",
      clientType: "private" as const,
      brand: "",
      model: "",
      locationType: "home" as const,
      problem: "",
      address: "",
      visitTime: "",
      comment: "",
      urgency: "one_two_days" as const,
    };

    assert.deepEqual(validateIntakeStep(emptyForm, 1), ["Имя", "Телефон"]);
    assert.deepEqual(validateIntakeStep({ ...emptyForm, name: "Anna", phone: "+7 999 111-22-33" }, 1), []);
    assert.deepEqual(validateIntakeStep(emptyForm, 2), ["Бренд кофемашины", "Комментарий"]);
    assert.deepEqual(validateIntakeStep({ ...emptyForm, brand: "Jura", problem: "Течет вода" }, 2), []);
    assert.deepEqual(validateIntakeStep(emptyForm, 3), ["Район или адрес"]);
    assert.deepEqual(validateIntakeStep({ ...emptyForm, address: "Тверская" }, 3), []);
  });

  it("maps form state to the API intake contract", () => {
    const payload = buildServiceRequestPayload({
      name: "Anna Petrova",
      phone: "+7 999 111-22-33",
      telegram: "@anna_fix",
      clientType: "coffee_shop",
      brand: "Jura",
      model: "E8",
      locationType: "coffee_shop",
      problem: "Leaking water",
      address: "Tverskaya district",
      visitTime: "",
      comment: "",
      urgency: "today",
    });

    assert.deepEqual(payload, {
      customer: {
        name: "Anna Petrova",
        phone: "+7 999 111-22-33",
        telegram: "@anna_fix",
        client_type: "coffee_shop",
      },
      machine: {
        brand: "Jura",
        model: "E8",
        location_type: "coffee_shop",
      },
      problem: "Leaking water",
      address: "Tverskaya district",
      urgency: "today",
    });
  });

  it("builds public status and notification API paths", () => {
    assert.equal(normalizeRequestNumber(" cfx-20260605-000001 "), "CFX-20260605-000001");
    assert.equal(statusPathFromRequestNumber("CFX-20260605-000001"), "/status/CFX-20260605-000001");
    assert.equal(statusLookupValueFromPath("/status/CFX-20260605-000001"), "CFX-20260605-000001");
    assert.equal(statusLookupValueFromPath("/status/status_aBc123"), "status_aBc123");
    assert.equal(statusLookupValueFromPath("/status"), null);
    assert.equal(statusLookupValueFromPath("/contacts"), null);
    assert.equal(
      buildStatusLookupPath(" cfx-20260605-000001 "),
      "/service-requests/CFX-20260605-000001/status",
    );
    assert.equal(buildStatusLookupPath(" status_aBc123 "), "/status/status_aBc123");
    assert.equal(
      telegramOptInPathFromRequestNumber("CFX-20260605-000001"),
      "/service-requests/CFX-20260605-000001/telegram-opt-in",
    );
    assert.deepEqual(buildCustomerAnswerPayload(12, "  Ошибка E8  "), {
      question_id: 12,
      answer: "Ошибка E8",
    });
    assert.deepEqual(buildTelegramOptInPayload(" @anna_fix "), {
      telegram: "@anna_fix",
    });
  });

  it("keeps the looked-up public status route refreshable", () => {
    const previousWindow = globalThis.window;
    const calls: unknown[][] = [];
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        location: {
          pathname: "/status",
        },
        history: {
          replaceState: (...args: unknown[]) => calls.push(args),
        },
      },
    });

    try {
      replaceStatusRoute(" cfx-20260605-000001 ");
      assert.deepEqual(calls, [[null, "", "/status/CFX-20260605-000001"]]);

      calls.length = 0;
      Object.defineProperty(globalThis.window, "location", {
        configurable: true,
        value: {
          pathname: "/status/CFX-20260605-000001",
        },
      });
      replaceStatusRoute("CFX-20260605-000001");
      assert.deepEqual(calls, []);

      replaceStatusLookupRoute();
      assert.deepEqual(calls, [[null, "", "/status"]]);
    } finally {
      Object.defineProperty(globalThis, "window", { configurable: true, value: previousWindow });
    }
  });

  it("uses the API port fallback for local Vite development", () => {
    assert.equal(resolveApiBaseUrl(undefined, "http://localhost:3000"), "http://localhost:8000");
    assert.equal(resolveApiBaseUrl(undefined, "http://127.0.0.1:3000"), "http://127.0.0.1:8000");
    assert.equal(resolveApiBaseUrl("https://api.example.test", "http://localhost:3000"), "https://api.example.test");
    assert.equal(resolveApiBaseUrl(undefined, "https://coffeefix.example"), "");
  });

  it("builds dispatcher API paths", () => {
    assert.equal(buildDispatcherListPath(), "/dispatcher/service-requests");
    assert.equal(buildDispatcherSchedulePath(), "/dispatcher/schedule");
    assert.equal(buildDispatcherTechnicianCandidatesPath(), "/dispatcher/technician-candidates");
    assert.equal(
      buildDispatcherDetailPath(" CFX-20260605-000001 "),
      "/dispatcher/service-requests/CFX-20260605-000001",
    );
    assert.equal(
      buildDispatcherStatusPath("CFX-20260605-000001"),
      "/dispatcher/service-requests/CFX-20260605-000001/status",
    );
    assert.equal(
      buildDispatcherClarificationPath("CFX-20260605-000001"),
      "/dispatcher/service-requests/CFX-20260605-000001/clarifications",
    );
    assert.equal(
      buildDispatcherAssignmentPath("CFX-20260605-000001"),
      "/dispatcher/service-requests/CFX-20260605-000001/assignment",
    );
    assert.equal(
      buildDispatcherInternalNotePath("CFX-20260605-000001"),
      "/dispatcher/service-requests/CFX-20260605-000001/internal-notes",
    );
    assert.equal(
      buildDispatcherAppointmentPath(" cfx-20260605-000001 "),
      "/dispatcher/service-requests/CFX-20260605-000001/appointments",
    );
    assert.equal(
      buildDispatcherAppointmentReschedulePath("CFX-20260605-000001", 7),
      "/dispatcher/service-requests/CFX-20260605-000001/appointments/7/reschedule",
    );
    assert.equal(
      buildDispatcherAppointmentCancelPath("CFX-20260605-000001", 7),
      "/dispatcher/service-requests/CFX-20260605-000001/appointments/7/cancel",
    );
    assert.equal(
      buildGenerateAiSuggestionsPath("CFX-20260605-000001"),
      "/dispatcher/service-requests/CFX-20260605-000001/ai-suggestions/generate",
    );
    assert.equal(
      buildAcceptAiClarificationPath("CFX-20260605-000001", 11),
      "/dispatcher/service-requests/CFX-20260605-000001/ai-suggestions/11/accept-clarification",
    );
    assert.equal(
      buildIgnoreAiSuggestionPath("CFX-20260605-000001", 12),
      "/dispatcher/service-requests/CFX-20260605-000001/ai-suggestions/12/ignore",
    );
    assert.equal(
      buildDispatcherTechnicianRecommendationsPath(" cfx-20260605-000001 "),
      "/dispatcher/service-requests/CFX-20260605-000001/technician-recommendations",
    );
    assert.equal(
      buildDispatcherTechnicianRecommendationsPath(
        "CFX-20260605-000001",
        "2026-06-19T10:00:00+03:00",
        "2026-06-19T12:00:00+03:00",
      ),
      "/dispatcher/service-requests/CFX-20260605-000001/technician-recommendations?starts_at=2026-06-19T10%3A00%3A00%2B03%3A00&ends_at=2026-06-19T12%3A00%3A00%2B03%3A00",
    );
  });

  it("builds technician and inventory API paths", () => {
    assert.equal(buildTechnicianListPath(), "/technician/service-requests");
    assert.equal(buildTechnicianSchedulePath(), "/technician/schedule");
    assert.equal(
      buildTechnicianDetailPath(" CFX-20260605-000001 "),
      "/technician/service-requests/CFX-20260605-000001",
    );
    assert.equal(
      buildTechnicianDiagnosisPath("CFX-20260605-000001"),
      "/technician/service-requests/CFX-20260605-000001/diagnosis",
    );
    assert.equal(
      buildTechnicianResultPath("CFX-20260605-000001"),
      "/technician/service-requests/CFX-20260605-000001/result",
    );
    assert.equal(
      buildTechnicianPartsUsedPath("CFX-20260605-000001"),
      "/technician/service-requests/CFX-20260605-000001/parts-used",
    );
    assert.equal(buildInventoryPartsPath(), "/inventory/parts");
    assert.equal(buildInventoryStockPath(7), "/inventory/parts/7/stock");
    assert.equal(buildInventoryPartCompatibilityPath(7), "/inventory/parts/7/compatibility");
    assert.equal(buildInventoryProcurementSuppliersPath(), "/inventory/procurement/suppliers");
    assert.equal(buildInventoryProcurementPurchaseRequestsPath(), "/inventory/procurement/purchase-requests");
    assert.equal(buildInventoryProcurementLowStockDraftPath(), "/inventory/procurement/purchase-requests/low-stock-draft");
    assert.equal(buildInventoryProcurementPurchaseRequestItemsPath(9), "/inventory/procurement/purchase-requests/9/items");
    assert.equal(buildInventoryProcurementPurchaseRequestSubmitPath(9), "/inventory/procurement/purchase-requests/9/submit");
    assert.equal(buildInventoryProcurementPurchaseRequestApprovePath(9), "/inventory/procurement/purchase-requests/9/approve");
    assert.equal(buildInventoryProcurementPurchaseRequestMarkOrderedPath(9), "/inventory/procurement/purchase-requests/9/mark-ordered");
    assert.equal(buildInventoryProcurementPurchaseRequestReceivePath(9), "/inventory/procurement/purchase-requests/9/receive");
    assert.equal(buildInventoryProcurementPurchaseRequestCancelPath(9), "/inventory/procurement/purchase-requests/9/cancel");
  });

  it("builds staff login paths and auth headers", () => {
    assert.equal(buildStaffLoginPath("/dispatcher"), "/staff/login?next=%2Fdispatcher");
    assert.equal(buildStaffLoginPath("/dispatcher/service-requests"), "/staff/login?next=%2Fdispatcher%2Fservice-requests");
    assert.deepEqual(staffAuthHeaders(null), {});
    assert.deepEqual(staffAuthHeaders({ accessToken: "staff-token", username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }), {
      Authorization: "Bearer staff-token",
    });
  });

  it("treats unauthorized staff API responses as session failures", () => {
    assert.equal(isStaffAuthFailureStatus(401), true);
    assert.equal(isStaffAuthFailureStatus(403), true);
    assert.equal(isStaffAuthFailureStatus(409), false);
    assert.equal(isStaffAuthFailureStatus(500), false);
  });

  it("clears stale staff sessions and redirects to login on auth failures", () => {
    const storage = new Map<string, string>();
    const fakeStorage = {
      get length() {
        return storage.size;
      },
      clear: () => storage.clear(),
      getItem: (key: string) => storage.get(key) ?? null,
      key: (index: number) => Array.from(storage.keys())[index] ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    } as Storage;
    const fakeLocation = { href: "" };
    fakeStorage.setItem(
      "serviceops.staffSession",
      JSON.stringify({ accessToken: "expired", username: "inventory@coffeefix.local", roles: ["inventory"] }),
    );

    assert.equal(redirectOnStaffAuthFailure(401, "/inventory", fakeStorage, fakeLocation), true);

    assert.equal(fakeStorage.getItem("serviceops.staffSession"), null);
    assert.equal(fakeLocation.href, "/staff/login?next=%2Finventory");
    assert.equal(redirectOnStaffAuthFailure(500, "/inventory", fakeStorage, fakeLocation), false);
  });

  it("redirects stale admin sessions instead of rendering an empty staff workspace", () => {
    const storage = new Map<string, string>();
    const fakeStorage = {
      get length() {
        return storage.size;
      },
      clear: () => storage.clear(),
      getItem: (key: string) => storage.get(key) ?? null,
      key: (index: number) => Array.from(storage.keys())[index] ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    } as Storage;
    const fakeLocation = { href: "" };
    fakeStorage.setItem(
      "serviceops.staffSession",
      JSON.stringify({ accessToken: "expired-admin", username: "admin@coffeefix.local", roles: ["admin"] }),
    );

    assert.equal(redirectOnAdminAuthFailure(401, fakeStorage, fakeLocation), true);

    assert.equal(fakeStorage.getItem("serviceops.staffSession"), null);
    assert.equal(fakeLocation.href, "/staff/login?next=%2Fadmin");
    assert.equal(redirectOnAdminAuthFailure(500, fakeStorage, fakeLocation), false);
  });

  it("builds admin staff management API paths", () => {
    assert.equal(buildAdminStaffPath(), "/admin/staff");
    assert.equal(
      buildAdminStaffRolesPath("admin user@coffeefix.local"),
      "/admin/staff/admin%20user%40coffeefix.local/roles",
    );
    assert.equal(
      buildAdminStaffProfilePath("admin@coffeefix.local"),
      "/admin/staff/admin%40coffeefix.local/profile",
    );
    assert.equal(
      buildAdminStaffActivatePath("admin@coffeefix.local"),
      "/admin/staff/admin%40coffeefix.local/activate",
    );
    assert.equal(
      buildAdminStaffDeactivatePath("admin@coffeefix.local"),
      "/admin/staff/admin%40coffeefix.local/deactivate",
    );
    assert.equal(
      buildAdminStaffResetPasswordPath("admin@coffeefix.local"),
      "/admin/staff/admin%40coffeefix.local/reset-password",
    );
    assert.equal(buildAdminStaffAuditPath(), "/admin/staff/audit");
    assert.equal(buildAdminTechnicianProfilesPath(), "/admin/technician-profiles");
    assert.equal(
      buildAdminTechnicianProfilePath("tech@coffeefix.local"),
      "/admin/technician-profiles/tech%40coffeefix.local",
    );
  });

  it("resolves one staff login landing path by role and validates next routes", () => {
    assert.equal(
      resolveStaffLandingPath({ username: "technician@coffeefix.local", roles: ["technician"] }, null),
      "/technician",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "inventory@coffeefix.local", roles: ["inventory"] }, null),
      "/inventory",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }, null),
      "/dispatcher",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "technician@coffeefix.local", roles: ["technician"] }, "/technician"),
      "/technician",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "technician@coffeefix.local", roles: ["technician"] }, "/dispatcher"),
      "/technician",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "inventory@coffeefix.local", roles: ["inventory"] }, "https://example.test"),
      "/inventory",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, null),
      "/staff/workspace",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/admin"),
      "/admin",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/owner"),
      "/owner",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/inventory"),
      "/inventory",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/procurement"),
      "/procurement",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }, "/assistant"),
      "/assistant",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "inventory@coffeefix.local", roles: ["inventory"] }, "/assistant"),
      "/assistant",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/assistant"),
      "/assistant",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "technician@coffeefix.local", roles: ["technician"] }, "/assistant"),
      "/technician",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "lead@coffeefix.local", roles: ["admin", "dispatcher"] }, "/dispatcher"),
      "/dispatcher",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "lead@coffeefix.local", roles: ["dispatcher", "technician", "inventory"] }, null),
      "/staff/workspace",
    );
  });

  it("reads stored staff sessions safely", () => {
    const emptyStorage = {
      getItem: () => null,
    } as unknown as Storage;
    const populatedStorage = {
      getItem: () =>
        JSON.stringify({
          accessToken: "staff-token",
          username: "dispatcher@coffeefix.local",
          roles: ["dispatcher"],
        }),
    } as unknown as Storage;
    const malformedStorage = {
      getItem: () => "{not-json",
    } as unknown as Storage;

    assert.equal(getStoredStaffSession(emptyStorage), null);
    assert.deepEqual(getStoredStaffSession(populatedStorage), {
      accessToken: "staff-token",
      username: "dispatcher@coffeefix.local",
      roles: ["dispatcher"],
    });
    assert.equal(getStoredStaffSession(malformedStorage), null);
  });

  it("renders staff login and dispatcher route guard", () => {
    const loginHtml = renderToStaticMarkup(<StaffLoginPage />);
    const guardedHtml = renderToStaticMarkup(<ProtectedDispatcherPage hasSession={false} />);
    const wrongRoleHtml = renderToStaticMarkup(
      <ProtectedDispatcherPage
        initialSession={{
          accessToken: "technician-token",
          username: "technician@coffeefix.local",
          roles: ["technician"],
        }}
      />,
    );

    assert.match(loginHtml, /Вход для сотрудников/);
    assert.doesNotMatch(loginHtml, /dispatcher@coffeefix.local/);
    assert.doesNotMatch(loginHtml, /dispatcher-local/);
    assert.match(loginHtml, /Пароль/);
    assert.match(guardedHtml, /Требуется вход сотрудника/);
    assert.match(guardedHtml, /href="\/staff\/login\?next=%2Fdispatcher"/);
    assert.match(wrongRoleHtml, /Недостаточно прав/);
    assert.doesNotMatch(wrongRoleHtml, /Заявки, статусы, уточнения/);
  });

  it("renders a staff workspace chooser for multi-role users", () => {
    const html = renderToStaticMarkup(
      <StaffWorkspacePage
        initialSession={{
          accessToken: "lead-token",
          username: "lead@coffeefix.local",
          roles: ["dispatcher", "technician", "inventory"],
        }}
      />,
    );

    assert.match(html, /Выберите кабинет/);
    assert.match(html, /href="\/dispatcher"/);
    assert.match(html, /Диспетчерская/);
    assert.match(html, /href="\/technician"/);
    assert.match(html, /Кабинет мастера/);
    assert.match(html, /href="\/inventory"/);
    assert.match(html, /Склад/);
    assert.doesNotMatch(html, /href="\/admin"/);
  });

  it("renders procurement as a separate inventory/admin cabinet, not inside the stock cabinet", () => {
    const inventorySession = {
      accessToken: "inventory-token",
      username: "inventory@coffeefix.local",
      roles: ["inventory" as const],
    };
    const workspaceHtml = renderToStaticMarkup(<StaffWorkspacePage initialSession={inventorySession} />);
    const inventoryHtml = renderToStaticMarkup(<ProtectedInventoryPage initialSession={inventorySession} />);
    const procurementHtml = renderToStaticMarkup(<ProtectedProcurementPage initialSession={inventorySession} />);

    assert.match(workspaceHtml, /Согласование закупок/);
    assert.match(workspaceHtml, /href="\/procurement"/);
    assert.doesNotMatch(inventoryHtml, /id="procurement"/);
    assert.doesNotMatch(inventoryHtml, /Создать черновик/);
    assert.match(procurementHtml, /Согласование закупок/);
    assert.match(procurementHtml, /Создать черновик/);
  });

  it("renders procurement as a focused workflow board with collapsible suppliers and clear actions", () => {
    const html = renderToStaticMarkup(
      <ProtectedProcurementPage
        initialSession={{
          accessToken: "inventory-token",
          username: "inventory@coffeefix.local",
          roles: ["inventory"],
        }}
        initialParts={{
          items: [
            {
              part_id: 1,
              sku: "VALVE-01",
              name: "Steam valve",
              brand: "Rocket",
              model: "Appartamento",
              unit: "pcs",
              compatibility_note: null,
              quantity_on_hand: 1,
              reserved_quantity: 0,
              available_quantity: 1,
              low_stock_threshold: 3,
              is_low_stock: true,
              created_at: "2026-06-18 10:00:00",
              stock_updated_at: "2026-06-18 10:00:00",
              compatibility: [],
              part_type: null,
              parameter_label: null,
              parameter_value: null,
              parameter_unit: null,
              factual_key: null,
            },
          ],
        }}
        initialSuppliers={{
          items: [
            {
              supplier_id: 5,
              name: "Supplier One",
              contact_name: "Nora",
              phone: "+101",
              email: null,
              note: null,
              active: true,
              created_at: "2026-06-18 10:00:00",
              updated_at: "2026-06-18 10:00:00",
            },
          ],
        }}
        initialPurchaseRequests={{
          items: [
            {
              purchase_request_id: 13,
              supplier_id: 5,
              supplier_name: "Supplier One",
              status: "draft",
              note: "Draft valves",
              actor: "inventory",
              created_at: "2026-06-18 10:05:00",
              updated_at: "2026-06-18 10:05:00",
              items: [
                {
                  item_id: 22,
                  purchase_request_id: 13,
                  part_id: 1,
                  sku: "VALVE-01",
                  part_name: "Steam valve",
                  unit: "pcs",
                  quantity: 2,
                  note: null,
                },
              ],
            },
          ],
        }}
      />,
    );

    assert.match(html, /<details class="procurement-suppliers-panel">/);
    assert.match(html, /<summary>[\s\S]*Поставщики/);
    assert.match(html, /procurement-draft-panel/);
    assert.match(html, /Создать из низких остатков/);
    assert.match(html, /procurement-board/);
    assert.match(html, /procurement-request-card/);
    assert.match(html, /Отправить на согласование/);
    assert.match(html, /Отменить заявку/);
    assert.match(html, /Заменить строки/);
  });

  it("renders an admin procurement approval workspace card", () => {
    const html = renderToStaticMarkup(
      <StaffWorkspacePage
        initialSession={{
          accessToken: "admin-token",
          username: "admin@coffeefix.local",
          roles: ["admin"],
        }}
      />,
    );

    assert.match(html, /Согласование закупок/);
    assert.match(html, /href="\/procurement"/);
  });

  it("routes procurement approval to a dedicated cabinet", () => {
    const previousWindow = globalThis.window;
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        location: {
          origin: "http://localhost:3000",
          pathname: "/procurement",
          search: "",
        },
        localStorage: {
          getItem: () =>
            JSON.stringify({
              accessToken: "admin-token",
              username: "admin@coffeefix.local",
              roles: ["admin"],
            }),
        },
      },
    });

    try {
      const html = renderToStaticMarkup(<App />);

      assert.match(html, /Согласование закупок/);
      assert.doesNotMatch(html, /<h1>Склад запчастей<\/h1>/);
    } finally {
      Object.defineProperty(globalThis, "window", { configurable: true, value: previousWindow });
    }
  });

  it("routes the /staff/ entry to the workspace chooser for stored multi-role sessions", () => {
    const previousWindow = globalThis.window;
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        location: {
          origin: "http://localhost:3000",
          pathname: "/staff/",
          search: "",
        },
        localStorage: {
          getItem: () =>
            JSON.stringify({
              accessToken: "dispatcher-token",
              username: "dispatcher@coffeefix.local",
              roles: ["admin", "dispatcher", "technician", "inventory"],
            }),
        },
      },
    });

    try {
      const html = renderToStaticMarkup(<App />);

      assert.match(html, /Выберите кабинет/);
      assert.match(html, /href="\/dispatcher"/);
      assert.match(html, /href="\/admin"/);
      assert.match(html, /href="\/technician"/);
      assert.match(html, /href="\/inventory"/);
    } finally {
      Object.defineProperty(globalThis, "window", { configurable: true, value: previousWindow });
    }
  });

  it("renders technician and inventory route guards", () => {
    const technicianGuard = renderToStaticMarkup(<ProtectedTechnicianPage hasSession={false} />);
    const technicianWrongRole = renderToStaticMarkup(
      <ProtectedTechnicianPage
        initialSession={{ accessToken: "dispatcher-token", username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }}
      />,
    );
    const inventoryGuard = renderToStaticMarkup(<ProtectedInventoryPage hasSession={false} />);
    const inventoryWrongRole = renderToStaticMarkup(
      <ProtectedInventoryPage
        initialSession={{ accessToken: "technician-token", username: "technician@coffeefix.local", roles: ["technician"] }}
      />,
    );

    assert.match(technicianGuard, /Требуется вход сотрудника/);
    assert.match(technicianGuard, /href="\/staff\/login\?next=%2Ftechnician"/);
    assert.match(technicianWrongRole, /Для выездов нужна роль technician/);
    assert.match(inventoryGuard, /href="\/staff\/login\?next=%2Finventory"/);
    assert.match(inventoryWrongRole, /Для склада нужна роль inventory/);
  });

  it("renders admin route guard and staff management workspace", () => {
    const adminGuard = renderToStaticMarkup(<ProtectedAdminPage hasSession={false} />);
    const wrongRoleHtml = renderToStaticMarkup(
      <ProtectedAdminPage
        initialSession={{ accessToken: "dispatcher-token", username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }}
      />,
    );
    const workspaceHtml = renderToStaticMarkup(
      <AdminPage
        initialSession={{ accessToken: "admin-token", username: "admin@coffeefix.local", roles: ["admin"] }}
        initialStaff={{
          items: [
            {
              username: "admin@coffeefix.local",
              display_name: "Admin",
              first_name: "Coffee",
              last_name: "Admin",
              phone: "+7 999 000-10-00",
              roles: ["admin"],
              active: true,
              created_at: "2026-06-07 12:00:00",
              updated_at: "2026-06-07 12:00:00",
            },
            {
              username: "tech@coffeefix.local",
              display_name: "Tech",
              first_name: "Field",
              last_name: "Tech",
              phone: "+7 999 000-10-02",
              roles: ["technician"],
              active: false,
              created_at: "2026-06-07 12:00:00",
              updated_at: "2026-06-07 12:10:00",
            },
          ],
        }}
        initialAudit={{
          items: [
            {
              actor_username: "admin@coffeefix.local",
              target_username: "tech@coffeefix.local",
              action: "staff.deactivated",
              metadata: {},
              created_at: "2026-06-07 12:10:00",
            },
          ],
        }}
        initialTechnicianProfiles={{
          items: [
            {
              staff_username: "tech@coffeefix.local",
              display_name: "Tech",
              phone: "+7 999 000-10-02",
              staff_active: false,
              active: true,
              skill_brands: ["Jura", "Rocket"],
              service_regions: ["Tverskaya"],
              notes: "Works central districts.",
              created_at: "2026-06-19 10:00:00",
              updated_at: "2026-06-19 10:00:00",
            },
          ],
        }}
      />,
    );

    assert.match(adminGuard, /Требуется вход сотрудника/);
    assert.match(adminGuard, /href="\/staff\/login\?next=%2Fadmin"/);
    assert.match(wrongRoleHtml, /Для управления сотрудниками нужна роль admin/);
    assert.match(workspaceHtml, /Администрирование/);
    assert.match(workspaceHtml, /Учетные записи сотрудников/);
    assert.match(workspaceHtml, /Новый сотрудник/);
    assert.match(workspaceHtml, /Роли сотрудника/);
    assert.match(workspaceHtml, /admin@coffeefix.local/);
    assert.match(workspaceHtml, /Coffee/);
    assert.match(workspaceHtml, /Admin/);
    assert.match(workspaceHtml, /\+7 999 000-10-00/);
    assert.match(workspaceHtml, /tech@coffeefix.local/);
    assert.match(workspaceHtml, /technician/);
    assert.match(workspaceHtml, /Активировать/);
    assert.match(workspaceHtml, /Сбросить пароль/);
    assert.match(workspaceHtml, /Сохранить изменения/);
    assert.doesNotMatch(workspaceHtml, /Сохранить данные/);
    assert.doesNotMatch(workspaceHtml, /Сохранить роли/);
    assert.match(workspaceHtml, /Имя/);
    assert.match(workspaceHtml, /Фамилия/);
    assert.match(workspaceHtml, /Телефон/);
    assert.match(workspaceHtml, /Аудит действий/);
    assert.match(workspaceHtml, /staff.deactivated/);
    assert.match(workspaceHtml, /Профиль мастера/);
    assert.match(workspaceHtml, /<details class="technician-profile-control"/);
    assert.match(workspaceHtml, /<summary class="technician-profile-summary"/);
    assert.match(workspaceHtml, /Бренды/);
    assert.match(workspaceHtml, /Районы/);
    assert.match(workspaceHtml, /Удалить бренд Jura/);
    assert.match(workspaceHtml, /Удалить бренд Rocket/);
    assert.match(workspaceHtml, /Удалить район Tverskaya/);
    assert.match(workspaceHtml, /Добавить бренд/);
    assert.match(workspaceHtml, /Добавить район/);
    assert.match(workspaceHtml, /Tverskaya/);
    assert.match(workspaceHtml, /class="technician-profile-save" type="button">Сохранить/);
  });

  it("builds trimmed technician profile payloads", () => {
    assert.deepEqual(
      buildTechnicianProfilePayload({
        active: true,
        skillBrands: [" Jura", "jura", "Rocket "],
        serviceRegions: [" Tverskaya", "ЦАО "],
        brandInput: "ignored draft",
        regionInput: "ignored draft",
        notes: "  Senior technician  ",
      }),
      {
        active: true,
        skill_brands: ["Jura", "Rocket"],
        service_regions: ["Tverskaya", "ЦАО"],
        notes: "Senior technician",
      },
    );
  });

  it("shows technician profile editing only for persisted technician staff roles", () => {
    assert.equal(canEditTechnicianProfile(["technician"]), true);
    assert.equal(canEditTechnicianProfile(["dispatcher", "technician"]), true);
    assert.equal(canEditTechnicianProfile(["dispatcher"]), false);
    assert.equal(canEditTechnicianProfile(["admin", "inventory"]), false);
  });

  it("passes preloaded technician profiles through the protected admin page", () => {
    const html = renderToStaticMarkup(
      <ProtectedAdminPage
        initialSession={{ accessToken: "admin-token", username: "admin@coffeefix.local", roles: ["admin"] }}
        initialStaff={{
          items: [
            {
              username: "tech@coffeefix.local",
              display_name: "Tech",
              first_name: "Field",
              last_name: "Tech",
              phone: "+7 999 000-10-02",
              roles: ["technician"],
              active: true,
              created_at: "2026-06-07 12:00:00",
              updated_at: "2026-06-07 12:10:00",
            },
          ],
        }}
        initialAudit={{ items: [] }}
        initialTechnicianProfiles={{
          items: [
            {
              staff_username: "tech@coffeefix.local",
              display_name: "Tech",
              phone: "+7 999 000-10-02",
              staff_active: true,
              active: true,
              skill_brands: ["Nuova Simonelli"],
              service_regions: ["Khamovniki"],
              notes: null,
              created_at: "2026-06-19 10:00:00",
              updated_at: "2026-06-19 10:00:00",
            },
          ],
        }}
      />,
    );

    assert.match(html, /Профиль мастера/);
    assert.match(html, /Nuova Simonelli/);
    assert.match(html, /Khamovniki/);
  });

  it("builds combined admin staff profile and role change requests", () => {
    assert.deepEqual(
      buildAdminStaffChangeRequests(
        "tech@coffeefix.local",
        { firstName: " Иван ", lastName: " Кофеевич ", phone: " +79111111111 " },
        ["dispatcher", "technician"],
      ),
      [
        {
          path: "/admin/staff/tech%40coffeefix.local/profile",
          body: { first_name: "Иван", last_name: "Кофеевич", phone: "+79111111111" },
        },
        {
          path: "/admin/staff/tech%40coffeefix.local/roles",
          body: { roles: ["dispatcher", "technician"] },
        },
      ],
    );
  });

  it("keeps admin staff rows in a responsive editing layout", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");

    assert.match(css, /\.admin-staff-row\s*{[^}]*grid-template-areas:/s);
    assert.match(css, /\.admin-staff-row\s*{[^}]*minmax\(420px, 1fr\)/s);
    assert.match(css, /\.admin-staff-identity\s*{[^}]*grid-area: identity;/s);
    assert.match(css, /\.admin-profile-control\s*{[^}]*grid-area: profile;/s);
    assert.match(css, /\.admin-staff-row \.role-chip-row\s*{[^}]*grid-area: roles;/s);
    assert.match(css, /\.admin-row-actions\s*{[^}]*display: grid;/s);
    assert.match(css, /\.admin-row-actions\s*{[^}]*grid-template-columns: 1fr;/s);
    assert.match(css, /\.admin-row-actions button\s*{[^}]*white-space: nowrap;/s);
    assert.doesNotMatch(
      css,
      /grid-template-columns: minmax\(170px, 0\.75fr\) minmax\(210px, 0\.9fr\) minmax\(210px, 0\.75fr\) minmax\(220px, 0\.7fr\)/,
    );
  });

  it("keeps the public hero balanced on landscape tablets", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");
    const tabletRules = mediaQueryRules(css, "(min-width: 981px) and (max-width: 1100px)");
    assert.match(cssRuleBody(tabletRules, ".hero-inner"), /grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);[\s\S]*gap: 24px;/);
    assert.match(cssRuleBody(tabletRules, ".hero-badges"), /grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
    assert.match(cssRuleBody(tabletRules, ".hero-actions"), /display: grid;[\s\S]*grid-template-columns: minmax\(0, 1\.2fr\) minmax\(0, 1fr\);/);
    assert.match(cssRuleBody(tabletRules, ".hero-actions .primary-cta,\n  .hero-actions .secondary-cta"), /width: 100%;/);
  });

  it("stacks public status content on portrait tablets and compact phones", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");
    const tabletRules = mediaQueryRules(css, "(max-width: 768px)");
    assert.match(cssRuleBody(tabletRules, ".status-lookup,\n  .status-dashboard"), /grid-template-columns: minmax\(0, 1fr\);/);
    assert.match(cssRuleBody(tabletRules, ".telegram-panel"), /grid-column: auto;/);
    assert.match(cssRuleBody(tabletRules, ".status-page .secondary-status-button"), /justify-self: stretch;[\s\S]*width: 100%;/);
    assert.match(cssRuleBody(tabletRules, ".status-page .timeline-item h3,\n  .status-page .timeline-item p"), /overflow-wrap: anywhere;/);
    assert.doesNotMatch(tabletRules, /(?:^|\n)\s{2}\.secondary-status-button\s*{/);

    const phoneRules = mediaQueryRules(css, "(max-width: 620px)");
    assert.match(cssRuleBody(phoneRules, ".status-lookup,\n  .status-summary,\n  .status-panel"), /padding: 20px;/);
    assert.match(
      cssRuleBody(phoneRules, ".status-answer-form .submit-button,\n  .telegram-controls .submit-button"),
      /width: 100%;[\s\S]*min-height: 44px;/,
    );
  });

  it("renders dispatcher list detail and action controls", () => {
    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "visit_scheduled",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialDetail={dispatcherDetail}
        initialTechnicianCandidates={{
          items: [
            {
              username: "dispatcher@coffeefix.local",
              display_name: "Dispatcher",
              phone: "+7 999 111-22-33",
            },
          ],
        }}
      />,
    );

    assert.match(html, /Диспетчерская/);
    assert.match(html, /CFX-20260605-000001/);
    assert.match(html, /Anna Petrova/);
    assert.match(html, /Jura E8/);
    assert.match(html, /Сегодня/);
    assert.match(html, /Machine leaks water under the brew group./);
    assert.match(html, /Пришлите фото шильдика/);
    assert.match(html, /Pavel Sokolov/);
    assert.match(html, /\+7 999 222-33-44/);
    assert.match(html, /Завтра 14:00-16:00/);
    assert.match(html, /Выберите мастера из списка/);
    assert.match(html, /aria-label="Кандидат мастера"/);
    assert.match(html, /Dispatcher/);
    assert.match(html, /dispatcher@coffeefix.local/);
    assert.match(html, /\+7 999 111-22-33/);
    assert.doesNotMatch(html, /class="technician-candidates"/);
    assert.doesNotMatch(html, /Sergey Morozov/);
    assert.match(html, /Клиент просит звонить после 12:00./);
    assert.match(html, /Обновить статус/);
    assert.match(html, /Клиент увидит эти заголовок и описание в истории статуса/);
    assert.match(html, /Заголовок для клиента/);
    assert.match(html, /Описание для клиента/);
    assert.match(html, /Задать вопрос клиенту/);
    assert.match(html, /Переписка с клиентом/);
    assert.match(html, /Вопрос сотрудника/);
    assert.match(html, /Когда появилась протечка/);
    assert.match(html, /Ответ клиента/);
    assert.match(html, /Сегодня утром/);
    assert.match(html, />Визит</);
    assert.match(html, /Назначить мастера/);
    assert.match(html, /Создать визит/);
    assert.doesNotMatch(html, />Назначение</);
    assert.doesNotMatch(html, />Расписание визита</);
    assert.match(html, /Сохранить заметку/);
    assert.match(html, /AI-подсказки/);
    assert.match(html, /Нажмите, чтобы открыть AI-ассистента/);
    assert.match(html, /<details class="dispatcher-card ai-suggestions-panel">/);
    assert.match(html, /Уточнить перегрев/);
    assert.match(html, /Когда именно перегревается группа/);
    assert.match(html, /Подробнее/);
    assert.match(html, /Принять как вопрос/);
    assert.match(html, /E61 overheating repair guide/);
    assert.match(html, /Черновик ответа/);
    assert.match(html, /Игнорировано/);
    assert.match(html, /Последние события/);
    assert.match(html, /Остальные события \(1\)/);
    assert.match(html, /Технический лог/);
    assert.doesNotMatch(html, /class="notification-delivery-panel"/);

    const aiIndex = html.indexOf("AI-подсказки");
    const statusIndex = html.indexOf("Обновить статус");
    const questionIndex = html.indexOf("Вопрос клиенту");
    const visitIndex = html.indexOf(">Визит<");
    const notesIndex = html.indexOf("Внутренние заметки");
    const eventsIndex = html.indexOf("Последние события");

    assert.ok(aiIndex > 0);
    assert.ok(aiIndex < statusIndex);
    assert.ok(statusIndex < questionIndex);
    assert.ok(questionIndex < visitIndex);
    assert.ok(visitIndex < notesIndex);
    assert.ok(notesIndex < eventsIndex);
  });

  it("renders explainable technician recommendations without automatic assignment", () => {
    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "awaiting_assignment",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Готово к назначению",
            },
          ],
        }}
        initialDetail={{
          ...dispatcherDetail,
          status: "awaiting_assignment",
          assignment: {
            technician_name: null,
            technician_phone: null,
            technician_region: null,
            visit_window: null,
          },
          appointment: null,
        }}
        initialTechnicianRecommendations={{
          request: {
            request_number: "CFX-20260605-000001",
            brand: "Jura",
            model: "E8",
            address: "Tverskaya district",
            urgency: "today",
            status: "awaiting_assignment",
          },
          items: [
            {
              staff_username: "pavel@coffeefix.local",
              display_name: "Pavel Sokolov",
              phone: "+7 999 222-33-44",
              score: 110,
              active: true,
              staff_active: true,
              skill_brands: ["Jura"],
              service_regions: ["Tverskaya"],
              scheduled_visit_count: 0,
              reasons: ["Brand match: Jura", "Region match: Tverskaya"],
              risks: [
                "No appointment window provided; schedule conflict will be checked when booking",
                "Active scheduled visits: 2",
                "Region mismatch for request address",
                "Profile is inactive",
              ],
            },
          ],
        }}
      />,
    );

    assert.match(html, /Рекомендации мастера/);
    assert.match(html, /Pavel Sokolov/);
    assert.match(html, /pavel@coffeefix.local/);
    assert.match(html, /Brand match: Jura/);
    assert.match(html, /Region match: Tverskaya/);
    assert.match(html, /schedule conflict will be checked/);
    assert.match(html, /Profile is inactive/);
    assert.match(html, /Использовать в форме/);
    assert.match(html, /Назначить мастера/);
    assert.doesNotMatch(html, /Назначено автоматически/);
  });

  it("maps a technician recommendation into manual assignment form fields only", () => {
    assert.deepEqual(
      buildTechnicianRecommendationSelection({
        staff_username: "pavel@coffeefix.local",
        display_name: "Pavel Sokolov",
        phone: "+7 999 111-22-33",
        score: 120,
        active: true,
        staff_active: true,
        skill_brands: ["Jura"],
        service_regions: ["Tverskaya", "ЦАО"],
        scheduled_visit_count: 0,
        reasons: ["Brand match: Jura"],
        risks: [],
      }),
      {
        technicianName: "pavel@coffeefix.local",
        technicianPhone: "+7 999 111-22-33",
        technicianRegion: "Tverskaya",
        appointmentTechnician: "pavel@coffeefix.local",
        appointmentName: "Pavel Sokolov",
      },
    );
  });

  it("renders dispatcher schedule and appointment controls", () => {
    const appointment = {
      appointment_id: 7,
      request_number: "CFX-20260605-000001",
      technician_identifier: "technician@coffeefix.local",
      technician_name: "Pavel Sokolov",
      starts_at: "2026-06-16T14:00:00+03:00",
      ends_at: "2026-06-16T16:00:00+03:00",
      window_label: "16 июня 14:00-16:00",
      status: "scheduled" as const,
      reschedule_reason: null,
      cancel_reason: null,
      created_at: "2026-06-15 10:00:00",
      updated_at: "2026-06-15 10:00:00",
    };

    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "visit_scheduled",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialSchedule={{
          items: [
            {
              appointment,
              request_status: "visit_scheduled",
              customer_name: "Anna Petrova",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialDetail={{ ...dispatcherDetail, appointment }}
      />,
    );

    assert.match(html, /Расписание/);
    assert.match(html, /16 июня 14:00-16:00/);
    assert.match(html, /technician@coffeefix\.local/);
    assert.match(html, /Создать новое окно/);
    assert.match(html, /Перенести визит/);
    assert.match(html, /Отменить визит/);
    assert.match(html, /Дата визита/);
    assert.match(html, /Время с/);
    assert.match(html, /Время по/);
    assert.match(html, /Новая дата визита/);
    assert.match(html, /Новое время с/);
    assert.match(html, /Новое время по/);
    assert.match(html, /type="date"/);
    assert.match(html, /type="time"/);
    assert.doesNotMatch(html, /datetime-local/);
    assert.doesNotMatch(html, />Назначение</);
    assert.doesNotMatch(html, />Расписание визита</);
    assert.match(html, /Логин мастера/);
    assert.doesNotMatch(html, /Начало ISO/);
    assert.doesNotMatch(html, /Конец ISO/);
  });

  it("builds visit window datetimes from one date and start/end times", () => {
    assert.equal(buildVisitWindowDateTime("2026-06-16", "14:00"), "2026-06-16T14:00");
    assert.equal(buildVisitWindowDateTime(" 2026-06-16 ", " 16:30 "), "2026-06-16T16:30");
    assert.equal(buildVisitWindowDateTime("", "14:00"), "");
    assert.equal(buildVisitWindowDateTime("2026-06-16", ""), "");
  });

  it("shows customer-safe appointment timing on public status", () => {
    const html = renderToStaticMarkup(
      <StatusPage
        initialStatus={{
          request_number: "CFX-20260615-000022",
          public_token: "status_token",
          status: "visit_scheduled",
          customer: { name: "test", phone_masked: "***", telegram: null },
          machine: { brand: "Nuova Simonelli", model: null },
          problem_summary: "кофемашина загорелась без причины",
          timeline: [
            {
              status: "visit_scheduled",
              title: "Визит запланирован",
              description: "Диспетчер назначил мастера и обновил следующий шаг по заявке.",
              actor: "dispatcher",
              created_at: "2026-06-15 15:56:00",
            },
          ],
          clarification: null,
          telegram_opt_in: { enabled: false, link: "/service-requests/CFX-20260615-000022/telegram-opt-in" },
          appointment: {
            starts_at: null,
            ends_at: null,
            window_label: "11:00",
            status: "scheduled",
          },
        }}
      />,
    );

    assert.match(html, /Окно визита/);
    assert.match(html, /11:00/);
    assert.doesNotMatch(html, /appointment_id/);
    assert.doesNotMatch(html, /Sergey Morozov/);
  });

  it("does not clamp dispatcher AI suggestion content", () => {
    const css = readFileSync(new URL("./styles.css", import.meta.url), "utf-8");
    const match = css.match(/\.ai-suggestion-content\s*{(?<rules>[^}]*)}/);

    assert.ok(match?.groups?.rules);
    assert.doesNotMatch(match.groups.rules, /line-clamp/);
    assert.doesNotMatch(match.groups.rules, /overflow:\\s*hidden/);
  });

  it("renders technician assigned visit workflow controls", () => {
    const html = renderToStaticMarkup(
      <ProtectedTechnicianPage
        initialSession={{
          accessToken: "technician-token",
          username: "technician@coffeefix.local",
          roles: ["technician"],
        }}
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "visit_scheduled",
              customer_name: "Anna Petrova",
              machine_label: "Rocket Appartamento",
              urgency: "today",
              address: "Tverskaya district",
              visit_window: "Сегодня 16:00-18:00",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialDetail={{
          request_number: "CFX-20260605-000001",
          status: "visit_scheduled",
          customer_name: "Anna Petrova",
          customer_phone: "+7 999 111-22-33",
          machine_label: "Rocket Appartamento",
          problem: "E61 group overheats after descaling.",
          address: "Tverskaya district",
          urgency: "today",
          visit_window: "Сегодня 16:00-18:00",
          appointment: {
            starts_at: "2026-06-16T16:00:00+03:00",
            ends_at: "2026-06-16T18:00:00+03:00",
            window_label: "Сегодня 16:00-18:00",
            status: "scheduled",
          },
          diagnosis: null,
          repair_result: null,
        }}
        initialSchedule={{
          items: [
            {
              appointment: {
                appointment_id: 7,
                request_number: "CFX-20260605-000001",
                technician_identifier: "technician@coffeefix.local",
                technician_name: "Pavel Sokolov",
                starts_at: "2026-06-16T16:00:00+03:00",
                ends_at: "2026-06-16T18:00:00+03:00",
                window_label: "Сегодня 16:00-18:00",
                status: "scheduled",
                reschedule_reason: null,
                cancel_reason: null,
                created_at: "2026-06-15 10:00:00",
                updated_at: "2026-06-15 10:00:00",
              },
              request_status: "visit_scheduled",
              customer_name: "Anna Petrova",
              machine_label: "Rocket Appartamento",
              urgency: "today",
              address: "Tverskaya district",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialParts={{
          items: [
            {
              part_id: 1,
              sku: "E61-GASKET-73",
              name: "Прокладка группы E61 73 мм",
              brand: "Rocket",
              model: "Appartamento",
              unit: "pcs",
              compatibility_note: "Подходит для распространенных групп E61.",
              part_type: "gasket",
              parameter_label: "diameter",
              parameter_value: "73",
              parameter_unit: "mm",
              factual_key: "gasket|rocket|diameter|73|mm",
              compatibility: [
                {
                  compatibility_id: 1,
                  part_id: 1,
                  compatibility_level: "exact_model",
                  brand: "Rocket",
                  model: "Appartamento",
                  series: null,
                  machine_family: null,
                  note: "Check thickness.",
                  created_at: "2026-06-07 12:03:00",
                },
              ],
              created_at: "2026-06-07 12:00:00",
              quantity_on_hand: 4,
              reserved_quantity: 1,
              available_quantity: 3,
              low_stock_threshold: 2,
              is_low_stock: false,
              stock_updated_at: "2026-06-07 12:05:00",
            },
          ],
        }}
      />,
    );

    assert.match(html, /Выезды мастера/);
    assert.match(html, /Мое расписание/);
    assert.match(html, /Rocket Appartamento/);
    assert.match(html, /Сегодня 16:00-18:00/);
    assert.match(html, /Запланировано/);
    assert.match(html, /Чеклист диагностики/);
    assert.match(html, /Питание включается/);
    assert.match(html, /Результат ремонта/);
    assert.match(html, /Использованные запчасти/);
    assert.match(html, /Подходит к этой машине/);
    assert.match(html, /Поиск по SKU, названию или бренду/);
    assert.match(html, /E61-GASKET-73 · Прокладка группы E61 73 мм/);
    assert.match(html, /доступно 3 шт\./);
    assert.doesNotMatch(html, /placeholder="ID запчасти"/);
    assert.doesNotMatch(html, /class="service-bar"/);
  });

  it("renders inventory catalog and stock controls", () => {
    const html = renderToStaticMarkup(
      <ProtectedInventoryPage
        initialSession={{
          accessToken: "inventory-token",
          username: "inventory@coffeefix.local",
          roles: ["inventory"],
        }}
        initialParts={{
          items: [
            {
              part_id: 1,
              sku: "E61-GASKET-73",
              name: "Прокладка группы E61 73 мм",
              brand: "Rocket",
              model: "Appartamento",
              unit: "pcs",
              compatibility_note: "Подходит для распространенных групп E61.",
              part_type: "seal",
              parameter_label: "diameter",
              parameter_value: "73",
              parameter_unit: "mm",
              factual_key: "seal|rocket|diameter|73|mm",
              compatibility: [
                {
                  compatibility_id: 1,
                  part_id: 1,
                  compatibility_level: "exact_model",
                  brand: "Rocket",
                  model: "Appartamento",
                  series: null,
                  machine_family: null,
                  note: "Check thickness.",
                  created_at: "2026-06-07 12:03:00",
                },
              ],
              created_at: "2026-06-07 12:00:00",
              quantity_on_hand: 4,
              reserved_quantity: 3,
              available_quantity: 1,
              low_stock_threshold: 2,
              is_low_stock: true,
              stock_updated_at: "2026-06-07 12:05:00",
            },
          ],
        }}
        initialSuppliers={{
          items: [
            {
              supplier_id: 5,
              name: "Supplier One",
              contact_name: "Nora",
              phone: "+101",
              email: null,
              note: null,
              active: true,
              created_at: "2026-06-18 10:00:00",
              updated_at: "2026-06-18 10:00:00",
            },
          ],
        }}
        initialPurchaseRequests={{
          items: [
            {
              purchase_request_id: 12,
              supplier_id: 5,
              supplier_name: "Supplier One",
              status: "draft",
              note: "Low stock",
              actor: "inventory",
              created_at: "2026-06-18 10:05:00",
              updated_at: "2026-06-18 10:05:00",
              items: [
                {
                  item_id: 21,
                  purchase_request_id: 12,
                  part_id: 1,
                  sku: "E61-GASKET-73",
                  part_name: "Прокладка группы E61 73 мм",
                  unit: "pcs",
                  quantity: 4,
                  note: null,
                },
              ],
            },
          ],
        }}
      />,
    );

    assert.match(html, /Склад запчастей/);
    assert.ok(html.indexOf("<h2>Каталог</h2>") < html.indexOf("Складские действия"));
    assert.match(html, /<summary>[\s\S]*Добавить позицию/);
    assert.match(html, /<summary>[\s\S]*Добавить совместимость/);
    assert.match(html, /<summary>[\s\S]*Обновить остаток/);
    assert.match(html, /E61-GASKET-73/);
    assert.match(html, /Прокладка группы E61 73 мм/);
    assert.match(html, /1 шт\./);
    assert.match(html, /Склад 4 · Резерв 3/);
    assert.match(html, /низкий остаток/);
    assert.match(html, /inventory-part-card/);
    assert.match(html, /inventory-part-stock/);
    assert.match(html, /<summary>[\s\S]*Подробности/);
    assert.match(html, /<dt>Характеристика<\/dt><dd>уплотнитель · диаметр: 73 мм<\/dd>/);
    assert.match(html, /<dt>Комментарий<\/dt><dd>Подходит для распространенных групп E61.<\/dd>/);
    assert.match(html, /Тип детали/);
    assert.match(html, /Добавить совместимость/);
    assert.match(html, /inventory-compatibility-list[\s\S]*Модель: Rocket · Appartamento/);
    assert.match(html, /Rocket · Appartamento/);
    assert.match(html, /Добавить позицию/);
    assert.match(html, /Артикул \/ SKU/);
    assert.match(html, /Например: GAGGIA-CLASSIC-GASKET-MODEL-4-MM/);
    assert.match(html, /Единица учета/);
    assert.match(html, /Начальный остаток/);
    assert.match(html, /Обновить остаток/);
    assert.match(html, /Позиция для остатка/);
    assert.match(html, /Позиция для резерва/);
    assert.doesNotMatch(html, /placeholder="ID позиции"/);
    assert.match(html, /Создать резерв/);
    assert.doesNotMatch(html, /id="procurement"/);
    assert.doesNotMatch(html, /Supplier One/);
    assert.doesNotMatch(html, /Создать черновик из низких остатков/);
    assert.doesNotMatch(html, /PR-12/);
    assert.doesNotMatch(html, /Заменить строки/);
    assert.match(html, /Движения склада/);
    assert.doesNotMatch(html, /class="service-bar"/);
  });

  it("renders a compact paginated inventory catalog", () => {
    const parts = Array.from({ length: 12 }, (_, index) => {
      const partNumber = index + 1;
      return {
        part_id: partNumber,
        sku: `PAGE-PART-${String(partNumber).padStart(2, "0")}`,
        name: `Позиция каталога ${partNumber}`,
        brand: "Catalog",
        model: `Model ${partNumber}`,
        unit: "pcs",
        compatibility_note: null,
        part_type: "seal",
        parameter_label: "diameter",
        parameter_value: String(70 + partNumber),
        parameter_unit: "mm",
        factual_key: `seal|catalog|diameter|${70 + partNumber}|mm`,
        compatibility: [],
        created_at: "2026-06-07 12:00:00",
        quantity_on_hand: partNumber,
        reserved_quantity: 0,
        available_quantity: partNumber,
        low_stock_threshold: 2,
        is_low_stock: false,
        stock_updated_at: "2026-06-07 12:05:00",
      };
    });
    const html = renderToStaticMarkup(
      <ProtectedInventoryPage
        initialSession={{
          accessToken: "inventory-token",
          username: "inventory@coffeefix.local",
          roles: ["inventory"],
        }}
        initialParts={{ items: parts }}
      />,
    );

    assert.match(html, /inventory-catalog-card compact-catalog/);
    assert.match(html, /Показано 1-10 из 12/);
    assert.match(html, /На странице/);
    assert.match(html, /aria-label="Показывать 10 позиций"/);
    assert.match(html, /aria-label="Показывать 50 позиций"/);
    assert.match(html, /aria-label="Показывать 100 позиций"/);
    assert.match(html, /PAGE-PART-01/);
    assert.match(html, /PAGE-PART-10/);
    assert.equal(html.match(/class="inventory-part-card"/g)?.length, 10);
    assert.match(html, /Следующая/);
    assert.ok(html.indexOf("PAGE-PART-10") < html.indexOf("inventory-catalog-footer"));
    assert.ok(html.indexOf("inventory-catalog-footer") < html.indexOf("На странице"));
    assert.ok(html.indexOf("inventory-catalog-footer") < html.indexOf("Следующая"));
  });

  it("renders admin procurement approval without inventory-only controls", () => {
    const html = renderToStaticMarkup(
      <ProtectedProcurementPage
        initialSession={{
          accessToken: "admin-token",
          username: "admin@coffeefix.local",
          roles: ["admin"],
        }}
        initialParts={{ items: [] }}
        initialSuppliers={{
          items: [
            {
              supplier_id: 5,
              name: "Supplier One",
              contact_name: "Nora",
              phone: "+101",
              email: null,
              note: null,
              active: true,
              created_at: "2026-06-18 10:00:00",
              updated_at: "2026-06-18 10:00:00",
            },
          ],
        }}
        initialPurchaseRequests={{
          items: [
            {
              purchase_request_id: 13,
              supplier_id: 5,
              supplier_name: "Supplier One",
              status: "pending_approval",
              note: "Approve valves",
              actor: "inventory",
              created_at: "2026-06-18 10:05:00",
              updated_at: "2026-06-18 10:05:00",
              items: [
                {
                  item_id: 22,
                  purchase_request_id: 13,
                  part_id: 9,
                  sku: "VALVE-01",
                  part_name: "Steam valve",
                  unit: "pcs",
                  quantity: 2,
                  note: null,
                },
              ],
            },
          ],
        }}
      />,
    );

    assert.match(html, /PR-13/);
    assert.match(html, /Согласовать/);
    assert.doesNotMatch(html, /Складские действия/);
    assert.doesNotMatch(html, /Создать резерв/);
    assert.doesNotMatch(html, /Обновить строки/);
  });

  it("builds an editable inventory SKU suggestion from part identity fields", () => {
    assert.equal(
      buildInventorySkuSuggestion({
        brand: "Gaggia",
        model: "Classic",
        partType: "gasket",
        parameterLabel: "model",
        parameterValue: "4",
        parameterUnit: "mm",
      }),
      "GAGGIA-CLASSIC-GASKET-MODEL-4-MM",
    );
    assert.equal(
      buildInventorySkuSuggestion({
        brand: "  Nuova Simonelli ",
        model: "",
        partType: "steam valve seal",
        parameterLabel: "",
        parameterValue: "",
        parameterUnit: "",
      }),
      "NUOVA-SIMONELLI-STEAM-VALVE-SEAL",
    );
  });

  it("formats inventory part identity and compatibility without mixing unrelated fields", () => {
    assert.equal(
      buildInventoryPartSpecLabel({
        part_type: "gasket",
        parameter_label: "connector",
        parameter_value: "55",
        parameter_unit: "mm",
      }),
      "прокладка · соединение: 55 мм",
    );
    assert.equal(
      buildInventoryPartSpecLabel({
        part_type: "seal",
        parameter_label: "diameter",
        parameter_value: "73",
        parameter_unit: "mm",
      }),
      "уплотнитель · диаметр: 73 мм",
    );
    assert.equal(
      buildInventoryCompatibilityLabel({
        compatibility_id: 1,
        part_id: 1,
        compatibility_level: "series",
        brand: "Jura",
        model: "Classic",
        series: "E series",
        machine_family: "Boiler probe",
        note: null,
        created_at: "2026-06-15 10:00:00",
      }),
      "Серия: Jura · серия E",
    );
    assert.equal(
      buildInventoryCompatibilityLabel({
        compatibility_id: 2,
        part_id: 1,
        compatibility_level: "exact_model",
        brand: "Gaggia",
        model: "Classic",
        series: "E series",
        machine_family: "Boiler probe",
        note: null,
        created_at: "2026-06-15 10:00:00",
      }),
      "Модель: Gaggia · Classic",
    );
    assert.equal(
      buildInventoryCompatibilityLabel({
        compatibility_id: 3,
        part_id: 1,
        compatibility_level: "generic_group",
        brand: null,
        model: null,
        series: null,
        machine_family: "Boiler probe",
        note: null,
        created_at: "2026-06-15 10:00:00",
      }),
      "Группа: датчик бойлера",
    );
  });

  it("filters dispatcher request list by status and urgency", () => {
    const items = [
      {
        request_number: "CFX-20260605-000001",
        status: "visit_scheduled" as const,
        customer_name: "Anna Petrova",
        customer_phone: "+7 999 111-22-33",
        machine_label: "Jura E8",
        urgency: "today" as const,
        address: "Tverskaya district",
        created_at: "2026-06-05 10:00:00",
        latest_event_title: "Визит запланирован",
      },
      {
        request_number: "CFX-20260605-000002",
        status: "awaiting_assignment" as const,
        customer_name: "Ivan Ivanov",
        customer_phone: "+7 999 111-22-33",
        machine_label: "Saeco E8",
        urgency: "planned" as const,
        address: "Arbat district",
        created_at: "2026-06-05 10:10:00",
        latest_event_title: "Заявка создана",
      },
    ];

    assert.deepEqual(
      filterDispatcherItems(items, "awaiting_assignment", "planned").map((item) => item.request_number),
      ["CFX-20260605-000002"],
    );

    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{ items }}
        initialDetail={dispatcherDetail}
      />,
    );

    assert.match(html, /aria-label="Фильтр по статусу"/);
    assert.match(html, /aria-label="Фильтр по срочности"/);
  });

  it("keeps dispatcher workspace free from public contact chrome and public CTAs", () => {
    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "visit_scheduled",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialDetail={dispatcherDetail}
      />,
    );

    assert.doesNotMatch(html, /class="service-bar"/);
    assert.doesNotMatch(html, /Москва и МО/);
    assert.doesNotMatch(html, /Пн-Вс 08:00-22:00/);
    assert.doesNotMatch(html, /href="tel:\+74950000000"/);
    assert.doesNotMatch(html, /class="desktop-nav"/);
    assert.doesNotMatch(html, /class="header-cta"/);
    assert.doesNotMatch(html, /Оставить заявку/);
    assert.doesNotMatch(html, /Вызвать мастера/);
  });

  it("renders admin owner dashboard workspace card and route helpers", () => {
    const html = renderToStaticMarkup(
      <StaffWorkspacePage
        initialSession={{
          accessToken: "admin-token",
          username: "owner@coffeefix.local",
          roles: ["admin"],
        }}
      />,
    );

    assert.equal(buildOwnerDashboardPath(), "/owner/dashboard");
    assert.equal(buildOwnerDailyReportPath(), "/owner/daily-report");
    assert.match(html, /Панель владельца/);
    assert.match(html, /href="\/owner"/);
  });

  it("renders staff assistant workspace card and route helpers", () => {
    const dispatcherHtml = renderToStaticMarkup(
      <StaffWorkspacePage
        initialSession={{
          accessToken: "dispatcher-token",
          username: "dispatcher@coffeefix.local",
          roles: ["dispatcher"],
        }}
      />,
    );
    const technicianHtml = renderToStaticMarkup(
      <StaffWorkspacePage
        initialSession={{
          accessToken: "technician-token",
          username: "technician@coffeefix.local",
          roles: ["technician"],
        }}
      />,
    );

    assert.equal(buildAssistantRunsPath(), "/assistant/runs");
    assert.equal(buildAssistantConfirmPath(12), "/assistant/runs/12/confirm");
    assert.match(dispatcherHtml, /AI-помощник/);
    assert.match(dispatcherHtml, /href="\/assistant"/);
    assert.doesNotMatch(technicianHtml, /AI-помощник/);
  });

  it("keeps assistant tool-level role denials on the assistant page", () => {
    assert.equal(shouldRedirectAssistantResponse(401), true);
    assert.equal(shouldRedirectAssistantResponse(403), false);
  });

  it("renders assistant runs, tool sources, and pending confirmation state", () => {
    const initialRuns: AssistantRunResponse[] = [
      {
        run_id: 7,
        actor_username: "dispatcher@coffeefix.local",
        safe_message: "Порекомендуй техника для CFX-20260617-000001",
        status: "completed",
        assistant_message: "recommend_technician completed.",
        created_at: "2026-06-17T12:00:00+00:00",
        updated_at: "2026-06-17T12:00:00+00:00",
        tool_calls: [
          {
            tool_call_id: 9,
            tool_name: "recommend_technician",
            policy: "read_only",
            status: "completed",
            arguments: { request_number: "CFX-20260617-000001" },
            result_summary: "pavel@coffeefix.local: score=110, reasons=Brand match: Jura",
            result_refs: [
              {
                label: "Pavel Sokolov",
                target_type: "technician",
                target_id: "pavel@coffeefix.local",
                href: "/dispatcher?request=CFX-20260617-000001",
              },
              {
                label: "Unsafe source",
                target_type: "knowledge_source",
                target_id: "javascript:alert(1)",
                href: "javascript:alert(1)",
              },
            ],
            created_at: "2026-06-17T12:00:00+00:00",
            updated_at: "2026-06-17T12:00:00+00:00",
          },
        ],
      },
      {
        run_id: 8,
        actor_username: "inventory@coffeefix.local",
        safe_message: "Создай черновик закупки supplier 1 part 2 qty 3",
        status: "confirmation_required",
        assistant_message: "create_purchase_request_draft requires staff confirmation before changing ServiceOps data.",
        created_at: "2026-06-17T12:05:00+00:00",
        updated_at: "2026-06-17T12:05:00+00:00",
        tool_calls: [
          {
            tool_call_id: 10,
            tool_name: "create_purchase_request_draft",
            policy: "requires_confirmation",
            status: "confirmation_required",
            arguments: { supplier_id: 1, part_id: 2, quantity: 3 },
            result_summary: "Confirmation required before creating a draft purchase request.",
            result_refs: [],
            created_at: "2026-06-17T12:05:00+00:00",
            updated_at: "2026-06-17T12:05:00+00:00",
          },
        ],
      },
      {
        run_id: 9,
        actor_username: "inventory@coffeefix.local",
        safe_message: "tool=create_purchase_request_draft; numeric_ids=1,2,3",
        status: "executing",
        assistant_message: "create_purchase_request_draft is being confirmed.",
        created_at: "2026-06-17T12:06:00+00:00",
        updated_at: "2026-06-17T12:06:00+00:00",
        tool_calls: [
          {
            tool_call_id: 11,
            tool_name: "create_purchase_request_draft",
            policy: "requires_confirmation",
            status: "executing",
            arguments: { supplier_id: 1, part_id: 2, quantity: 3 },
            result_summary: "Confirmed tool is executing.",
            result_refs: [],
            created_at: "2026-06-17T12:06:00+00:00",
            updated_at: "2026-06-17T12:06:00+00:00",
          },
        ],
      },
      {
        run_id: 10,
        actor_username: "admin@coffeefix.local",
        safe_message: "Вопрос: сколько всего получено заявок на ремонт?; инструмент: generate_daily_report",
        status: "completed",
        assistant_message: "Daily report 2026-06-19: Всего заявок: 33",
        created_at: "2026-06-19T12:06:00+00:00",
        updated_at: "2026-06-19T12:06:00+00:00",
        tool_calls: [
          {
            tool_call_id: 12,
            tool_name: "generate_daily_report",
            policy: "read_only",
            status: "completed",
            arguments: {},
            result_summary: "Daily report 2026-06-19: Всего заявок: 33",
            result_refs: [{ label: "dashboard_url", target_type: "owner_dashboard", target_id: "/owner", href: "/owner" }],
            created_at: "2026-06-19T12:06:00+00:00",
            updated_at: "2026-06-19T12:06:00+00:00",
          },
        ],
      },
      {
        run_id: 11,
        actor_username: "admin@coffeefix.local",
        safe_message: "tool=generate_daily_report",
        status: "completed",
        assistant_message: "Daily report 2026-06-19: Всего заявок: 33; Новые заявки: 19",
        created_at: "2026-06-19T12:07:00+00:00",
        updated_at: "2026-06-19T12:07:00+00:00",
        tool_calls: [
          {
            tool_call_id: 13,
            tool_name: "generate_daily_report",
            policy: "read_only",
            status: "completed",
            arguments: {},
            result_summary: "Daily report 2026-06-19: Всего заявок: 33; Новые заявки: 19",
            result_refs: [],
            created_at: "2026-06-19T12:07:00+00:00",
            updated_at: "2026-06-19T12:07:00+00:00",
          },
        ],
      },
    ];
    const html = renderToStaticMarkup(
      <AssistantPage
        initialSession={{
          accessToken: "inventory-token",
          username: "inventory@coffeefix.local",
          roles: ["inventory"],
        }}
        initialRuns={initialRuns}
      />,
    );

    assert.match(html, /AI-помощник/);
    assert.match(html, /recommend_technician/);
    assert.match(html, /Pavel Sokolov/);
    assert.match(html, /Unsafe source/);
    assert.doesNotMatch(html, /href="javascript:alert\(1\)"/);
    assert.match(html, /Требует подтверждения/);
    assert.match(html, /Подтвердить действие/);
    assert.match(html, /Выполняется/);
    assert.match(html, /выполняется/);
    assert.match(html, /<h2>сколько всего получено заявок на ремонт\?<\/h2>/);
    assert.match(html, /<h2>Всего заявок: 33<\/h2>/);
    assert.match(html, /Всего заявок: 33/);
    assert.doesNotMatch(html, /<h2>tool=generate_daily_report<\/h2>/);
    assert.doesNotMatch(html, /<h2>Дневной отчет<\/h2>/);
    assert.doesNotMatch(html, /<h2>.*инструмент:/);
    assert.doesNotMatch(html, /уже создана/i);
    assert.doesNotMatch(html, /\+7 999/);
  });

  it("protects and routes the staff assistant page", () => {
    const guardedHtml = renderToStaticMarkup(<ProtectedAssistantPage initialSession={null} />);
    const previousWindow = globalThis.window;
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        location: {
          origin: "http://localhost:3000",
          pathname: "/assistant",
          search: "",
        },
        localStorage: {
          getItem: () =>
            JSON.stringify({
              accessToken: "dispatcher-token",
              username: "dispatcher@coffeefix.local",
              roles: ["dispatcher"],
            }),
        },
      },
    });

    try {
      const routedHtml = renderToStaticMarkup(<App />);

      assert.match(guardedHtml, /Требуется вход сотрудника/);
      assert.match(guardedHtml, /href="\/staff\/login\?next=%2Fassistant"/);
      assert.match(routedHtml, /AI-помощник/);
      assert.doesNotMatch(renderToStaticMarkup(<App />), /class="desktop-nav"/);
    } finally {
      Object.defineProperty(globalThis, "window", { configurable: true, value: previousWindow });
    }
  });

  it("renders owner dashboard SLA, workload, issue, and low-stock metrics", () => {
    const initialDashboard: OwnerDashboardResponse = {
      generated_at: "2026-06-17T12:00:00+00:00",
      metrics: {
        total_requests: 4,
        new_requests: 1,
        in_progress_requests: 2,
        waiting_for_parts_requests: 1,
        completed_requests: 1,
        overdue_requests: 1,
        near_deadline_requests: 1,
      },
      sla_risks: [
        {
          request_number: "CFX-20260617-000001",
          status: "new",
          urgency: "today",
          customer_name: "Anna Petrova",
          machine_label: "Jura E8",
          latest_event_title: "Заявка создана",
          sla: {
            request_number: "CFX-20260617-000001",
            state: "overdue",
            deadline_at: "2026-06-17T11:00:00+00:00",
            hours_remaining: -1,
            is_overdue: true,
            is_near_deadline: false,
          },
        },
      ],
      technician_workload: [
        {
          technician_identifier: "technician@coffeefix.local",
          active_requests: 2,
          scheduled_visits: 1,
          waiting_for_parts: 1,
        },
      ],
      top_issue_groups: [{ label: "no coffee flow", count: 2 }],
      low_stock_risk: [
        {
          part_id: 1,
          sku: "FLOW-METER",
          name: "Flow meter",
          unit: "pcs",
          available_quantity: 1,
          low_stock_threshold: 2,
        },
      ],
    };
    const html = renderToStaticMarkup(
      <OwnerDashboardPage
        initialSession={{
          accessToken: "admin-token",
          username: "owner@coffeefix.local",
          roles: ["admin"],
        }}
        initialDashboard={initialDashboard}
      />,
    );

    assert.match(html, /Панель владельца/);
    assert.match(html, /Всего заявок/);
    assert.match(html, /Новые заявки/);
    assert.match(html, /Просрочены/);
    assert.match(html, /CFX-20260617-000001/);
    assert.match(html, /Anna Petrova/);
    assert.match(html, /technician@coffeefix.local/);
    assert.match(html, /no coffee flow/);
    assert.match(html, /FLOW-METER/);
    assert.match(html, /Доступно 1 pcs/);
    assert.doesNotMatch(html, /internal-notes/);
  });

  it("protects owner dashboard for admin sessions", () => {
    const html = renderToStaticMarkup(<ProtectedOwnerDashboardPage initialSession={null} />);

    assert.match(html, /Требуется вход администратора/);
    assert.match(html, /href="\/staff\/login\?next=%2Fowner"/);
  });

  it("keeps dispatcher notification delivery status in a collapsed technical log", () => {
    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "visit_scheduled",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Визит запланирован",
            },
          ],
        }}
        initialDetail={dispatcherDetail}
      />,
    );

    assert.match(html, /Технический лог/);
    assert.match(html, /Уведомления/);
    assert.match(html, /service_request\.created/);
    assert.match(html, /sent/);
    assert.match(html, /telegram/);
    assert.match(html, /попытка 1/);
    assert.doesNotMatch(html, /class="notification-delivery-panel"/);
  });

  it("does not label queued notification delivery as an error", () => {
    const html = renderToStaticMarkup(
      <DispatcherPage
        initialList={{
          items: [
            {
              request_number: "CFX-20260605-000001",
              status: "new",
              customer_name: "Anna Petrova",
              customer_phone: "+7 999 111-22-33",
              machine_label: "Jura E8",
              urgency: "today",
              address: "Tverskaya district",
              created_at: "2026-06-05 10:00:00",
              latest_event_title: "Заявка создана",
            },
          ],
        }}
        initialDetail={{
          ...dispatcherDetail,
          notification_deliveries: [
            {
              event_id: "CFX-20260605-000001:service_request.created:1",
              event_type: "service_request.created",
              status: "queued",
              channel: null,
              provider_message_id: null,
              error: null,
              attempt_count: 1,
              created_at: "2026-06-05 10:01:00",
              updated_at: "2026-06-05 10:01:00",
            },
          ],
        }}
      />,
    );

    assert.doesNotMatch(html, /Ошибка уведомления/);
    assert.match(html, /queued/);
  });

  it("renders the public status page with timeline, clarification answer, and Telegram opt-in", () => {
    const html = renderToStaticMarkup(
      <StatusPage
        initialStatus={{
          request_number: "CFX-20260605-000001",
          public_token: "status_token",
          status: "needs_clarification",
          customer: {
            name: "Anna Petrova",
            phone_masked: "+7 999 ***-**-33",
            telegram: "@anna_fix",
          },
          machine: {
            brand: "Jura",
            model: "E8",
          },
          problem_summary: "Machine leaks water under the brew group.",
          timeline: [
            {
              status: "new",
              title: "Заявка создана",
              description: "Мы получили обращение.",
              actor: "system",
              created_at: "2026-06-05 10:00:00",
            },
            {
              status: "needs_clarification",
              title: "Нужно уточнить симптомы",
              description: "Диспетчер попросил фото ошибки на дисплее.",
              actor: "dispatcher",
              created_at: "2026-06-05 10:05:00",
            },
            {
              status: "visit_scheduled",
              title: "Визит запланирован",
              description: "Диспетчер согласовал окно визита.",
              actor: "dispatcher",
              created_at: "2026-06-05 11:00:00",
            },
            {
              status: "repair_in_progress",
              title: "Ремонт в работе",
              description: "Мастер начал ремонт.",
              actor: "technician",
              created_at: "2026-06-05 12:00:00",
            },
          ],
          clarification: {
            question_id: 7,
            question: "Пришлите, пожалуйста, код ошибки на дисплее.",
            answer: null,
            answered_at: null,
          },
          telegram_opt_in: {
            enabled: false,
            link: "/service-requests/CFX-20260605-000001/telegram-opt-in",
          },
        }}
      />,
    );

    assert.match(html, /Статус заявки CFX-20260605-000001/);
    assert.match(html, /Проверить другую заявку/);
    assert.doesNotMatch(html, /placeholder="CFX-20260605-000001"/);
    assert.match(html, /Ждет уточнения/);
    assert.match(html, /Jura E8/);
    assert.match(html, /class="timeline status-visible-timeline"/);
    assert.match(html, /Визит запланирован/);
    assert.match(html, /Ремонт в работе/);
    assert.match(html, /Остальные события \(2\)/);
    assert.match(html, /class="status-hidden-events"/);
    assert.match(html, /Нужно уточнить симптомы/);
    assert.match(html, /Вопрос диспетчера/);
    assert.match(html, /Пришлите, пожалуйста, код ошибки на дисплее./);
    assert.match(html, /Отправить ответ/);
    assert.match(html, /Подключить Telegram/);
    assert.doesNotMatch(html, /Pavel Sokolov/);
    assert.doesNotMatch(html, /Клиент просит звонить/);
    assert.doesNotMatch(html, /AI-подсказки/);
    assert.doesNotMatch(html, /Уточнить перегрев/);
  });
});

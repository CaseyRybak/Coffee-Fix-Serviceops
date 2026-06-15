import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  App,
  AdminPage,
  DispatcherPage,
  ProtectedAdminPage,
  ProtectedDispatcherPage,
  ProtectedInventoryPage,
  ProtectedTechnicianPage,
  StaffLoginPage,
  StatusPage,
  SuccessState,
  buildDispatcherAssignmentPath,
  buildDispatcherClarificationPath,
  buildDispatcherDetailPath,
  buildDispatcherInternalNotePath,
  buildDispatcherListPath,
  buildDispatcherSchedulePath,
  buildDispatcherAppointmentPath,
  buildDispatcherAppointmentReschedulePath,
  buildDispatcherAppointmentCancelPath,
  buildAcceptAiClarificationPath,
  buildAdminStaffActivatePath,
  buildAdminStaffAuditPath,
  buildAdminStaffDeactivatePath,
  buildAdminStaffPath,
  buildAdminStaffResetPasswordPath,
  buildAdminStaffRolesPath,
  buildGenerateAiSuggestionsPath,
  buildIgnoreAiSuggestionPath,
  buildInventoryPartCompatibilityPath,
  buildInventoryPartsPath,
  buildInventoryStockPath,
  buildInventorySkuSuggestion,
  buildInventoryPartSpecLabel,
  buildInventoryCompatibilityLabel,
  buildTechnicianDetailPath,
  buildTechnicianDiagnosisPath,
  buildTechnicianListPath,
  buildTechnicianPartsUsedPath,
  buildTechnicianResultPath,
  buildTechnicianSchedulePath,
  buildDispatcherStatusPath,
  buildCustomerAnswerPayload,
  buildServiceRequestPayload,
  buildStaffLoginPath,
  buildStatusLookupPath,
  buildTelegramOptInPayload,
  resolveApiBaseUrl,
  resolveStaffLandingPath,
  getStoredStaffSession,
  staffAuthHeaders,
  filterDispatcherItems,
  normalizeRequestNumber,
  statusPathFromRequestNumber,
  telegramOptInPathFromRequestNumber,
  getNextFormStep,
  validateIntakeStep,
} from "./App";

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
    assert.match(nginxConfig, /try_files \$uri \$uri\/ \/index\.html;/);
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
      attachmentFilename: "",
      attachmentContentType: "",
      attachmentSizeBytes: "",
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
      attachmentFilename: "leak.jpg",
      attachmentContentType: "image/jpeg",
      attachmentSizeBytes: "34822",
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
      attachment_metadata: [
        {
          filename: "leak.jpg",
          content_type: "image/jpeg",
          size_bytes: 34822,
        },
      ],
    });
  });

  it("builds public status and notification API paths", () => {
    assert.equal(normalizeRequestNumber(" cfx-20260605-000001 "), "CFX-20260605-000001");
    assert.equal(statusPathFromRequestNumber("CFX-20260605-000001"), "/status/CFX-20260605-000001");
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

  it("uses the API port fallback for local Vite development", () => {
    assert.equal(resolveApiBaseUrl(undefined, "http://localhost:3000"), "http://localhost:8000");
    assert.equal(resolveApiBaseUrl(undefined, "http://127.0.0.1:3000"), "http://127.0.0.1:8000");
    assert.equal(resolveApiBaseUrl("https://api.example.test", "http://localhost:3000"), "https://api.example.test");
    assert.equal(resolveApiBaseUrl(undefined, "https://coffeefix.example"), "");
  });

  it("builds dispatcher API paths", () => {
    assert.equal(buildDispatcherListPath(), "/dispatcher/service-requests");
    assert.equal(buildDispatcherSchedulePath(), "/dispatcher/schedule");
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
  });

  it("builds staff login paths and auth headers", () => {
    assert.equal(buildStaffLoginPath("/dispatcher"), "/staff/login?next=%2Fdispatcher");
    assert.equal(buildStaffLoginPath("/dispatcher/service-requests"), "/staff/login?next=%2Fdispatcher%2Fservice-requests");
    assert.deepEqual(staffAuthHeaders(null), {});
    assert.deepEqual(staffAuthHeaders({ accessToken: "staff-token", username: "dispatcher@coffeefix.local", roles: ["dispatcher"] }), {
      Authorization: "Bearer staff-token",
    });
  });

  it("builds admin staff management API paths", () => {
    assert.equal(buildAdminStaffPath(), "/admin/staff");
    assert.equal(
      buildAdminStaffRolesPath("admin user@coffeefix.local"),
      "/admin/staff/admin%20user%40coffeefix.local/roles",
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
      "/admin",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "admin@coffeefix.local", roles: ["admin"] }, "/admin"),
      "/admin",
    );
    assert.equal(
      resolveStaffLandingPath({ username: "lead@coffeefix.local", roles: ["admin", "dispatcher"] }, "/dispatcher"),
      "/dispatcher",
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
              roles: ["admin"],
              active: true,
              created_at: "2026-06-07 12:00:00",
              updated_at: "2026-06-07 12:00:00",
            },
            {
              username: "tech@coffeefix.local",
              display_name: "Tech",
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
    assert.match(workspaceHtml, /tech@coffeefix.local/);
    assert.match(workspaceHtml, /technician/);
    assert.match(workspaceHtml, /Активировать/);
    assert.match(workspaceHtml, /Сбросить пароль/);
    assert.match(workspaceHtml, /Аудит действий/);
    assert.match(workspaceHtml, /staff.deactivated/);
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
    assert.match(html, /Кандидаты мастеров/);
    assert.match(html, /Sergey Morozov/);
    assert.match(html, /Jura, Saeco · ЦАО/);
    assert.match(html, /Клиент просит звонить после 12:00./);
    assert.match(html, /Обновить статус/);
    assert.match(html, /Клиент увидит эти заголовок и описание в истории статуса/);
    assert.match(html, /Заголовок для клиента/);
    assert.match(html, /Описание для клиента/);
    assert.match(html, /Задать вопрос клиенту/);
    assert.match(html, /Назначить мастера/);
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
    assert.match(html, /Логин мастера/);
    assert.doesNotMatch(html, /Начало ISO/);
    assert.doesNotMatch(html, /Конец ISO/);
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
      />,
    );

    assert.match(html, /Склад запчастей/);
    assert.ok(html.indexOf("<h2>Каталог</h2>") < html.indexOf("Складские действия"));
    assert.match(html, /<summary>[\s\S]*Добавить позицию/);
    assert.match(html, /<summary>[\s\S]*Добавить совместимость/);
    assert.match(html, /<summary>[\s\S]*Обновить остаток/);
    assert.match(html, /E61-GASKET-73/);
    assert.match(html, /Прокладка группы E61 73 мм/);
    assert.match(html, /Доступно: 1 шт\./);
    assert.match(html, /На складе: 4 · Резерв: 3/);
    assert.match(html, /низкий остаток/);
    assert.match(html, /inventory-part-card/);
    assert.match(html, /inventory-part-stock/);
    assert.match(html, /<summary>[\s\S]*Подробности/);
    assert.match(html, /<dt>Характеристика<\/dt><dd>уплотнитель · диаметр: 73 мм<\/dd>/);
    assert.match(html, /<dt>Комментарий<\/dt><dd>Подходит для распространенных групп E61.<\/dd>/);
    assert.match(html, /Тип детали/);
    assert.match(html, /Добавить совместимость/);
    assert.match(html, /inventory-compatibility-list[\s\S]*Совместимость/);
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
    assert.match(html, /Движения склада/);
    assert.doesNotMatch(html, /class="service-bar"/);
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

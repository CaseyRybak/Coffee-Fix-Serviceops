import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  App,
  StatusPage,
  SuccessState,
  buildCustomerAnswerPayload,
  buildServiceRequestPayload,
  buildStatusLookupPath,
  buildTelegramOptInPayload,
  normalizeRequestNumber,
  statusPathFromRequestNumber,
  telegramOptInPathFromRequestNumber,
  getNextFormStep,
  validateIntakeStep,
} from "./App";

describe("App", () => {
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

    assert.match(dockerfile, /COPY nginx\.conf \/etc\/nginx\/conf\.d\/default\.conf/);
    assert.match(nginxConfig, /try_files \$uri \$uri\/ \/index\.html;/);
  });

  it("renders the success state with a request number", () => {
    const html = renderToStaticMarkup(<SuccessState requestNumber="CFX-20260605-000001" />);

    assert.match(html, /Заявка CFX-20260605-000001 создана/);
    assert.match(html, /Диспетчер проверит описание/);
    assert.match(html, /Открыть страницу статуса/);
    assert.match(html, /Подключить Telegram-уведомления/);
    assert.match(html, /href="\/status\/CFX-20260605-000001"/);
    assert.match(html, /href="\/service-requests\/CFX-20260605-000001\/telegram-opt-in"/);
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
  });
});

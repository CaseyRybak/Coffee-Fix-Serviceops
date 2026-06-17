import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Clock, HelpCircle, MessageCircle, Send } from "lucide-react";

import {
  apiBaseUrl,
  buildCustomerAnswerPayload,
  buildStatusLookupPath,
  buildTelegramOptInPayload,
  replaceStatusLookupRoute,
  replaceStatusRoute,
  statusLookupValueFromPath,
  telegramOptInPathFromRequestNumber,
} from "../../shared/api";
import { formatCompactDateTime, statusLabel } from "../../shared/formatters";
import type { PublicStatusSnapshot } from "../../shared/types";
import { Footer, Header, ServiceBar } from "./PublicLandingPage";

export function StatusPage({ initialStatus }: { initialStatus?: PublicStatusSnapshot }) {
  const [lookup, setLookup] = useState(initialStatus?.request_number ?? "");
  const [status, setStatus] = useState<PublicStatusSnapshot | null>(initialStatus ?? null);
  const [changingRequest, setChangingRequest] = useState(!initialStatus);
  const [answer, setAnswer] = useState("");
  const [telegram, setTelegram] = useState(initialStatus?.customer.telegram ?? "");
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function loadStatus(value: string) {
    const cleaned = value.trim();
    if (!cleaned) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${buildStatusLookupPath(cleaned)}`);
      if (!response.ok) throw new Error(`Status request failed with ${response.status}`);
      const body = (await response.json()) as PublicStatusSnapshot;
      setStatus(body);
      setLookup(body.request_number);
      setTelegram(body.customer.telegram ?? "");
      setChangingRequest(false);
      replaceStatusRoute(body.request_number);
    } catch {
      setMessage("Не удалось открыть статус. Проверьте номер заявки и попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialStatus) return;
    if (typeof window === "undefined") return;
    const statusLookup = statusLookupValueFromPath(window.location.pathname);
    if (statusLookup) {
      setLookup(statusLookup);
      void loadStatus(statusLookup);
    }
  }, [initialStatus]);

  async function handleLookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadStatus(lookup);
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!status?.clarification) return;
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}/service-requests/${status.request_number}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildCustomerAnswerPayload(status.clarification.question_id, answer)),
      });
      if (!response.ok) throw new Error(`Answer request failed with ${response.status}`);
      setAnswer("");
      await loadStatus(status.request_number);
      setMessage("Ответ сохранен. Диспетчер увидит его в заявке.");
    } catch {
      setMessage("Не удалось отправить ответ. Попробуйте еще раз.");
    }
  }

  async function requestTelegramOptIn() {
    if (!status) return;
    setMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${telegramOptInPathFromRequestNumber(status.request_number)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildTelegramOptInPayload(telegram)),
      });
      if (!response.ok) throw new Error(`Telegram opt-in failed with ${response.status}`);
      const body = (await response.json()) as { link: string };
      setTelegramLink(body.link);
      window.open(body.link, "_blank", "noopener,noreferrer");
      setMessage("Откройте Telegram и нажмите Start у бота, чтобы завершить подключение.");
    } catch {
      setMessage("Не удалось подготовить Telegram-подключение. Попробуйте позже.");
    }
  }

  return (
    <div className="app-page status-page">
      <ServiceBar />
      <Header />
      <main className="status-main">
        <section className="section-inner status-workspace">
          {status && !changingRequest ? (
            <div className="status-lookup compact-status-header">
              <div>
                <span>Страница статуса</span>
                <h1>Статус заявки {status.request_number}</h1>
                <p>Ниже показаны текущий этап, история заявки и доступные действия.</p>
              </div>
              <button
                className="secondary-status-button"
                type="button"
                onClick={() => {
                  setLookup("");
                  setChangingRequest(true);
                  replaceStatusLookupRoute();
                }}
              >
                Проверить другую заявку
              </button>
            </div>
          ) : (
            <form className="status-lookup" onSubmit={handleLookup}>
              <div>
                <span>Страница статуса</span>
                <h1>{status ? "Проверить другую заявку" : "Проверьте статус заявки"}</h1>
                <p>Введите номер обращения из SMS, звонка диспетчера или письма после отправки заявки.</p>
              </div>
              <div className="status-lookup-controls">
                <input
                  aria-label="Номер заявки"
                  value={lookup}
                  onChange={(event) => setLookup(event.target.value)}
                  placeholder="CFX-20260605-000001"
                />
                <button className="submit-button" type="submit" disabled={loading}>
                  {loading ? "Проверяем" : "Показать статус"}
                </button>
              </div>
            </form>
          )}

          {message ? <p className="status-message">{message}</p> : null}

          {status ? (
            <div className="status-dashboard">
              <section className="status-summary">
                <div>
                  <span className="status-pill">{statusLabel(status.status)}</span>
                  <h2>{status.customer.name}</h2>
                  <p>{status.customer.phone_masked}</p>
                </div>
                <div>
                  <span>Кофемашина</span>
                  <strong>
                    {status.machine.brand}
                    {status.machine.model ? ` ${status.machine.model}` : ""}
                  </strong>
                  <p>{status.problem_summary}</p>
                </div>
                {status.appointment ? (
                  <div>
                    <span>Окно визита</span>
                    <strong>{status.appointment.window_label}</strong>
                    {status.appointment.starts_at && status.appointment.ends_at ? (
                      <p>
                        {formatCompactDateTime(status.appointment.starts_at)} - {formatCompactDateTime(status.appointment.ends_at)}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </section>

              <section className="status-panel">
                <div className="status-panel-heading">
                  <Clock aria-hidden="true" />
                  <h2>История заявки</h2>
                </div>
                <div className="timeline status-visible-timeline">
                  {status.timeline.slice(-2).map((event) => (
                    <article className="timeline-item" key={`${event.title}-${event.created_at}`}>
                      <span />
                      <div>
                        <small>{statusLabel(event.status)}</small>
                        <h3>{event.title}</h3>
                        <p>{event.description}</p>
                        <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                      </div>
                    </article>
                  ))}
                </div>
                {status.timeline.length > 2 ? (
                  <details className="status-hidden-events">
                    <summary>Остальные события ({status.timeline.length - 2})</summary>
                    <div className="timeline status-hidden-timeline">
                      {status.timeline.slice(0, -2).map((event) => (
                        <article className="timeline-item" key={`${event.title}-${event.created_at}-hidden`}>
                          <span />
                          <div>
                            <small>{statusLabel(event.status)}</small>
                            <h3>{event.title}</h3>
                            <p>{event.description}</p>
                            <time dateTime={event.created_at}>{formatCompactDateTime(event.created_at)}</time>
                          </div>
                        </article>
                      ))}
                    </div>
                  </details>
                ) : null}
              </section>

              <section className="status-panel clarification-panel">
                <div className="status-panel-heading">
                  <HelpCircle aria-hidden="true" />
                  <h2>Вопрос диспетчера</h2>
                </div>
                {status.clarification ? (
                  <>
                    <p>{status.clarification.question}</p>
                    {status.clarification.answer ? (
                      <div className="saved-answer">
                        <span>Ваш ответ</span>
                        <strong>{status.clarification.answer}</strong>
                      </div>
                    ) : (
                      <form className="status-answer-form" onSubmit={submitAnswer}>
                        <textarea
                          value={answer}
                          onChange={(event) => setAnswer(event.target.value)}
                          placeholder="Напишите ответ для диспетчера"
                          required
                          rows={3}
                        />
                        <button className="submit-button" type="submit">
                          <Send aria-hidden="true" />
                          Отправить ответ
                        </button>
                      </form>
                    )}
                  </>
                ) : (
                  <p>Сейчас нет открытых уточняющих вопросов.</p>
                )}
              </section>

              <section className="status-panel telegram-panel">
                <div className="status-panel-heading">
                  <MessageCircle aria-hidden="true" />
                  <h2>Telegram-уведомления</h2>
                </div>
                <p>Можно подключить уведомления по этой заявке без личного кабинета.</p>
                <div className="telegram-controls">
                  <input value={telegram ?? ""} onChange={(event) => setTelegram(event.target.value)} placeholder="@username" />
                  <button className="submit-button" type="button" onClick={requestTelegramOptIn}>
                    Подключить Telegram
                  </button>
                </div>
                {telegramLink ? (
                  <a className="status-link" href={telegramLink} target="_blank" rel="noreferrer">
                    Открыть Telegram-бота
                  </a>
                ) : null}
              </section>
            </div>
          ) : null}
        </section>
      </main>
      <Footer />
    </div>
  );
}

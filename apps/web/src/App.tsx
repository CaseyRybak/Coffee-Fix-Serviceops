import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  ArrowRight,
  Brush,
  Building2,
  Car,
  CheckCircle2,
  CheckSquare,
  ChevronRight,
  ClipboardList,
  Clock,
  Coffee,
  Cog,
  CupSoda,
  Droplets,
  ExternalLink,
  Eye,
  HelpCircle,
  Mail,
  MapPin,
  Menu,
  MessageCircle,
  Monitor,
  Package,
  Phone,
  PhoneCall,
  Power,
  Send,
  Shield,
  Thermometer,
  Wrench,
  X,
} from "lucide-react";

type ClientType = "private" | "office" | "coffee_shop" | "restaurant" | "other";
type LocationType = "home" | "office" | "coffee_shop" | "restaurant" | "other";
type Urgency = "today" | "one_two_days" | "planned";
type FormStep = 1 | 2 | 3;

export interface IntakeFormState {
  name: string;
  phone: string;
  telegram: string;
  clientType: ClientType;
  brand: string;
  model: string;
  locationType: LocationType;
  problem: string;
  address: string;
  visitTime: string;
  comment: string;
  urgency: Urgency;
  attachmentFilename: string;
  attachmentContentType: string;
  attachmentSizeBytes: string;
}

interface IntakePayload {
  customer: {
    name: string;
    phone: string;
    telegram?: string;
    client_type: ClientType;
  };
  machine: {
    brand: string;
    model?: string;
    location_type: LocationType;
  };
  problem: string;
  address: string;
  urgency: Urgency;
  attachment_metadata?: Array<{
    filename: string;
    content_type: string;
    size_bytes: number;
  }>;
}

type RequestStatus =
  | "new"
  | "needs_clarification"
  | "awaiting_assignment"
  | "technician_assigned"
  | "visit_scheduled"
  | "diagnostics"
  | "waiting_for_parts"
  | "repair_in_progress"
  | "completed"
  | "closed"
  | "warranty_case"
  | "cancelled";

interface PublicStatusSnapshot {
  request_number: string;
  public_token: string;
  status: RequestStatus;
  customer: {
    name: string;
    phone_masked: string;
    telegram: string | null;
  };
  machine: {
    brand: string;
    model: string | null;
  };
  problem_summary: string;
  timeline: Array<{
    status: RequestStatus;
    title: string;
    description: string;
    actor: string;
    created_at: string;
  }>;
  clarification: {
    question_id: number;
    question: string;
    answer: string | null;
    answered_at: string | null;
  } | null;
  telegram_opt_in: {
    enabled: boolean;
    link: string;
  };
}

const initialForm: IntakeFormState = {
  name: "",
  phone: "",
  telegram: "",
  clientType: "private",
  brand: "",
  model: "",
  locationType: "home",
  problem: "",
  address: "",
  visitTime: "",
  comment: "",
  urgency: "one_two_days",
  attachmentFilename: "",
  attachmentContentType: "",
  attachmentSizeBytes: "",
};

const navLinks = [
  { label: "Услуги", href: "#services" },
  { label: "Бренды", href: "#brands" },
  { label: "Как работаем", href: "#how-it-works" },
  { label: "Гарантия", href: "#trust" },
  { label: "Статус заявки", href: "/status" },
  { label: "Контакты", href: "#footer" },
];

const clientTypes: Array<{ value: ClientType; label: string }> = [
  { value: "private", label: "Частный клиент" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

const locations: Array<{ value: LocationType; label: string }> = [
  { value: "home", label: "Дом" },
  { value: "office", label: "Офис" },
  { value: "coffee_shop", label: "Кофейня" },
  { value: "restaurant", label: "Ресторан" },
  { value: "other", label: "Другое" },
];

const urgencies: Array<{ value: Urgency; label: string }> = [
  { value: "today", label: "Сегодня" },
  { value: "one_two_days", label: "В ближайшие 1-2 дня" },
  { value: "planned", label: "Плановое обслуживание" },
];

const brands = [
  "Jura",
  "Saeco",
  "DeLonghi",
  "Philips",
  "Bosch",
  "Nivona",
  "WMF",
  "Nuova Simonelli",
  "La Cimbali",
  "Rancilio",
  "Melitta",
  "Miele",
];

const machineTypes = [
  "Домашние автоматические",
  "Профессиональные",
  "Офисные",
  "Кофемашины для кофеен",
  "Встраиваемые",
  "Капсульные",
];

const issues = [
  { icon: Cog, title: "Не мелет кофе", desc: "Засор жерновов или проблема с кофемолкой" },
  { icon: Droplets, title: "Течет вода", desc: "Повреждение уплотнителей или трубок подачи воды" },
  { icon: Power, title: "Не включается", desc: "Неисправность платы управления или питания" },
  { icon: Monitor, title: "Ошибка на дисплее", desc: "Диагностика кода ошибки и устранение причины" },
  { icon: Thermometer, title: "Не греет воду", desc: "Вышел из строя нагревательный элемент или термоблок" },
  { icon: Coffee, title: "Не взбивает молоко", desc: "Засор или износ капучинатора / паровой трубки" },
  { icon: CupSoda, title: "Не подает кофе", desc: "Засор заварочного устройства или группы" },
  { icon: Brush, title: "Чистка и декальцинация", desc: "Плановое обслуживание и удаление накипи" },
];

const repairSteps = [
  {
    icon: ClipboardList,
    title: "Оставляете заявку",
    desc: "Заполните короткую форму на сайте или позвоните. Укажите бренд, симптомы и удобное время.",
  },
  {
    icon: PhoneCall,
    title: "Диспетчер уточняет симптомы",
    desc: "Специалист свяжется с вами, уточнит детали неисправности и согласует время визита мастера.",
  },
  {
    icon: Wrench,
    title: "Мастер приезжает и проводит диагностику",
    desc: "Выездной мастер осматривает кофемашину, диагностирует причину и определяет объем работ.",
  },
  {
    icon: CheckSquare,
    title: "Согласуем стоимость и выполняем ремонт",
    desc: "После согласования стоимости выполняем ремонт. Большинство поломок устраняется за один выезд.",
  },
];

const trustCards = [
  {
    icon: Shield,
    title: "Гарантия на выполненные работы",
    desc: "До 6 месяцев на ремонт и установленные запчасти. Письменная гарантия по каждому обращению.",
    tone: "green",
  },
  {
    icon: Car,
    title: "Выезд на дом, в офис и кофейни",
    desc: "Работаем по Москве и Московской области. Выезд в день обращения при наличии свободных мастеров.",
    tone: "brown",
  },
  {
    icon: Package,
    title: "Запчасти и расходники в наличии",
    desc: "Собственный склад оригинальных и совместимых запчастей для популярных брендов.",
    tone: "brown",
  },
  {
    icon: Building2,
    title: "Работаем с физ. и юрлицами",
    desc: "Договор и закрывающие документы для бухгалтерии. Безналичная оплата для организаций.",
    tone: "brown",
  },
  {
    icon: Eye,
    title: "Статус заявки онлайн",
    desc: "Отслеживайте этапы ремонта по ссылке - без личного кабинета и регистрации.",
    tone: "green",
  },
  {
    icon: MessageCircle,
    title: "Уведомления в Telegram",
    desc: "Получайте обновления по статусу заявки прямо в мессенджер - по желанию клиента.",
    tone: "green",
  },
];

const nextSteps = [
  "Проверим описание и симптомы",
  "Зададим уточняющие вопросы, если нужно",
  "Подберем мастера и проверим запчасти",
  "Согласуем время визита",
];

const footerServices = [
  "Ремонт кофемашин",
  "Диагностика",
  "Плановое обслуживание",
  "Декальцинация",
  "Замена запчастей",
  "Настройка помола",
];

const footerBrands = ["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli"];
const footerClientLinks = [
  { label: "Оставить заявку", href: "#request-form" },
  { label: "Отследить статус", href: "/status" },
  { label: "Telegram-уведомления", href: "/status" },
  { label: "Гарантийные условия", href: "#trust" },
  { label: "Оплата и документы", href: "#trust" },
];

export function getNextFormStep(step: FormStep): FormStep {
  return step < 3 ? ((step + 1) as FormStep) : 3;
}

export function validateIntakeStep(form: IntakeFormState, step: FormStep): string[] {
  if (step === 1) {
    return [
      [form.name, "Имя"],
      [form.phone, "Телефон"],
    ]
      .filter(([value]) => !String(value).trim())
      .map(([, label]) => String(label));
  }

  if (step === 2) {
    return [
      [form.brand, "Бренд кофемашины"],
      [form.problem, "Комментарий"],
    ]
      .filter(([value]) => !String(value).trim())
      .map(([, label]) => String(label));
  }

  return form.address.trim() ? [] : ["Район или адрес"];
}

export function buildServiceRequestPayload(form: IntakeFormState): IntakePayload {
  const payload: IntakePayload = {
    customer: {
      name: form.name.trim(),
      phone: form.phone.trim(),
      client_type: form.clientType,
    },
    machine: {
      brand: form.brand.trim(),
      location_type: form.locationType,
    },
    problem: form.problem.trim(),
    address: form.address.trim(),
    urgency: form.urgency,
  };

  const telegram = form.telegram.trim();
  if (telegram) payload.customer.telegram = telegram;

  const model = form.model.trim();
  if (model) payload.machine.model = model;

  const filename = form.attachmentFilename.trim();
  const contentType = form.attachmentContentType.trim();
  const sizeBytes = Number(form.attachmentSizeBytes);
  if (filename && contentType && Number.isFinite(sizeBytes) && sizeBytes > 0) {
    payload.attachment_metadata = [{ filename, content_type: contentType, size_bytes: sizeBytes }];
  }

  return payload;
}

function apiBaseUrl(): string {
  return import.meta.env.VITE_SERVICEOPS_API_BASE_URL ?? "";
}

export function normalizeRequestNumber(value: string): string {
  return value.trim().toUpperCase();
}

export function statusPathFromRequestNumber(requestNumber: string): string {
  return `/status/${encodeURIComponent(normalizeRequestNumber(requestNumber))}`;
}

export function buildStatusLookupPath(value: string): string {
  const cleaned = value.trim();
  const normalized = normalizeRequestNumber(cleaned);
  if (/^CFX-\d{8}-\d{6}$/.test(normalized)) {
    return `/service-requests/${encodeURIComponent(normalized)}/status`;
  }
  return `/status/${encodeURIComponent(cleaned)}`;
}

export function telegramOptInPathFromRequestNumber(requestNumber: string): string {
  return `/service-requests/${encodeURIComponent(normalizeRequestNumber(requestNumber))}/telegram-opt-in`;
}

export function buildCustomerAnswerPayload(questionId: number, answer: string) {
  return {
    question_id: questionId,
    answer: answer.trim(),
  };
}

export function buildTelegramOptInPayload(telegram: string) {
  const cleaned = telegram.trim();
  return cleaned ? { telegram: cleaned } : { telegram: undefined };
}

function statusLabel(status: RequestStatus): string {
  const labels: Record<RequestStatus, string> = {
    new: "Новая заявка",
    needs_clarification: "Ждет уточнения",
    awaiting_assignment: "Ждет назначения мастера",
    technician_assigned: "Мастер назначен",
    visit_scheduled: "Визит запланирован",
    diagnostics: "Диагностика",
    waiting_for_parts: "Ожидаем запчасти",
    repair_in_progress: "Ремонт в работе",
    completed: "Ремонт завершен",
    closed: "Заявка закрыта",
    warranty_case: "Гарантийный случай",
    cancelled: "Заявка отменена",
  };
  return labels[status];
}

function Field({
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

function ChipGroup<T extends string>({
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

function Logo() {
  return (
    <a className="brand" href="#top" aria-label="CoffeeFix Pro">
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

function ServiceBar() {
  return (
    <div className="service-bar" aria-label="Сервисная информация">
      <div className="service-bar-inner">
        <div className="service-bar-left">
          <span>
            <MapPin aria-hidden="true" />
            Москва и МО
          </span>
          <span>
            <Clock aria-hidden="true" />
            Пн-Вс 08:00-22:00
          </span>
          <span className="desktop-service-note">
            <Car aria-hidden="true" />
            Выезд мастера на дом, в офис и кофейни
          </span>
        </div>
        <div className="service-bar-right">
          <a href="tel:+74950000000">
            <Phone aria-hidden="true" />
            +7 (495) 000-00-00
          </a>
          <a className="service-mini-cta" href="#request-form">
            Вызвать мастера
          </a>
        </div>
      </div>
    </div>
  );
}

function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Logo />
        <nav className="desktop-nav" aria-label="Основная навигация">
          {navLinks.map((link) => (
            <a href={link.href} key={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="header-actions">
          <a className="header-cta" href="#request-form">
            Оставить заявку
          </a>
          <button className="menu-button" type="button" aria-label="Меню" onClick={() => setMobileOpen((open) => !open)}>
            {mobileOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          </button>
        </div>
      </div>

      {mobileOpen ? (
        <nav className="mobile-nav" aria-label="Мобильная навигация">
          {navLinks.map((link) => (
            <a href={link.href} key={link.href} onClick={() => setMobileOpen(false)}>
              {link.label}
            </a>
          ))}
          <a className="mobile-nav-cta" href="#request-form" onClick={() => setMobileOpen(false)}>
            Оставить заявку
          </a>
        </nav>
      ) : null}
    </header>
  );
}

function HeroSection() {
  return (
    <section className="hero-section" id="top">
      <div className="section-inner hero-inner">
        <div className="hero-copy">
          <h1>
            Ремонт кофемашин
            <br />с выездом мастера
          </h1>
          <p>
            Диагностика, ремонт и обслуживание домашних, офисных и профессиональных кофемашин. Уточним симптомы,
            проверим наличие запчастей и согласуем удобное время визита.
          </p>
          <div className="hero-badges">
            {[
              "Выезд в день обращения",
              "Гарантия до 6 месяцев",
              "Запчасти в наличии",
              "Статус заявки онлайн",
              "Без предоплаты",
              "Для юрлиц",
            ].map((badge) => (
              <span key={badge}>
                <CheckCircle2 aria-hidden="true" />
                {badge}
              </span>
            ))}
          </div>
          <div className="hero-actions">
            <a className="primary-cta" href="#request-form">
              Оставить заявку на ремонт
              <ArrowRight aria-hidden="true" />
            </a>
            <a className="secondary-cta" href="#request-form">
              Рассчитать стоимость
            </a>
          </div>
          <p className="hero-footnote">После отправки заявки вы получите номер обращения и ссылку для отслеживания статуса.</p>
        </div>
        <div className="hero-media">
          <img
            src="https://images.unsplash.com/photo-1769326541255-c6612ab334a0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=900"
            alt="Профессиональная кофемашина на сервисном столе"
          />
        </div>
      </div>
    </section>
  );
}

export function SuccessState({ requestNumber }: { requestNumber: string }) {
  return (
    <section className="request-card success-card" aria-live="polite">
      <div className="success-title">
        <CheckCircle2 aria-hidden="true" />
        <h2>Заявка {requestNumber} создана</h2>
      </div>
      <p>Мы получили обращение. Диспетчер проверит описание, уточнит симптомы и предложит ближайшее время визита.</p>
      <div className="success-actions">
        <a href={statusPathFromRequestNumber(requestNumber)}>
          <ExternalLink aria-hidden="true" />
          Открыть страницу статуса
        </a>
        <a className="ghost-action" href={telegramOptInPathFromRequestNumber(requestNumber)}>
          <MessageCircle aria-hidden="true" />
          Подключить Telegram-уведомления
        </a>
      </div>
      <div className="next-steps">
        <p>Что дальше?</p>
        {nextSteps.map((step, index) => (
          <div className="next-step" key={step}>
            <span>{index + 1}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export function StatusPage({ initialStatus }: { initialStatus?: PublicStatusSnapshot }) {
  const [lookup, setLookup] = useState(initialStatus?.request_number ?? "");
  const [status, setStatus] = useState<PublicStatusSnapshot | null>(initialStatus ?? null);
  const [changingRequest, setChangingRequest] = useState(!initialStatus);
  const [answer, setAnswer] = useState("");
  const [telegram, setTelegram] = useState(initialStatus?.customer.telegram ?? "");
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
    } catch {
      setMessage("Не удалось открыть статус. Проверьте номер заявки и попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialStatus) return;
    if (typeof window === "undefined") return;
    const [, route, tokenOrNumber] = window.location.pathname.split("/");
    if (route === "status" && tokenOrNumber) {
      const decoded = decodeURIComponent(tokenOrNumber);
      setLookup(decoded);
      void loadStatus(decoded);
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
      setMessage(`Ссылка для подключения Telegram: ${body.link}`);
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
              </section>

              <section className="status-panel">
                <div className="status-panel-heading">
                  <Clock aria-hidden="true" />
                  <h2>История заявки</h2>
                </div>
                <div className="timeline">
                  {status.timeline.map((event) => (
                    <article className="timeline-item" key={`${event.title}-${event.created_at}`}>
                      <span />
                      <div>
                        <small>{statusLabel(event.status)}</small>
                        <h3>{event.title}</h3>
                        <p>{event.description}</p>
                        <em>{event.created_at}</em>
                      </div>
                    </article>
                  ))}
                </div>
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
              </section>
            </div>
          ) : null}
        </section>
      </main>
      <Footer />
    </div>
  );
}

function RequestForm() {
  const [form, setForm] = useState<IntakeFormState>(initialForm);
  const [step, setStep] = useState<FormStep>(1);
  const [requestNumber, setRequestNumber] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (key: keyof IntakeFormState) => (value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    setValidationWarning(null);
  };

  function requireCurrentStepFields(): boolean {
    const missingFields = validateIntakeStep(form, step);
    if (missingFields.length === 0) {
      setValidationWarning(null);
      return true;
    }
    setValidationWarning(`Заполните: ${missingFields.join(", ")}`);
    return false;
  }

  function goToNextStep() {
    setSubmitError(null);
    if (!requireCurrentStepFields()) return;
    setStep(getNextFormStep(step));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    if (step < 3) {
      goToNextStep();
      return;
    }

    if (!requireCurrentStepFields()) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl()}/service-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildServiceRequestPayload(form)),
      });
      if (!response.ok) throw new Error(`Request failed with ${response.status}`);
      const body = (await response.json()) as { request_number: string };
      setRequestNumber(body.request_number);
    } catch {
      setSubmitError("Не удалось отправить заявку. Проверьте данные и попробуйте еще раз.");
    } finally {
      setSubmitting(false);
    }
  }

  if (requestNumber) return <SuccessState requestNumber={requestNumber} />;

  return (
    <section className="request-section" id="request-form">
      <form className="request-card" onSubmit={handleSubmit}>
        <div className="request-heading">
          <h2>Заявка на ремонт кофемашины</h2>
          <p>Заполните форму - диспетчер уточнит детали и предложит ближайшее время выезда.</p>
          <div className="stepper" aria-label="Шаги формы">
            {([1, 2, 3] as FormStep[]).map((item) => (
              <button
                className={step === item ? "step active" : step > item ? "step complete" : "step"}
                key={item}
                type="button"
                onClick={() => {
                  if (item < step) {
                    setValidationWarning(null);
                    setStep(item);
                  }
                }}
              >
                <span>{step > item ? "✓" : item}</span>
                <strong>{item === 1 ? "Контакты" : item === 2 ? "Кофемашина и проблема" : "Адрес и время"}</strong>
              </button>
            ))}
          </div>
        </div>

        {step === 1 ? (
          <div className="form-stack">
            <Field label="Имя">
              <input value={form.name} onChange={(event) => set("name")(event.target.value)} placeholder="Как вас зовут?" required />
            </Field>
            <Field label="Телефон">
              <input
                value={form.phone}
                onChange={(event) => set("phone")(event.target.value)}
                placeholder="+7 (___) ___-__-__"
                required
                type="tel"
              />
            </Field>
            <Field label="Telegram" optional>
              <input value={form.telegram} onChange={(event) => set("telegram")(event.target.value)} placeholder="@username" />
            </Field>
            <div className="control-group">
              <span className="field-label">Тип клиента</span>
              <ChipGroup value={form.clientType} options={clientTypes} onChange={(value) => set("clientType")(value)} />
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="form-stack">
            <Field label="Бренд кофемашины">
              <select value={form.brand} onChange={(event) => set("brand")(event.target.value)} required>
                <option value="" disabled>
                  Выберите бренд
                </option>
                {["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli", "Другое"].map((brand) => (
                  <option key={brand} value={brand}>
                    {brand}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Модель" optional>
              <input value={form.model} onChange={(event) => set("model")(event.target.value)} placeholder="Например: Jura E6, Saeco Xelsis" />
            </Field>
            <div className="control-group">
              <span className="field-label">Где находится кофемашина</span>
              <ChipGroup value={form.locationType} options={locations} onChange={(value) => set("locationType")(value)} />
            </div>
            <Field label="Что случилось?">
              <textarea
                value={form.problem}
                onChange={(event) => set("problem")(event.target.value)}
                placeholder="Например: не мелет кофе, течет вода, ошибка на дисплее, не включается"
                required
                rows={3}
              />
            </Field>
            <div className="control-group">
              <span className="field-label">Срочность</span>
              <ChipGroup value={form.urgency} options={urgencies} onChange={(value) => set("urgency")(value)} />
            </div>
          </div>
        ) : null}

        {step === 3 ? (
          <div className="form-stack">
            <Field label="Район или адрес">
              <input value={form.address} onChange={(event) => set("address")(event.target.value)} placeholder="Например: м. Тверская, ул. Пушкина, 10" required />
            </Field>
            <Field label="Удобное время визита" optional>
              <input value={form.visitTime} onChange={(event) => set("visitTime")(event.target.value)} placeholder="Например: завтра после 14:00" />
            </Field>
            <Field label="Фото или видео" optional>
              <div className="attachment-grid">
                <input value={form.attachmentFilename} onChange={(event) => set("attachmentFilename")(event.target.value)} placeholder="leak.jpg" />
                <input value={form.attachmentContentType} onChange={(event) => set("attachmentContentType")(event.target.value)} placeholder="image/jpeg" />
                <input inputMode="numeric" value={form.attachmentSizeBytes} onChange={(event) => set("attachmentSizeBytes")(event.target.value)} placeholder="34822" />
              </div>
            </Field>
            <Field label="Комментарий" optional>
              <textarea value={form.comment} onChange={(event) => set("comment")(event.target.value)} placeholder="Любые дополнительные сведения" rows={2} />
            </Field>
          </div>
        ) : null}

        <div className="form-navigation">
          {step > 1 ? (
            <button
              className="back-button"
              type="button"
              onClick={() => {
                setValidationWarning(null);
                setStep((current) => (current - 1) as FormStep);
              }}
            >
              ← Назад
            </button>
          ) : (
            <span />
          )}
          {step < 3 ? (
            <button className="next-button" type="button" onClick={goToNextStep}>
              Далее
              <ChevronRight aria-hidden="true" />
            </button>
          ) : (
            <button className="submit-button" disabled={submitting} type="submit">
              <Send aria-hidden="true" />
              {submitting ? "Отправляем" : "Отправить заявку"}
            </button>
          )}
        </div>
        {step === 3 ? <p className="consent-copy">Нажимая кнопку, вы соглашаетесь с обработкой персональных данных.</p> : null}
        {validationWarning ? (
          <p className="validation-warning" role="alert">
            {validationWarning}
          </p>
        ) : null}
        {submitError ? <p className="submit-error">{submitError}</p> : null}
      </form>
    </section>
  );
}

function BrandsSection() {
  return (
    <section className="section white-section" id="brands">
      <div className="section-inner">
        <SectionHeading
          title="Какие кофемашины ремонтируем"
          copy="Работаем с домашними, офисными и профессиональными кофемашинами всех ведущих брендов."
        />
        <div className="brand-grid">
          {brands.map((brand) => (
            <div key={brand}>{brand}</div>
          ))}
        </div>
        <div className="machine-types">
          <p>Типы кофемашин</p>
          <div>
            {machineTypes.map((type) => (
              <span key={type}>{type}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function IssuesSection() {
  return (
    <section className="section warm-section" id="services">
      <div className="section-inner">
        <SectionHeading
          title="Частые неисправности"
          copy="Опытные мастера диагностируют и устраняют любые неполадки - от механических до электронных."
        />
        <div className="issue-grid">
          {issues.map((issue) => {
            const Icon = issue.icon;
            return (
              <article className="info-card" key={issue.title}>
                <span className="info-icon">
                  <Icon aria-hidden="true" />
                </span>
                <h3>{issue.title}</h3>
                <p>{issue.desc}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section white-section" id="how-it-works">
      <div className="section-inner">
        <SectionHeading title="Как проходит ремонт" copy="Простой и прозрачный процесс - от заявки до готовой кофемашины." />
        <div className="steps-grid">
          {repairSteps.map((item, index) => {
            const Icon = item.icon;
            return (
              <article className="repair-step" key={item.title}>
                <div>
                  <span className="step-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <small>Шаг {index + 1}</small>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            );
          })}
        </div>
        <p className="note-box">
          <strong>Примечание:</strong> Если для ремонта нужна деталь, мы проверим наличие на складе и согласуем срок поставки.
        </p>
      </div>
    </section>
  );
}

function TrustSection() {
  return (
    <section className="section warm-section" id="trust">
      <div className="section-inner">
        <SectionHeading title="Почему выбирают нас" copy="Работаем честно, быстро и с гарантией результата." />
        <div className="trust-grid">
          {trustCards.map((card) => {
            const Icon = card.icon;
            return (
              <article className="info-card trust-card" key={card.title}>
                <span className={card.tone === "green" ? "info-icon green" : "info-icon"}>
                  <Icon aria-hidden="true" />
                </span>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer" id="footer">
      <div className="footer-cta">
        <div className="section-inner footer-cta-inner">
          <div>
            <p>Кофемашина не работает?</p>
            <span>Оставьте заявку - мастер приедет в день обращения</span>
          </div>
          <a href="#request-form">
            Оставить заявку на ремонт
            <ArrowRight aria-hidden="true" />
          </a>
        </div>
      </div>
      <div className="section-inner footer-main">
        <FooterColumn title="Услуги" items={footerServices.map((label) => ({ label, href: "#services" }))} />
        <FooterColumn title="Бренды" items={footerBrands.map((label) => ({ label, href: "#brands" }))} />
        <FooterColumn title="Клиентам" items={footerClientLinks} />
        <div>
          <h3>Контакты</h3>
          <ul className="footer-contacts">
            <li>
              <Phone aria-hidden="true" />
              <a href="tel:+74950000000">+7 (495) 000-00-00</a>
            </li>
            <li>
              <MessageCircle aria-hidden="true" />
              <a href="https://t.me/coffeefixpro">@coffeefixpro</a>
            </li>
            <li>
              <Mail aria-hidden="true" />
              <a href="mailto:info@coffeefixpro.ru">info@coffeefixpro.ru</a>
            </li>
            <li>
              <Clock aria-hidden="true" />
              <span>Пн-Вс 08:00-22:00</span>
            </li>
            <li>
              <MapPin aria-hidden="true" />
              <span>Москва и МО</span>
            </li>
          </ul>
        </div>
      </div>
      <div className="section-inner footer-bottom">
        <Logo />
        <p>© 2026 CoffeeFix Pro. Ремонт и обслуживание кофемашин.</p>
        <div>
          <a href="#top">Политика конфиденциальности</a>
          <a href="#top">Публичная оферта</a>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ title, items }: { title: string; items: Array<{ label: string; href: string }> }) {
  return (
    <div>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item.label}>
            <a href={item.href}>{item.label}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SectionHeading({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="section-heading">
      <h2>{title}</h2>
      <p>{copy}</p>
    </div>
  );
}

export function App() {
  const isStatusRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/status");
  if (isStatusRoute) return <StatusPage />;

  return (
    <div className="app-page">
      <ServiceBar />
      <Header />
      <main>
        <HeroSection />
        <RequestForm />
        <BrandsSection />
        <IssuesSection />
        <HowItWorks />
        <TrustSection />
      </main>
      <Footer />
      <div className="mobile-sticky-cta">
        <a href="tel:+74950000000" aria-label="Позвонить">
          <Phone aria-hidden="true" />
        </a>
        <a href="#request-form">Оставить заявку</a>
      </div>
    </div>
  );
}

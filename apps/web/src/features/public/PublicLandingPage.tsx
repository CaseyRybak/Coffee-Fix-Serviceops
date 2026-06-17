import { useState } from "react";
import type { FormEvent } from "react";
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

import { apiBaseUrl, buildServiceRequestPayload, buildTelegramOptInPayload, statusPathFromRequestNumber, telegramOptInPathFromRequestNumber } from "../../shared/api";
import { clientTypes, locations, urgencies } from "../../shared/options";
import type { FormStep, IntakeFormState } from "../../shared/types";
import { ChipGroup, Field, Logo } from "../../shared/ui";

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
};

const navLinks = [
  { label: "Услуги", href: "#services" },
  { label: "Бренды", href: "#brands" },
  { label: "Как работаем", href: "#how-it-works" },
  { label: "Гарантия", href: "#trust" },
  { label: "Статус заявки", href: "/status" },
  { label: "Контакты", href: "#footer" },
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
  { label: "Оставить заявку", href: "/#request-form" },
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

export function ServiceBar() {
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
          <a className="service-mini-cta" href="/#request-form">
            Вызвать мастера
          </a>
        </div>
      </div>
    </div>
  );
}

export function Header() {
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
          <a className="header-cta" href="/#request-form">
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
          <a className="mobile-nav-cta" href="/#request-form" onClick={() => setMobileOpen(false)}>
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
            <a className="primary-cta" href="/#request-form">
              Оставить заявку на ремонт
              <ArrowRight aria-hidden="true" />
            </a>
            <a className="secondary-cta" href="/status">
              Проверить статус заявки
            </a>
          </div>
          <p className="hero-footnote">После отправки заявки вы получите номер обращения и ссылку для отслеживания статуса.</p>
        </div>
        <div className="hero-media">
          <picture>
            <source
              type="image/webp"
              media="(max-width: 720px)"
              srcSet="/assets/hero-coffee-service-wide-mobile.webp"
            />
            <source type="image/webp" srcSet="/assets/hero-coffee-service-wide-desktop.webp" />
            <img
              src="/assets/hero-coffee-service-wide.png"
              alt="Профессиональная кофемашина на сервисном столе"
            />
          </picture>
        </div>
      </div>
    </section>
  );
}

export function SuccessState({ requestNumber, onCreateNew }: { requestNumber: string; onCreateNew?: () => void }) {
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [telegramMessage, setTelegramMessage] = useState<string | null>(null);

  async function connectTelegram() {
    setTelegramLoading(true);
    setTelegramMessage(null);
    try {
      const response = await fetch(`${apiBaseUrl()}${telegramOptInPathFromRequestNumber(requestNumber)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildTelegramOptInPayload("")),
      });
      if (!response.ok) throw new Error(`Telegram opt-in failed with ${response.status}`);
      const body = (await response.json()) as { link: string };
      setTelegramLink(body.link);
      window.open(body.link, "_blank", "noopener,noreferrer");
      setTelegramMessage("Откройте Telegram и нажмите Start у бота, чтобы завершить подключение.");
    } catch {
      setTelegramMessage("Не удалось подготовить Telegram-подключение. Откройте страницу статуса и попробуйте еще раз.");
    } finally {
      setTelegramLoading(false);
    }
  }

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
        <button className="ghost-action" type="button" onClick={connectTelegram} disabled={telegramLoading}>
          <MessageCircle aria-hidden="true" />
          {telegramLoading ? "Готовим Telegram" : "Подключить Telegram-уведомления"}
        </button>
        <button className="ghost-action" type="button" onClick={onCreateNew}>
          <ClipboardList aria-hidden="true" />
          Создать новую заявку
        </button>
      </div>
      {telegramMessage ? <p className="success-note">{telegramMessage}</p> : null}
      {telegramLink ? (
        <a className="status-link" href={telegramLink} target="_blank" rel="noreferrer">
          Открыть Telegram-бота
        </a>
      ) : null}
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

  function startNewRequest() {
    setForm(initialForm);
    setStep(1);
    setRequestNumber(null);
    setSubmitError(null);
    setValidationWarning(null);
  }

  if (requestNumber) {
    return (
      <section className="request-section request-section-success" id="request-form">
        <SuccessState requestNumber={requestNumber} onCreateNew={startNewRequest} />
      </section>
    );
  }

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

export function Footer() {
  return (
    <footer className="footer" id="footer">
      <div className="footer-cta">
        <div className="section-inner footer-cta-inner">
          <div>
            <p>Кофемашина не работает?</p>
            <span>Оставьте заявку - мастер приедет в день обращения</span>
          </div>
          <a href="/#request-form">
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

export function PublicLandingPage() {
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
        <a href="/#request-form">Оставить заявку</a>
      </div>
    </div>
  );
}

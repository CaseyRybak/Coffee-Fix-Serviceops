import { useState } from "react";
import { CheckCircle2, Send, ExternalLink, MessageCircle, ChevronRight } from "lucide-react";

type FormStep = 1 | 2 | 3;

interface FormData {
  name: string;
  phone: string;
  telegram: string;
  clientType: string;
  brand: string;
  model: string;
  location: string;
  problem: string;
  urgency: string;
  address: string;
  visitTime: string;
  comment: string;
}

const initialForm: FormData = {
  name: "", phone: "", telegram: "", clientType: "",
  brand: "", model: "", location: "", problem: "", urgency: "",
  address: "", visitTime: "", comment: "",
};

const clientTypes = ["Частный клиент", "Офис", "Кофейня", "Ресторан", "Другое"];
const brands = ["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli", "Другое"];
const locations = ["Дом", "Офис", "Кофейня", "Ресторан"];
const urgencies = ["Сегодня", "В ближайшие 1–2 дня", "Плановое обслуживание"];

const nextSteps = [
  "Проверим описание и симптомы",
  "Зададим уточняющие вопросы, если нужно",
  "Подберём мастера и проверим запчасти",
  "Согласуем время визита",
];

function FieldLabel({ children, optional }: { children: React.ReactNode; optional?: boolean }) {
  return (
    <label style={{ color: "#1F1A17", fontSize: "13px", fontWeight: 600, display: "block", marginBottom: 4 }}>
      {children}
      {optional && <span style={{ color: "#717182", fontWeight: 400, marginLeft: 4 }}>— необязательно</span>}
    </label>
  );
}

function Input({
  value, onChange, placeholder, type = "text",
}: { value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%", border: "1px solid #E2D8CD", borderRadius: 8,
        padding: "10px 12px", fontSize: "14px", color: "#1F1A17",
        backgroundColor: "#FFFFFF", outline: "none",
      }}
      onFocus={(e) => { e.target.style.borderColor = "#5A3825"; }}
      onBlur={(e) => { e.target.style.borderColor = "#E2D8CD"; }}
    />
  );
}

function Select({ value, onChange, options, placeholder }: {
  value: string; onChange: (v: string) => void; options: string[]; placeholder?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width: "100%", border: "1px solid #E2D8CD", borderRadius: 8,
        padding: "10px 12px", fontSize: "14px", color: value ? "#1F1A17" : "#717182",
        backgroundColor: "#FFFFFF", outline: "none", cursor: "pointer",
      }}
    >
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt} value={opt} style={{ color: "#1F1A17" }}>{opt}</option>
      ))}
    </select>
  );
}

function ChipGroup({ options, value, onChange }: {
  options: string[]; value: string; onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          style={{
            border: `1px solid ${value === opt ? "#5A3825" : "#E2D8CD"}`,
            backgroundColor: value === opt ? "#5A3825" : "#FFFFFF",
            color: value === opt ? "#FFFFFF" : "#1F1A17",
            borderRadius: 20, padding: "6px 14px", fontSize: "13px", cursor: "pointer",
            transition: "all 0.15s",
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export function RequestForm() {
  const [step, setStep] = useState<FormStep>(1);
  const [form, setForm] = useState<FormData>(initialForm);
  const [submitted, setSubmitted] = useState(false);
  const ticketNumber = "CFX-000123";

  const set = (key: keyof FormData) => (value: string) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <section id="request-form" style={{ backgroundColor: "#F7F2EA" }} className="w-full py-16 px-4">
        <div className="max-w-2xl mx-auto">
          <div style={{ backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD", borderRadius: 16, padding: "40px 32px", boxShadow: "0 4px 24px rgba(0,0,0,0.06)" }}>
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 size={32} style={{ color: "#2F6B4F", flexShrink: 0 }} />
              <div>
                <h2 style={{ color: "#1F1A17", fontSize: "22px", fontWeight: 700 }}>Заявка {ticketNumber} создана</h2>
              </div>
            </div>
            <p style={{ color: "#5A3825", fontSize: "15px", lineHeight: 1.6 }} className="mb-6">
              Мы получили обращение. Диспетчер проверит описание, уточнит симптомы и предложит ближайшее время визита.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 mb-8">
              <button
                style={{ backgroundColor: "#5A3825", color: "#FFFFFF", borderRadius: 8, padding: "12px 20px", fontSize: "14px", fontWeight: 600, border: "none", cursor: "pointer" }}
                className="flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
              >
                <ExternalLink size={15} />
                Открыть страницу статуса
              </button>
              <button
                style={{ backgroundColor: "#FFFFFF", color: "#1F1A17", borderRadius: 8, padding: "12px 20px", fontSize: "14px", border: "1px solid #E2D8CD", cursor: "pointer" }}
                className="flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
              >
                <MessageCircle size={15} style={{ color: "#2F6B4F" }} />
                Подключить Telegram-уведомления
              </button>
            </div>

            <div style={{ borderTop: "1px solid #E2D8CD", paddingTop: 24 }}>
              <p style={{ color: "#717182", fontSize: "12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>Что дальше?</p>
              <div className="flex flex-col gap-2">
                {nextSteps.map((s, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span
                      style={{ backgroundColor: "#5A3825", color: "#FFFFFF", borderRadius: "50%", width: 22, height: 22, fontSize: "11px", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}
                    >{i + 1}</span>
                    <span style={{ color: "#1F1A17", fontSize: "14px" }}>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="request-form" style={{ backgroundColor: "#F7F2EA" }} className="w-full py-16 px-4">
      <div className="max-w-2xl mx-auto">
        <div style={{ backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.06)", overflow: "hidden" }}>
          {/* Header */}
          <div style={{ padding: "28px 32px 0" }}>
            <h2 style={{ color: "#1F1A17", fontSize: "22px", fontWeight: 700, marginBottom: 4 }}>
              Заявка на ремонт кофемашины
            </h2>
            <p style={{ color: "#717182", fontSize: "14px", lineHeight: 1.5, marginBottom: 24 }}>
              Заполните форму — диспетчер уточнит детали и предложит ближайшее время выезда.
            </p>

            {/* Step indicator */}
            <div className="flex items-center gap-2 mb-6">
              {([1, 2, 3] as FormStep[]).map((s) => (
                <div key={s} className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => s < step && setStep(s)}
                    style={{
                      width: 28, height: 28, borderRadius: "50%", border: "none",
                      backgroundColor: step === s ? "#5A3825" : step > s ? "#2F6B4F" : "#E2D8CD",
                      color: step >= s ? "#FFFFFF" : "#717182",
                      fontSize: "12px", fontWeight: 700, cursor: s < step ? "pointer" : "default",
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}
                  >{step > s ? "✓" : s}</button>
                  <span style={{ fontSize: "12px", color: step === s ? "#5A3825" : "#717182", fontWeight: step === s ? 600 : 400 }}>
                    {s === 1 ? "Контакты" : s === 2 ? "Кофемашина и проблема" : "Адрес и время"}
                  </span>
                  {s < 3 && <ChevronRight size={14} style={{ color: "#E2D8CD", marginRight: 4 }} />}
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ padding: "0 32px 28px" }}>
              {/* Step 1 */}
              {step === 1 && (
                <div className="flex flex-col gap-4">
                  <div>
                    <FieldLabel>Имя</FieldLabel>
                    <Input value={form.name} onChange={set("name")} placeholder="Как вас зовут?" />
                  </div>
                  <div>
                    <FieldLabel>Телефон</FieldLabel>
                    <Input value={form.phone} onChange={set("phone")} placeholder="+7 (___) ___-__-__" type="tel" />
                  </div>
                  <div>
                    <FieldLabel optional>Telegram</FieldLabel>
                    <Input value={form.telegram} onChange={set("telegram")} placeholder="@username" />
                  </div>
                  <div>
                    <FieldLabel>Тип клиента</FieldLabel>
                    <ChipGroup options={clientTypes} value={form.clientType} onChange={set("clientType")} />
                  </div>
                </div>
              )}

              {/* Step 2 */}
              {step === 2 && (
                <div className="flex flex-col gap-4">
                  <div>
                    <FieldLabel>Бренд кофемашины</FieldLabel>
                    <Select value={form.brand} onChange={set("brand")} options={brands} placeholder="Выберите бренд" />
                  </div>
                  <div>
                    <FieldLabel optional>Модель</FieldLabel>
                    <Input value={form.model} onChange={set("model")} placeholder="Например: Jura E6, Saeco Xelsis" />
                  </div>
                  <div>
                    <FieldLabel>Где находится кофемашина</FieldLabel>
                    <ChipGroup options={locations} value={form.location} onChange={set("location")} />
                  </div>
                  <div>
                    <FieldLabel>Что случилось?</FieldLabel>
                    <textarea
                      value={form.problem}
                      onChange={(e) => set("problem")(e.target.value)}
                      placeholder="Например: не мелет кофе, течёт вода, ошибка на дисплее, не включается"
                      rows={3}
                      style={{
                        width: "100%", border: "1px solid #E2D8CD", borderRadius: 8,
                        padding: "10px 12px", fontSize: "14px", color: "#1F1A17",
                        backgroundColor: "#FFFFFF", outline: "none", resize: "vertical", fontFamily: "inherit",
                      }}
                      onFocus={(e) => { e.target.style.borderColor = "#5A3825"; }}
                      onBlur={(e) => { e.target.style.borderColor = "#E2D8CD"; }}
                    />
                  </div>
                  <div>
                    <FieldLabel>Срочность</FieldLabel>
                    <ChipGroup options={urgencies} value={form.urgency} onChange={set("urgency")} />
                  </div>
                </div>
              )}

              {/* Step 3 */}
              {step === 3 && (
                <div className="flex flex-col gap-4">
                  <div>
                    <FieldLabel>Район или адрес</FieldLabel>
                    <Input value={form.address} onChange={set("address")} placeholder="Например: м. Тверская, ул. Пушкина, 10" />
                  </div>
                  <div>
                    <FieldLabel>Удобное время визита</FieldLabel>
                    <Input value={form.visitTime} onChange={set("visitTime")} placeholder="Например: завтра после 14:00" />
                  </div>
                  <div>
                    <FieldLabel optional>Комментарий</FieldLabel>
                    <textarea
                      value={form.comment}
                      onChange={(e) => set("comment")(e.target.value)}
                      placeholder="Любые дополнительные сведения"
                      rows={2}
                      style={{
                        width: "100%", border: "1px solid #E2D8CD", borderRadius: 8,
                        padding: "10px 12px", fontSize: "14px", color: "#1F1A17",
                        backgroundColor: "#FFFFFF", outline: "none", resize: "vertical", fontFamily: "inherit",
                      }}
                      onFocus={(e) => { e.target.style.borderColor = "#5A3825"; }}
                      onBlur={(e) => { e.target.style.borderColor = "#E2D8CD"; }}
                    />
                  </div>
                </div>
              )}

              {/* Navigation */}
              <div className="flex items-center justify-between mt-6">
                {step > 1 ? (
                  <button
                    type="button"
                    onClick={() => setStep((s) => (s - 1) as FormStep)}
                    style={{ color: "#5A3825", fontSize: "14px", background: "none", border: "none", cursor: "pointer" }}
                  >
                    ← Назад
                  </button>
                ) : <div />}

                {step < 3 ? (
                  <button
                    type="button"
                    onClick={() => setStep((s) => (s + 1) as FormStep)}
                    style={{ backgroundColor: "#5A3825", color: "#FFFFFF", borderRadius: 8, padding: "11px 24px", fontSize: "14px", fontWeight: 600, border: "none", cursor: "pointer" }}
                    className="flex items-center gap-2 hover:opacity-90 transition-opacity"
                  >
                    Далее <ChevronRight size={15} />
                  </button>
                ) : (
                  <button
                    type="submit"
                    style={{ backgroundColor: "#2F6B4F", color: "#FFFFFF", borderRadius: 8, padding: "11px 24px", fontSize: "14px", fontWeight: 600, border: "none", cursor: "pointer" }}
                    className="flex items-center gap-2 hover:opacity-90 transition-opacity"
                  >
                    <Send size={15} />
                    Отправить заявку
                  </button>
                )}
              </div>
              {step === 3 && (
                <p style={{ color: "#717182", fontSize: "11px", marginTop: 10, textAlign: "center" }}>
                  Нажимая кнопку, вы соглашаетесь с обработкой персональных данных.
                </p>
              )}
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}

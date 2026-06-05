import { CheckCircle2, HelpCircle, Send } from "lucide-react";
import { useState } from "react";

export function StatusPreview() {
  const [answer, setAnswer] = useState("");

  return (
    <section id="status" style={{ backgroundColor: "#FFFFFF" }} className="w-full py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col lg:flex-row gap-12 items-start">
          {/* Text */}
          <div className="flex-1 max-w-md">
            <h2 style={{ color: "#1F1A17", fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, marginBottom: 12 }}>
              Статус заявки онлайн
            </h2>
            <p style={{ color: "#717182", fontSize: "15px", lineHeight: 1.7, marginBottom: 20 }}>
              После отправки заявки вы получите номер обращения и ссылку на страницу статуса. Там можно увидеть этап ремонта, ответить на уточняющие вопросы и подключить Telegram-уведомления.
            </p>
            <ul className="flex flex-col gap-3">
              {[
                "Текущий статус и имя назначенного мастера",
                "Ответы на уточняющие вопросы прямо в браузере",
                "Telegram-уведомления по желанию — без лишних регистраций",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5" style={{ fontSize: "14px", color: "#1F1A17" }}>
                  <CheckCircle2 size={15} style={{ color: "#2F6B4F", marginTop: 2, flexShrink: 0 }} />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Status card preview */}
          <div className="flex-1 w-full max-w-md">
            {/* Label */}
            <p style={{ color: "#9A8F87", fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 10 }}>
              Пример страницы статуса
            </p>
            <div
              style={{
                backgroundColor: "#F7F2EA", border: "1px solid #E2D8CD",
                borderRadius: 16, padding: "24px",
                boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
              }}
            >
              {/* Ticket header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p style={{ color: "#9A8F87", fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Заявка
                  </p>
                  <p style={{ color: "#1F1A17", fontSize: "22px", fontWeight: 800 }}>CFX-000123</p>
                </div>
                <span
                  style={{
                    backgroundColor: "rgba(201,130,43,0.12)", color: "#C9822B",
                    borderRadius: 20, padding: "4px 12px", fontSize: "12px", fontWeight: 600,
                  }}
                >
                  Ждёт уточнения
                </span>
              </div>

              {/* Dispatcher question */}
              <div
                style={{
                  backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD",
                  borderRadius: 10, padding: "14px", marginBottom: 12,
                }}
              >
                <div className="flex items-start gap-2 mb-2">
                  <HelpCircle size={14} style={{ color: "#C9822B", flexShrink: 0, marginTop: 1 }} />
                  <p style={{ color: "#717182", fontSize: "12px", fontWeight: 600 }}>
                    Вопрос диспетчера
                  </p>
                </div>
                <p style={{ color: "#1F1A17", fontSize: "14px", paddingLeft: 20 }}>
                  Есть ли ошибка на дисплее?
                </p>
              </div>

              {/* Answer input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Например: E8"
                  style={{
                    flex: 1, border: "1px solid #E2D8CD", borderRadius: 8,
                    padding: "9px 12px", fontSize: "13px", color: "#1F1A17",
                    backgroundColor: "#FFFFFF", outline: "none",
                  }}
                  onFocus={(e) => { e.target.style.borderColor = "#5A3825"; }}
                  onBlur={(e) => { e.target.style.borderColor = "#E2D8CD"; }}
                />
                <button
                  style={{
                    backgroundColor: "#5A3825", color: "#FFFFFF",
                    border: "none", borderRadius: 8, padding: "9px 14px",
                    cursor: "pointer", display: "flex", alignItems: "center", gap: 5,
                    fontSize: "13px", fontWeight: 600,
                  }}
                  className="hover:opacity-90 transition-opacity whitespace-nowrap"
                >
                  <Send size={13} />
                  Отправить ответ
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

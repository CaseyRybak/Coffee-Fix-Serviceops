import { Phone, MessageCircle, Clock, MapPin, Mail, Coffee, ArrowRight } from "lucide-react";

const services = [
  "Ремонт кофемашин",
  "Диагностика",
  "Плановое обслуживание",
  "Декальцинация",
  "Замена запчастей",
  "Настройка помола",
];

const footerBrands = ["Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona", "WMF", "Nuova Simonelli"];

const clientLinks = [
  "Оставить заявку",
  "Отследить статус",
  "Telegram-уведомления",
  "Гарантийные условия",
  "Оплата и документы",
];

export function Footer() {
  return (
    <footer id="footer" style={{ backgroundColor: "#1F1A17", color: "#E2D8CD" }} className="w-full">
      {/* CTA bar */}
      <div style={{ backgroundColor: "#5A3825", padding: "28px 16px" }}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p style={{ color: "#FFFFFF", fontSize: "18px", fontWeight: 700 }}>Кофемашина не работает?</p>
            <p style={{ color: "#E2D8CD", fontSize: "14px" }}>Оставьте заявку — мастер приедет в день обращения</p>
          </div>
          <a
            href="#request-form"
            style={{ backgroundColor: "#FFFFFF", color: "#5A3825", borderRadius: 8, padding: "12px 24px", fontSize: "15px", fontWeight: 700, whiteSpace: "nowrap" }}
            className="flex items-center gap-2 hover:opacity-90 transition-opacity"
          >
            Оставить заявку на ремонт
            <ArrowRight size={16} />
          </a>
        </div>
      </div>

      {/* Main footer */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
          {/* Services */}
          <div>
            <p style={{ color: "#E2D8CD", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
              Услуги
            </p>
            <ul className="flex flex-col gap-2">
              {services.map((s) => (
                <li key={s}>
                  <a href="#services" style={{ color: "#9A8F87", fontSize: "14px" }} className="hover:text-white transition-colors">{s}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Brands */}
          <div>
            <p style={{ color: "#E2D8CD", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
              Бренды
            </p>
            <ul className="flex flex-col gap-2">
              {footerBrands.map((b) => (
                <li key={b}>
                  <a href="#brands" style={{ color: "#9A8F87", fontSize: "14px" }} className="hover:text-white transition-colors">{b}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Clients */}
          <div>
            <p style={{ color: "#E2D8CD", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
              Клиентам
            </p>
            <ul className="flex flex-col gap-2">
              {clientLinks.map((l) => (
                <li key={l}>
                  <a href="#request-form" style={{ color: "#9A8F87", fontSize: "14px" }} className="hover:text-white transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contacts */}
          <div>
            <p style={{ color: "#E2D8CD", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
              Контакты
            </p>
            <ul className="flex flex-col gap-3">
              <li className="flex items-center gap-2">
                <Phone size={14} style={{ color: "#C9822B", flexShrink: 0 }} />
                <a href="tel:+74950000000" style={{ color: "#E2D8CD", fontSize: "14px" }} className="hover:text-white transition-colors">
                  +7 (495) 000-00-00
                </a>
              </li>
              <li className="flex items-center gap-2">
                <MessageCircle size={14} style={{ color: "#2F6B4F", flexShrink: 0 }} />
                <a href="https://t.me/coffeefixpro" style={{ color: "#E2D8CD", fontSize: "14px" }} className="hover:text-white transition-colors">
                  @coffeefixpro
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Mail size={14} style={{ color: "#9A8F87", flexShrink: 0 }} />
                <a href="mailto:info@coffeefixpro.ru" style={{ color: "#E2D8CD", fontSize: "14px" }} className="hover:text-white transition-colors">
                  info@coffeefixpro.ru
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Clock size={14} style={{ color: "#9A8F87", flexShrink: 0 }} />
                <span style={{ color: "#9A8F87", fontSize: "14px" }}>Пн–Вс 08:00–22:00</span>
              </li>
              <li className="flex items-center gap-2">
                <MapPin size={14} style={{ color: "#9A8F87", flexShrink: 0 }} />
                <span style={{ color: "#9A8F87", fontSize: "14px" }}>Москва и МО</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 20 }} className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div style={{ backgroundColor: "#5A3825" }} className="w-6 h-6 rounded flex items-center justify-center">
              <Coffee size={13} color="#F7F2EA" />
            </div>
            <span style={{ color: "#E2D8CD", fontSize: "14px", fontWeight: 600 }}>CoffeeFix Pro</span>
          </div>
          <p style={{ color: "#717182", fontSize: "12px" }}>
            © 2024 CoffeeFix Pro. Ремонт и обслуживание кофемашин.
          </p>
          <div className="flex gap-4">
            <a href="#" style={{ color: "#717182", fontSize: "12px" }} className="hover:text-white transition-colors">Политика конфиденциальности</a>
            <a href="#" style={{ color: "#717182", fontSize: "12px" }} className="hover:text-white transition-colors">Публичная оферта</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

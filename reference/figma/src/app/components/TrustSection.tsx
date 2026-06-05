import { Shield, Car, Package, Building2, Eye, MessageCircle } from "lucide-react";

const cards = [
  {
    icon: <Shield size={22} />,
    title: "Гарантия на выполненные работы",
    desc: "До 6 месяцев на ремонт и установленные запчасти. Письменная гарантия по каждому обращению.",
    color: "#2F6B4F",
  },
  {
    icon: <Car size={22} />,
    title: "Выезд на дом, в офис и кофейни",
    desc: "Работаем по Москве и Московской области. Выезд в день обращения при наличии свободных мастеров.",
    color: "#5A3825",
  },
  {
    icon: <Package size={22} />,
    title: "Запчасти и расходники в наличии",
    desc: "Собственный склад оригинальных и совместимых запчастей для популярных брендов.",
    color: "#5A3825",
  },
  {
    icon: <Building2 size={22} />,
    title: "Работаем с физ. и юрлицами",
    desc: "Договор и закрывающие документы для бухгалтерии. Безналичная оплата для организаций.",
    color: "#5A3825",
  },
  {
    icon: <Eye size={22} />,
    title: "Статус заявки онлайн",
    desc: "Отслеживайте этапы ремонта по ссылке — без личного кабинета и регистрации.",
    color: "#2F6B4F",
  },
  {
    icon: <MessageCircle size={22} />,
    title: "Уведомления в Telegram",
    desc: "Получайте обновления по статусу заявки прямо в мессенджер — по желанию клиента.",
    color: "#2F6B4F",
  },
];

export function TrustSection() {
  return (
    <section id="trust" style={{ backgroundColor: "#F7F2EA" }} className="w-full py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <h2 style={{ color: "#1F1A17", fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, marginBottom: 8 }}>
          Почему выбирают нас
        </h2>
        <p style={{ color: "#5A3825", fontSize: "15px", marginBottom: 36 }}>
          Работаем честно, быстро и с гарантией результата.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map((card) => (
            <div
              key={card.title}
              style={{
                backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD",
                borderRadius: 12, padding: "22px",
              }}
            >
              <div
                style={{
                  width: 42, height: 42, borderRadius: 10,
                  backgroundColor: card.color === "#2F6B4F" ? "rgba(47,107,79,0.1)" : "rgba(90,56,37,0.1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: card.color, marginBottom: 14,
                }}
              >
                {card.icon}
              </div>
              <h3 style={{ color: "#1F1A17", fontSize: "15px", fontWeight: 700, marginBottom: 6 }}>
                {card.title}
              </h3>
              <p style={{ color: "#717182", fontSize: "13px", lineHeight: 1.55 }}>
                {card.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

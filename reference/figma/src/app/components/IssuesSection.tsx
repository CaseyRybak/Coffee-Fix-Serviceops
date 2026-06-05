import { Cog, Droplets, Power, Monitor, Thermometer, Coffee, CupSoda, Brush } from "lucide-react";

const issues = [
  { icon: <Cog size={20} />, title: "Не мелет кофе", desc: "Засор жерновов или проблема с кофемолкой" },
  { icon: <Droplets size={20} />, title: "Течёт вода", desc: "Повреждение уплотнителей или трубок подачи воды" },
  { icon: <Power size={20} />, title: "Не включается", desc: "Неисправность платы управления или питания" },
  { icon: <Monitor size={20} />, title: "Ошибка на дисплее", desc: "Диагностика кода ошибки и устранение причины" },
  { icon: <Thermometer size={20} />, title: "Не греет воду", desc: "Вышел из строя нагревательный элемент или термоблок" },
  { icon: <Coffee size={20} />, title: "Не взбивает молоко", desc: "Засор или износ капучинатора / паровой трубки" },
  { icon: <CupSoda size={20} />, title: "Не подаёт кофе", desc: "Засор заварочного устройства или группы" },
  { icon: <Brush size={20} />, title: "Чистка и декальцинация", desc: "Плановое обслуживание и удаление накипи" },
];

export function IssuesSection() {
  return (
    <section id="services" style={{ backgroundColor: "#F7F2EA" }} className="w-full py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <h2 style={{ color: "#1F1A17", fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, marginBottom: 8 }}>
          Частые неисправности
        </h2>
        <p style={{ color: "#5A3825", fontSize: "15px", marginBottom: 32 }}>
          Опытные мастера диагностируют и устраняют любые неполадки — от механических до электронных.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {issues.map((issue) => (
            <div
              key={issue.title}
              style={{
                backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD",
                borderRadius: 12, padding: "20px",
              }}
              className="hover:shadow-sm transition-shadow"
            >
              <div
                style={{
                  width: 40, height: 40, borderRadius: 10,
                  backgroundColor: "#F7F2EA", border: "1px solid #E2D8CD",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#5A3825", marginBottom: 12,
                }}
              >
                {issue.icon}
              </div>
              <h3 style={{ color: "#1F1A17", fontSize: "15px", fontWeight: 700, marginBottom: 4 }}>
                {issue.title}
              </h3>
              <p style={{ color: "#717182", fontSize: "13px", lineHeight: 1.5 }}>
                {issue.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

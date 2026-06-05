import { ClipboardList, PhoneCall, Wrench, CheckSquare } from "lucide-react";

const steps = [
  {
    icon: <ClipboardList size={22} />,
    title: "Оставляете заявку",
    desc: "Заполните короткую форму на сайте или позвоните. Укажите бренд, симптомы и удобное время.",
  },
  {
    icon: <PhoneCall size={22} />,
    title: "Диспетчер уточняет симптомы",
    desc: "Специалист свяжется с вами, уточнит детали неисправности и согласует время визита мастера.",
  },
  {
    icon: <Wrench size={22} />,
    title: "Мастер приезжает и проводит диагностику",
    desc: "Выездной мастер осматривает кофемашину, диагностирует причину и определяет объём работ.",
  },
  {
    icon: <CheckSquare size={22} />,
    title: "Согласуем стоимость и выполняем ремонт",
    desc: "После согласования стоимости выполняем ремонт. Большинство поломок устраняется за один выезд.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" style={{ backgroundColor: "#FFFFFF" }} className="w-full py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <h2 style={{ color: "#1F1A17", fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, marginBottom: 8 }}>
          Как проходит ремонт
        </h2>
        <p style={{ color: "#5A3825", fontSize: "15px", marginBottom: 40 }}>
          Простой и прозрачный процесс — от заявки до готовой кофемашины.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className="hidden lg:block absolute top-5 left-1/2 w-full h-px"
                  style={{ backgroundColor: "#E2D8CD", zIndex: 0 }}
                />
              )}
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    style={{
                      width: 44, height: 44, borderRadius: "50%",
                      backgroundColor: "#5A3825", color: "#FFFFFF",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {step.icon}
                  </div>
                  <span
                    style={{
                      fontSize: "11px", fontWeight: 700, color: "#C9822B",
                      textTransform: "uppercase", letterSpacing: "0.06em",
                    }}
                  >
                    Шаг {index + 1}
                  </span>
                </div>
                <h3 style={{ color: "#1F1A17", fontSize: "16px", fontWeight: 700, marginBottom: 8 }}>
                  {step.title}
                </h3>
                <p style={{ color: "#717182", fontSize: "13px", lineHeight: 1.6 }}>
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: 40, padding: "16px 20px",
            backgroundColor: "#F7F2EA", border: "1px solid #E2D8CD",
            borderLeft: "3px solid #C9822B", borderRadius: 8,
          }}
        >
          <p style={{ color: "#5A3825", fontSize: "14px" }}>
            <strong>Примечание:</strong> Если для ремонта нужна деталь, мы проверим наличие на складе и согласуем срок поставки.
          </p>
        </div>
      </div>
    </section>
  );
}

import { CheckCircle2, ArrowRight, ChevronRight } from "lucide-react";

const trustBadges = [
  "Выезд в день обращения",
  "Гарантия до 6 месяцев",
  "Запчасти в наличии",
  "Статус заявки онлайн",
];

export function HeroSection() {
  return (
    <section style={{ backgroundColor: "#F7F2EA" }} className="w-full pt-12 pb-16 px-4">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
        {/* Left */}
        <div className="flex-1 max-w-xl">
          <h1
            style={{ color: "#1F1A17", fontSize: "clamp(28px, 4vw, 48px)", fontWeight: 800, lineHeight: 1.15 }}
            className="mb-5"
          >
            Ремонт кофемашин<br />с выездом мастера
          </h1>
          <p style={{ color: "#5A3825", fontSize: "16px", lineHeight: 1.7 }} className="mb-7">
            Диагностика, ремонт и обслуживание домашних, офисных и профессиональных кофемашин. Уточним симптомы, проверим наличие запчастей и согласуем удобное время визита.
          </p>

          {/* Trust badges */}
          <div className="flex flex-wrap gap-2 mb-8">
            {trustBadges.map((badge) => (
              <span
                key={badge}
                style={{ backgroundColor: "#FFFFFF", border: "1px solid #E2D8CD", color: "#1F1A17", fontSize: "13px" }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
              >
                <CheckCircle2 size={13} style={{ color: "#2F6B4F", flexShrink: 0 }} />
                {badge}
              </span>
            ))}
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <a
              href="#request-form"
              style={{ backgroundColor: "#5A3825", color: "#ffffff", fontSize: "15px", fontWeight: 600 }}
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg hover:opacity-90 transition-opacity"
            >
              Оставить заявку на ремонт
              <ArrowRight size={16} />
            </a>
            <a
              href="#request-form"
              style={{ backgroundColor: "transparent", color: "#5A3825", border: "1px solid #5A3825", fontSize: "15px" }}
              className="inline-flex items-center justify-center gap-1.5 px-6 py-3.5 rounded-lg hover:bg-white transition-colors"
            >
              Узнать ориентировочную стоимость
              <ChevronRight size={15} />
            </a>
          </div>
          <p style={{ color: "#9A8F87", fontSize: "12px" }}>
            После отправки заявки вы получите номер обращения и ссылку для отслеживания статуса.
          </p>
        </div>

        {/* Right — coffee machine photo */}
        <div className="flex-1 w-full max-w-lg">
          <div className="relative rounded-2xl overflow-hidden" style={{ aspectRatio: "4/3" }}>
            <img
              src="https://images.unsplash.com/photo-1769326541255-c6612ab334a0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=900"
              alt="Профессиональная кофемашина на сервисном столе"
              className="w-full h-full object-cover"
            />
            <div
              className="absolute inset-0"
              style={{ background: "linear-gradient(to bottom left, transparent 50%, rgba(31,26,23,0.15) 100%)" }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

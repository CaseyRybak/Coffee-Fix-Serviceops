const brands = [
  "Jura", "Saeco", "DeLonghi", "Philips", "Bosch", "Nivona",
  "WMF", "Nuova Simonelli", "La Cimbali", "Rancilio", "Melitta", "Miele",
];

const types = [
  "Домашние автоматические",
  "Профессиональные",
  "Офисные",
  "Кофемашины для кофеен",
  "Встраиваемые",
  "Капсульные",
];

export function BrandsSection() {
  return (
    <section id="brands" style={{ backgroundColor: "#FFFFFF" }} className="w-full py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <h2 style={{ color: "#1F1A17", fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, marginBottom: 8 }}>
          Какие кофемашины ремонтируем
        </h2>
        <p style={{ color: "#5A3825", fontSize: "15px", marginBottom: 32 }}>
          Работаем с домашними, офисными и профессиональными кофемашинами всех ведущих брендов.
        </p>

        {/* Brands grid */}
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3 mb-10">
          {brands.map((brand) => (
            <div
              key={brand}
              style={{
                backgroundColor: "#F7F2EA", border: "1px solid #E2D8CD",
                borderRadius: 10, padding: "14px 10px",
                textAlign: "center", fontSize: "14px", fontWeight: 600,
                color: "#1F1A17", cursor: "default",
              }}
              className="hover:border-[#5A3825] transition-colors"
            >
              {brand}
            </div>
          ))}
        </div>

        {/* Types */}
        <div style={{ borderTop: "1px solid #E2D8CD", paddingTop: 24 }}>
          <p style={{ color: "#717182", fontSize: "12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
            Типы кофемашин
          </p>
          <div className="flex flex-wrap gap-2">
            {types.map((type) => (
              <span
                key={type}
                style={{
                  border: "1px solid #E2D8CD", borderRadius: 20,
                  padding: "7px 16px", fontSize: "13px", color: "#1F1A17",
                  backgroundColor: "#F7F2EA",
                }}
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

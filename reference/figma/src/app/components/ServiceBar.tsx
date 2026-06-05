import { MapPin, Clock, Car, Phone } from "lucide-react";

export function ServiceBar() {
  return (
    <div style={{ backgroundColor: "#1F1A17", color: "#E2D8CD" }} className="w-full py-2 px-4">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-sm">
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1.5">
            <MapPin size={13} style={{ color: "#C9822B" }} />
            Москва и МО
          </span>
          <span className="flex items-center gap-1.5">
            <Clock size={13} style={{ color: "#C9822B" }} />
            Пн–Вс 08:00–22:00
          </span>
          <span className="hidden md:flex items-center gap-1.5">
            <Car size={13} style={{ color: "#C9822B" }} />
            Выезд мастера на дом, в офис и кофейни
          </span>
        </div>
        <div className="flex items-center gap-3">
          <a href="tel:+74950000000" className="flex items-center gap-1.5 hover:text-white transition-colors">
            <Phone size={13} style={{ color: "#C9822B" }} />
            +7 (495) 000-00-00
          </a>
          <a
            href="#request-form"
            style={{ backgroundColor: "#2F6B4F", color: "#ffffff" }}
            className="px-3 py-1 rounded text-xs hover:opacity-90 transition-opacity whitespace-nowrap"
          >
            Вызвать мастера
          </a>
        </div>
      </div>
    </div>
  );
}

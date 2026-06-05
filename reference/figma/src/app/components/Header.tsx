import { useState } from "react";
import { Menu, X, Coffee } from "lucide-react";

const navLinks = [
  { label: "Услуги", href: "#services" },
  { label: "Бренды", href: "#brands" },
  { label: "Как работаем", href: "#how-it-works" },
  { label: "Гарантия", href: "#trust" },
  { label: "Статус заявки", href: "#status" },
  { label: "Контакты", href: "#footer" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header style={{ backgroundColor: "#F7F2EA", borderBottom: "1px solid #E2D8CD" }} className="sticky top-0 z-40 w-full">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2.5">
          <div style={{ backgroundColor: "#5A3825" }} className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0">
            <Coffee size={18} color="#F7F2EA" />
          </div>
          <div>
            <div style={{ color: "#1F1A17", fontSize: "17px", fontWeight: 700, lineHeight: 1.1 }}>CoffeeFix Pro</div>
            <div style={{ color: "#5A3825", fontSize: "11px", fontWeight: 400, lineHeight: 1 }}>ремонт и обслуживание кофемашин</div>
          </div>
        </a>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-6">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              style={{ color: "#1F1A17", fontSize: "14px" }}
              className="hover:opacity-60 transition-opacity whitespace-nowrap"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* CTA + mobile toggle */}
        <div className="flex items-center gap-3">
          <a
            href="#request-form"
            style={{ backgroundColor: "#5A3825", color: "#ffffff", fontSize: "14px" }}
            className="hidden sm:inline-flex px-4 py-2 rounded hover:opacity-90 transition-opacity whitespace-nowrap"
          >
            Оставить заявку
          </a>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-2 rounded"
            style={{ color: "#1F1A17" }}
            aria-label="Меню"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div style={{ backgroundColor: "#F7F2EA", borderTop: "1px solid #E2D8CD" }} className="lg:hidden px-4 pb-4">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              style={{ color: "#1F1A17", fontSize: "15px", borderColor: "#E2D8CD" }}
              className="block py-2.5 border-b hover:opacity-60"
            >
              {link.label}
            </a>
          ))}
          <a
            href="#request-form"
            onClick={() => setMobileOpen(false)}
            style={{ backgroundColor: "#5A3825", color: "#ffffff" }}
            className="mt-3 block text-center px-4 py-2.5 rounded"
          >
            Оставить заявку
          </a>
        </div>
      )}
    </header>
  );
}

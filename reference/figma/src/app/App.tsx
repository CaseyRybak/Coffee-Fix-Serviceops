import { ServiceBar } from "./components/ServiceBar";
import { Header } from "./components/Header";
import { HeroSection } from "./components/HeroSection";
import { RequestForm } from "./components/RequestForm";
import { BrandsSection } from "./components/BrandsSection";
import { IssuesSection } from "./components/IssuesSection";
import { HowItWorks } from "./components/HowItWorks";
import { TrustSection } from "./components/TrustSection";
import { StatusPreview } from "./components/StatusPreview";
import { Footer } from "./components/Footer";
import { Phone } from "lucide-react";

export default function App() {
  return (
    <div
      style={{ fontFamily: "'Manrope', sans-serif", backgroundColor: "#F7F2EA", minHeight: "100vh" }}
      className="relative"
    >
      <ServiceBar />
      <Header />

      <main>
        <HeroSection />
        <RequestForm />
        <BrandsSection />
        <IssuesSection />
        <HowItWorks />
        <TrustSection />
        <StatusPreview />
      </main>

      <Footer />

      {/* Mobile sticky CTA */}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 sm:hidden"
        style={{
          backgroundColor: "#FFFFFF",
          borderTop: "1px solid #E2D8CD",
          padding: "12px 16px",
          boxShadow: "0 -4px 16px rgba(0,0,0,0.08)",
        }}
      >
        <div className="flex gap-3">
          <a
            href="tel:+74950000000"
            style={{
              border: "1px solid #E2D8CD", borderRadius: 8,
              padding: "12px", color: "#5A3825",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >
            <Phone size={20} />
          </a>
          <a
            href="#request-form"
            style={{
              flex: 1, backgroundColor: "#5A3825", color: "#FFFFFF",
              borderRadius: 8, padding: "12px", fontSize: "15px",
              fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center",
              textDecoration: "none",
            }}
          >
            Оставить заявку
          </a>
        </div>
      </div>
    </div>
  );
}

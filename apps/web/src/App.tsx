import { ClipboardList, RadioTower, Route, Wrench } from "lucide-react";

const lanes = [
  {
    label: "Intake queue",
    value: "12",
    detail: "new requests waiting for triage",
  },
  {
    label: "Technician dispatch",
    value: "7",
    detail: "visits scheduled for today",
  },
  {
    label: "Parts watch",
    value: "4",
    detail: "jobs waiting on stock confirmation",
  },
];

const timeline = [
  "Request received",
  "Dispatcher review",
  "Visit window confirmed",
  "Technician assigned",
];

export function App() {
  return (
    <main className="app-shell">
      <section className="hero-panel" aria-labelledby="app-title">
        <div className="hero-copy">
          <p className="eyebrow">repair operations runtime</p>
          <h1 id="app-title">Coffee Fix ServiceOps</h1>
          <p className="lede">
            A focused workspace for repair intake, scheduling, field coordination, and customer status updates.
          </p>
        </div>
        <div className="signal-card" aria-label="Local environment status">
          <div className="signal-dot" />
          <span>local runtime online</span>
        </div>
      </section>

      <section className="ops-grid" aria-label="Operations summary">
        {lanes.map((lane) => (
          <article className="metric-card" key={lane.label}>
            <span>{lane.label}</span>
            <strong>{lane.value}</strong>
            <p>{lane.detail}</p>
          </article>
        ))}
      </section>

      <section className="workbench" aria-label="Service workflow">
        <div className="workflow-panel">
          <div className="panel-heading">
            <ClipboardList aria-hidden="true" />
            <h2>Request lifecycle</h2>
          </div>
          <ol className="timeline">
            {timeline.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </div>

        <div className="tool-panel">
          <div className="tool-row">
            <Route aria-hidden="true" />
            <div>
              <h2>Dispatch board</h2>
              <p>Route planning and technician assignment will land after the runtime foundation.</p>
            </div>
          </div>
          <div className="tool-row">
            <Wrench aria-hidden="true" />
            <div>
              <h2>Repair context</h2>
              <p>Machine, customer, and parts context will connect through the domain modules.</p>
            </div>
          </div>
          <div className="tool-row">
            <RadioTower aria-hidden="true" />
            <div>
              <h2>Notifications</h2>
              <p>Telegram and status updates are prepared as runtime services in this phase.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

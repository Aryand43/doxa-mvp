import { ChatPanel } from "./features/chat/ChatPanel";
import { ReportPanel } from "./features/reports/ReportPanel";
import { AlertsPanel } from "./features/alerts/AlertsPanel";
import { SummaryBar } from "./components/SummaryBar";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <h1>Doxa Connex AI</h1>
          <p className="app-subtitle">
            Procurement intelligence copilot — assistant, reports & data crawler,
            grounded in your operational data
          </p>
        </div>
        <SummaryBar />
      </header>
      <main className="app-panels">
        <ChatPanel />
        <ReportPanel />
        <AlertsPanel />
      </main>
    </div>
  );
}

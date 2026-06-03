import { ChatPanel } from "./features/chat/ChatPanel";
import { ReportPanel } from "./features/reports/ReportPanel";
import { AlertsPanel } from "./features/alerts/AlertsPanel";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>DOXA</h1>
        <p className="app-subtitle">MVP workspace</p>
      </header>
      <main className="app-panels">
        <ChatPanel />
        <ReportPanel />
        <AlertsPanel />
      </main>
    </div>
  );
}

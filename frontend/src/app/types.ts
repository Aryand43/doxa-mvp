// Shared response types — mirror backend/services/schema.py.

export type Metric = { label: string; value: string; hint?: string | null };

export type TableData = {
  columns: string[];
  rows: Array<Array<string | number | null>>;
};

export type AlertItem = {
  id: string;
  severity: string; // high | medium | low
  type: string;
  source: string;
  title: string;
  description: string;
  recommended_action: string;
  records: string[];
  vendor_name?: string | null;
  amount?: number | null;
  currency?: string | null;
};

export type ActionItem = { label: string; kind: string; hint?: string | null };

export type EvidenceItem = {
  source: string;
  snippet: string;
  doc_id?: string | null;
  score?: number | null;
};

export type AIResponse = {
  mode: string; // assistant | report
  intent: string;
  title: string;
  narrative: string;
  bullets: string[];
  metrics: Metric[];
  table?: TableData | null;
  alerts: AlertItem[];
  actions: ActionItem[];
  evidence: EvidenceItem[];
  data_scope: string[];
  confidence: number;
};

export type ScanStats = {
  records_scanned: number;
  alerts_found: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  retrieval_backend: string;
};

export type ScanPhase = {
  id: string;
  label: string;
  detail: string;
};

export type CrawlResponse = {
  digest: string;
  alerts: AlertItem[];
  scan_stats: ScanStats;
  phases: ScanPhase[];
  confidence: number;
};

export type ReportType = { id: string; label: string };

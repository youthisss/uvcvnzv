export type Mode = "day_ahead" | "horizon";

export interface Params {
  from: string;
  to: string;
  mode: Mode;
  gate: string;
  h: number;
}

export interface SeriesPoint {
  startTime: string;
  actual: number | null;
  forecast: number | null;
  publishTime: string | null;
  leadHours: number | null;
  error: number | null;
  persistence: number | null;
}

export interface SeriesResponse {
  mode: Mode;
  gate: string | null;
  horizonHours: number | null;
  points: SeriesPoint[];
}

export interface Metrics {
  n: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  nmae: number | null;
  mean_actual: number | null;
  pct_over_forecast: number | null;
  error_p50: number | null;
  error_p90: number | null;
  error_p95: number | null;
  persistence_mae: number | null;
  skill_vs_persistence: number | null;
  n_persistence: number;
}

export interface MetricsResponse {
  mode: Mode;
  summary: Metrics;
  byHour: { key: string; metrics: Metrics }[];
  missingForecasts: number;
  missingActuals: number;
}

export interface HorizonBucket {
  label: string;
  fromHours: number;
  toHours: number;
  metrics: Metrics;
}

export interface Revision {
  publishTime: string;
  leadHours: number;
  forecast: number;
  usedByGate: boolean;
}

export interface RevisionsResponse {
  target: string;
  actual: number | null;
  revisions: Revision[];
}

export const MIN_DAY = "2026-01-01";
export const MAX_DAY = "2026-01-31";

export function queryString(p: Params): string {
  const q = new URLSearchParams({
    from: p.from,
    to: p.to,
    mode: p.mode,
    gate: p.gate,
    h: String(p.h),
  });
  return q.toString();
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // body was not JSON
    }
    throw new Error("Request failed (" + res.status + "): " + detail);
  }
  return res.json() as Promise<T>;
}

export const fetchSeries = (p: Params) =>
  getJson<SeriesResponse>("/api/series?" + queryString(p));
export const fetchMetrics = (p: Params) =>
  getJson<MetricsResponse>("/api/metrics?" + queryString(p));
export const fetchHorizon = (p: Params) =>
  getJson<HorizonBucket[]>("/api/error-by-horizon?" + queryString(p));
export const fetchRevisions = (target: string, gate: string) =>
  getJson<RevisionsResponse>(
    "/api/revisions?" + new URLSearchParams({ target, gate }).toString(),
  );
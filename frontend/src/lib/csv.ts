import type { SeriesPoint } from "./api";

const HEADER = [
  "startTime",
  "actual_mw",
  "forecast_mw",
  "forecast_publishTime",
  "lead_hours",
  "error_mw",
  "persistence_mw",
];

function cell(v: number | string | null): string {
  return v == null ? "" : String(v);
}

export function toCsv(points: SeriesPoint[]): string {
  const rows = points.map((p) =>
    [p.startTime, p.actual, p.forecast, p.publishTime, p.leadHours, p.error, p.persistence]
      .map(cell)
      .join(","),
  );
  return [HEADER.join(","), ...rows].join("\n") + "\n";
}

export function downloadCsv(filename: string, text: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
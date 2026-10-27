export function mw(v: number | null | undefined, signed = false): string {
  if (v == null || Number.isNaN(v)) return "n/a";
  const s = Math.round(v).toLocaleString("en-GB");
  return signed && v > 0 ? "+" + s : s;
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v == null || Number.isNaN(v)) return "n/a";
  return (v * 100).toFixed(digits) + "%";
}

// "2026-01-14T07:30:00+00:00" -> "14 Jan 07:30 UTC"
export function stamp(iso: string | null | undefined): string {
  if (!iso) return "n/a";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "n/a";
  const day = d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", timeZone: "UTC" });
  const time = d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
  return day + " " + time + " UTC";
}

// Gate time (HH:MM) on the day before delivery day (YYYY-MM-DD), as a UTC ISO string.
export function decisionTime(day: string, gate: string): string {
  const d = new Date(day + "T" + gate + ":00Z");
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString();
}
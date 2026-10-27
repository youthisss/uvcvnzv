import type { MetricsResponse } from "../lib/api";
import { mw, pct } from "../lib/format";

interface Kpi {
  label: string;
  value: string;
  hint: string;
  tone?: "warn";
}

export function Kpis({ data }: { data: MetricsResponse }) {
  const m = data.summary;
  const items: Kpi[] = [
    { label: "MAE", value: mw(m.mae) + " MW", hint: "Mean absolute error: typical size of a miss." },
    { label: "RMSE", value: mw(m.rmse) + " MW", hint: "Like MAE but penalises large misses more." },
    {
      label: "Bias",
      value: mw(m.bias, true) + " MW",
      hint: "Mean of forecast - actual. Positive: forecast is too high, so you under-buy.",
      tone: m.bias != null && m.bias > 0 ? "warn" : undefined,
    },
    { label: "nMAE", value: pct(m.nmae), hint: "MAE divided by mean actual generation." },
    {
      label: "Over-forecast",
      value: pct(m.pct_over_forecast, 0),
      hint: "Share of hours where forecast exceeded actual (buyer is short).",
      tone: m.pct_over_forecast != null && m.pct_over_forecast > 0.6 ? "warn" : undefined,
    },
    {
      label: "Buffer P90",
      value: mw(m.error_p90) + " MW",
      hint: "90% of hours the forecast overshoots by less than this. P50 " + mw(m.error_p50) +
        ", P95 " + mw(m.error_p95) + " MW.",
    },
    {
      label: "Skill vs persistence",
      value: pct(m.skill_vs_persistence, 0),
      hint: "1 - MAE / MAE of 'same hour yesterday'. Positive beats the naive baseline.",
    },
    { label: "Hours scored", value: String(m.n), hint: data.missingForecasts + " without forecast, " + data.missingActuals + " without actual." },
  ];
  return (
    <section className="kpis" aria-label="Key metrics">
      {items.map((k) => (
        <div key={k.label} className={"card kpi" + (k.tone ? " " + k.tone : "")} title={k.hint}>
          <span className="kpi-label">{k.label}</span>
          <span className="kpi-value">{k.value}</span>
          <span className="kpi-hint">{k.hint}</span>
        </div>
      ))}
    </section>
  );
}
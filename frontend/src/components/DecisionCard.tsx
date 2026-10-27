import type { Params, SeriesPoint } from "../lib/api";
import { decisionTime, mw, stamp } from "../lib/format";

export function DecisionCard({ params, points }: { params: Params; points: SeriesPoint[] }) {
  const day = params.to;
  const dayPoints = points.filter((p) => p.startTime.slice(0, 10) === day);
  const withF = dayPoints.filter((p) => p.forecast != null);
  const pubs = [...new Set(withF.map((p) => p.publishTime).filter((x): x is string => !!x))].sort();
  const all = [...new Set(points.map((p) => p.publishTime).filter((x): x is string => !!x))].sort();

  let heading: string;
  let detail: string;
  if (params.mode === "day_ahead") {
    heading = "Decision for " + day;
    detail = "Made " + stamp(decisionTime(day, params.gate)) +
      ". Only forecasts published up to then are used.";
  } else {
    heading = "Fixed-horizon view";
    detail = "Each hour uses the latest forecast published at least " + params.h +
      " h before it starts.";
  }

  const peak = withF.reduce<SeriesPoint | null>((a, p) => (!a || p.forecast! > a.forecast! ? p : a), null);
  const mean = withF.length ? withF.reduce((s, p) => s + p.forecast!, 0) / withF.length : null;

  return (
    <section className="card decision" aria-label="Forecast in use">
      <h2>{heading}</h2>
      <p>{detail}</p>
      <dl>
        <div>
          <dt>Forecast publishTime in use ({day})</dt>
          <dd>{pubs.length === 0 ? "none available" : pubs.map(stamp).join(", ")}</dd>
        </div>
        <div>
          <dt>Mean / peak forecast that day</dt>
          <dd>
            {mw(mean)} MW / {peak ? mw(peak.forecast) + " MW at " + stamp(peak.startTime).slice(7, 12) : "n/a"}
          </dd>
        </div>
        <div>
          <dt>All forecast publishes in range</dt>
          <dd>
            {all.length ? all.length + " (" + stamp(all[0]) + " to " + stamp(all[all.length - 1]) + ")" : "none"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
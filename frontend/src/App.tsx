import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Controls } from "./components/Controls";
import { DataTable } from "./components/DataTable";
import { DecisionCard } from "./components/DecisionCard";
import { ErrorBars } from "./components/ErrorBars";
import { Kpis } from "./components/Kpis";
import { QueryState } from "./components/QueryState";
import { Revisions } from "./components/Revisions";
import { SeriesChart } from "./components/SeriesChart";
import { fetchHorizon, fetchMetrics, fetchSeries, MAX_DAY, MIN_DAY, type Params } from "./lib/api";
import { mw, pct } from "./lib/format";

function validate(p: Params): string | null {
  if (!p.from || !p.to) return "Choose both dates.";
  if (p.from > p.to) return "The start date must be on or before the end date.";
  if (p.from < MIN_DAY || p.to > MAX_DAY) return "Dates must be within January 2026.";
  if (!/^\d{2}:\d{2}$/.test(p.gate)) return "Enter a gate time.";
  return null;
}

export default function App() {
  const [params, setParams] = useState<Params>({
    from: MIN_DAY, to: MAX_DAY, mode: "day_ahead", gate: "09:00", h: 24,
  });
  const problem = validate(params);
  const enabled = problem === null;
  const series = useQuery({ queryKey: ["series", params], queryFn: () => fetchSeries(params), enabled });
  const metrics = useQuery({ queryKey: ["metrics", params], queryFn: () => fetchMetrics(params), enabled });
  const horizon = useQuery({ queryKey: ["horizon", params.from, params.to], queryFn: () => fetchHorizon(params), enabled });

  return (
    <main>
      <header>
        <h1>Wind forecast check</h1>
        <p className="muted">
          GB national wind, Elexon BMRS (WINDFOR forecasts vs FUELHH actuals). Purchase decisions for
          January 2026. Error = forecast - actual.
        </p>
      </header>

      <Controls value={params} onChange={setParams} problem={problem} />

      {enabled && (
        <>
          <QueryState query={series} height={140} isEmpty={(d) => d.points.every((p) => p.forecast == null)}
            emptyText="No forecast was available at this decision time.">
            {(d) => <DecisionCard params={params} points={d.points} />}
          </QueryState>

          <QueryState query={metrics} height={120} isEmpty={(d) => d.summary.n === 0}
            emptyText="No hours with both a forecast and an actual in this range.">
            {(d) => (
              <>
                <Kpis data={d} />
                <p className="takeaway">
                  {d.summary.bias != null && d.summary.bias > 0
                    ? "The forecast was above actual in " + pct(d.summary.pct_over_forecast, 0) +
                      " of hours (average " + mw(d.summary.bias, true) + " MW). Buying only to the forecast would leave you short; a buffer of about " +
                      mw(d.summary.error_p90) + " MW covers 90% of hours."
                    : "The forecast is not systematically above actual in this range (bias " + mw(d.summary.bias, true) + " MW)."}
                </p>
              </>
            )}
          </QueryState>

          <section className="card" aria-label="Actual versus forecast">
            <h2>Actual vs forecast</h2>
            <QueryState query={series} height={380} isEmpty={(d) => d.points.length === 0}>
              {(d) => <SeriesChart points={d.points} />}
            </QueryState>
          </section>

          <div className="two">
            <section className="card" aria-label="Error by horizon">
              <h2>Error by lead time</h2>
              <p className="muted">All forecasts published for these targets, grouped by how far ahead they were issued.</p>
              <QueryState query={horizon} isEmpty={(d) => d.length === 0}>
                {(d) => <ErrorBars rows={d} title="Error by forecast lead time" xLabel="Hours before delivery" />}
              </QueryState>
            </section>
            <section className="card" aria-label="Error by hour of day">
              <h2>Error by hour of day</h2>
              <p className="muted">Under the current forecast basis, by UK hour of the delivery time.</p>
              <QueryState query={metrics} isEmpty={(d) => d.byHour.length === 0}>
                {(d) => (
                  <ErrorBars rows={d.byHour.map((r) => ({ label: r.key.slice(0, 2), metrics: r.metrics }))}
                    title="Error by hour of day" xLabel="Hour of day" />
                )}
              </QueryState>
            </section>
          </div>

          <Revisions gate={params.gate} />

          <QueryState query={series} height={200} isEmpty={(d) => d.points.length === 0}>
            {(d) => <DataTable points={d.points} filename={"wind-forecast-" + params.from + "_" + params.to + ".csv"} />}
          </QueryState>
        </>
      )}

      <footer className="muted">
        Data: Elexon BMRS (snapshot). The day-ahead gate time is configurable; verify the exact gate
        closure with your market operations team.
      </footer>
    </main>
  );
}
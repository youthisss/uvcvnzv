import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fetchRevisions, MAX_DAY, MIN_DAY } from "../lib/api";
import { mw, stamp } from "../lib/format";
import { QueryState } from "./QueryState";

interface DotProps {
  cx?: number;
  cy?: number;
  payload?: { usedByGate: boolean };
}

function Dot({ cx, cy, payload }: DotProps) {
  if (cx == null || cy == null) return null;
  const used = payload?.usedByGate;
  return <circle cx={cx} cy={cy} r={used ? 7 : 3.5} fill={used ? "var(--accent)" : "var(--forecast)"} />;
}

export function Revisions({ gate }: { gate: string }) {
  const [day, setDay] = useState("2026-01-15");
  const [hour, setHour] = useState(12);
  const target = day + "T" + String(hour).padStart(2, "0") + ":00:00Z";
  const q = useQuery({
    queryKey: ["revisions", target, gate],
    queryFn: () => fetchRevisions(target, gate),
    enabled: day >= MIN_DAY && day <= MAX_DAY,
  });
  return (
    <section className="card" aria-label="Forecast revisions">
      <h2>How one forecast changed over time</h2>
      <p className="muted">
        Every forecast issued before a single target hour. The large dot is the one available at the
        decision gate; the line is what was actually generated.
      </p>
      <div className="row">
        <label>Delivery day
          <input type="date" min={MIN_DAY} max={MAX_DAY} value={day} onChange={(e) => setDay(e.target.value)} />
        </label>
        <label>Hour (UTC)
          <input type="number" min={0} max={23} value={hour}
            onChange={(e) => setHour(Math.min(23, Math.max(0, Number(e.target.value) || 0)))} />
        </label>
      </div>
      <QueryState query={q} height={240} isEmpty={(d) => d.revisions.length === 0}>
        {(d) => (
          <div className="chart" role="img" aria-label="Forecast revisions for one target hour">
            <ResponsiveContainer>
              <LineChart
                data={d.revisions
                  .filter((r) => r.leadHours >= 0)
                  .map((r) => ({ ...r, label: stamp(r.publishTime).slice(0, 12) }))}
                margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
                <XAxis dataKey="label" minTickGap={24} stroke="var(--muted)" />
                <YAxis
                  domain={[
                    (lo: number) => Math.floor(Math.min(lo, d.actual ?? lo) / 500) * 500,
                    (hi: number) => Math.ceil(Math.max(hi, d.actual ?? hi) / 500) * 500,
                  ]}
                  tickFormatter={(v: number) => mw(v)} stroke="var(--muted)" width={56} />
                <Tooltip formatter={(v: number) => mw(v) + " MW"} />
                {d.actual != null && (
                  <ReferenceLine y={d.actual} stroke="var(--actual)" strokeDasharray="5 3"
                    label={{ value: "Actual " + mw(d.actual), fill: "var(--actual)", position: "insideTopRight" }} />
                )}
                <Line dataKey="forecast" name="Forecast" stroke="var(--forecast)" dot={<Dot />} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </QueryState>
    </section>
  );
}
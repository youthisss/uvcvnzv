import { useState } from "react";
import {
  Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { SeriesPoint } from "../lib/api";
import { mw, stamp } from "../lib/format";

interface Row {
  p: SeriesPoint;
  t: string;
  actual: number | null;
  forecast: number | null;
  persistence: number | null;
  lo: number | null;
  band: number | null;
}

function toRow(p: SeriesPoint): Row {
  const both = p.actual != null && p.forecast != null;
  return {
    p,
    t: p.startTime,
    actual: p.actual,
    forecast: p.forecast,
    persistence: p.persistence,
    lo: both ? Math.min(p.actual!, p.forecast!) : null,
    band: both ? Math.abs(p.forecast! - p.actual!) : null,
  };
}

function Tip({ active, payload }: { active?: boolean; payload?: { payload: Row }[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload.p;
  return (
    <div className="tip">
      <strong>{stamp(p.startTime)}</strong>
      <div>Actual: {mw(p.actual)} MW</div>
      <div>Forecast: {mw(p.forecast)} MW</div>
      <div>Error: {mw(p.error, true)} MW</div>
      <div className="muted">Forecast published {stamp(p.publishTime)}</div>
    </div>
  );
}

const tick = (t: string) => stamp(t).slice(0, 12);

export function SeriesChart({ points }: { points: SeriesPoint[] }) {
  const [showBase, setShowBase] = useState(false);
  const data = points.map(toRow);
  return (
    <div>
      <label className="check">
        <input type="checkbox" checked={showBase} onChange={(e) => setShowBase(e.target.checked)} />
        Show persistence baseline (same hour yesterday)
      </label>
      <div className="chart tall" role="img" aria-label="Actual versus forecast wind generation">
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
            <XAxis dataKey="t" tickFormatter={tick} minTickGap={48} stroke="var(--muted)" />
            <YAxis tickFormatter={(v: number) => mw(v / 1000) + " GW"} stroke="var(--muted)" width={64} />
            <Tooltip content={<Tip />} />
            <Legend />
            <Area dataKey="lo" stackId="b" stroke="none" fill="none" legendType="none" isAnimationActive={false} />
            <Area dataKey="band" stackId="b" name="Error band" stroke="none" fill="var(--forecast)" fillOpacity={0.22} isAnimationActive={false} />
            <Line dataKey="actual" name="Actual" stroke="var(--actual)" dot={false} strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="forecast" name="Forecast (as of decision)" stroke="var(--forecast)" dot={false} strokeWidth={2} isAnimationActive={false} />
            {showBase && (
              <Line dataKey="persistence" name="Persistence" stroke="var(--muted)" strokeDasharray="4 3" dot={false} isAnimationActive={false} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
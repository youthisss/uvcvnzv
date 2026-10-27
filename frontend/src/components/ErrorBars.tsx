import {
  Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Metrics } from "../lib/api";
import { mw } from "../lib/format";

export interface BarRow {
  label: string;
  metrics: Metrics;
}

export function ErrorBars({ rows, title, xLabel }: { rows: BarRow[]; title: string; xLabel: string }) {
  const data = rows.map((r) => ({
    label: r.label,
    MAE: r.metrics.mae,
    Bias: r.metrics.bias,
    n: r.metrics.n,
  }));
  return (
    <div className="chart" role="img" aria-label={title}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 16, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
          <XAxis dataKey="label" stroke="var(--muted)" interval="preserveStartEnd" minTickGap={8}
            label={{ value: xLabel, position: "insideBottom", offset: -10, fill: "var(--muted)" }} />
          <YAxis tickFormatter={(v: number) => mw(v)} stroke="var(--muted)" width={56} />
          <Tooltip formatter={(v: number) => mw(v) + " MW"} />
          <Legend verticalAlign="top" />
          <ReferenceLine y={0} stroke="var(--muted)" />
          <Bar dataKey="MAE" fill="var(--actual)" isAnimationActive={false} />
          <Bar dataKey="Bias" fill="var(--forecast)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
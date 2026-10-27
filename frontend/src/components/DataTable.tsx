import type { SeriesPoint } from "../lib/api";
import { downloadCsv, toCsv } from "../lib/csv";
import { mw, stamp } from "../lib/format";

export function DataTable({ points, filename }: { points: SeriesPoint[]; filename: string }) {
  return (
    <section className="card" aria-label="Data table">
      <div className="row between">
        <h2>Hourly data</h2>
        <button onClick={() => downloadCsv(filename, toCsv(points))}>Export CSV</button>
      </div>
      <div className="table-wrap" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th>Target (UTC)</th><th>Actual MW</th><th>Forecast MW</th><th>Error MW</th>
              <th>Forecast publishTime</th><th>Lead h</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={p.startTime} className={p.forecast == null || p.actual == null ? "gap" : ""}>
                <td>{stamp(p.startTime)}</td>
                <td>{mw(p.actual)}</td>
                <td>{mw(p.forecast)}</td>
                <td>{mw(p.error, true)}</td>
                <td>{stamp(p.publishTime)}</td>
                <td>{p.leadHours == null ? "n/a" : p.leadHours.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
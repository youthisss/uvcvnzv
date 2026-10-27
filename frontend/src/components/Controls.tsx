import { MAX_DAY, MIN_DAY, type Mode, type Params } from "../lib/api";

interface Props {
  value: Params;
  onChange: (p: Params) => void;
  problem: string | null;
}

export function Controls({ value, onChange, problem }: Props) {
  const set = (patch: Partial<Params>) => onChange({ ...value, ...patch });
  return (
    <section className="card controls" aria-label="Controls">
      <label>
        From
        <input type="date" min={MIN_DAY} max={MAX_DAY} value={value.from}
          onChange={(e) => set({ from: e.target.value })} />
      </label>
      <label>
        To
        <input type="date" min={MIN_DAY} max={MAX_DAY} value={value.to}
          onChange={(e) => set({ to: e.target.value })} />
      </label>
      <label>
        Forecast basis
        <select value={value.mode} onChange={(e) => set({ mode: e.target.value as Mode })}>
          <option value="day_ahead">Day-ahead decision (D-1 gate)</option>
          <option value="horizon">Fixed horizon before delivery</option>
        </select>
      </label>
      {value.mode === "day_ahead" ? (
        <label>
          Gate time (UK, D-1)
          <input type="time" value={value.gate} onChange={(e) => set({ gate: e.target.value })} />
        </label>
      ) : (
        <label>
          Horizon (hours ahead)
          <input type="number" min={0} max={72} step={1} value={value.h}
            onChange={(e) => set({ h: Math.min(72, Math.max(0, Number(e.target.value) || 0)) })} />
        </label>
      )}
      {problem && <p className="problem" role="alert">{problem}</p>}
    </section>
  );
}
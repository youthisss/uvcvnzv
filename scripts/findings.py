"""Print the January 2026 findings quoted in docs/video-script.md. Run: uv run python ../scripts/findings.py (from backend/)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import pandas as pd
from datetime import time
from app.store import get_store
from app.frame import build_frame
from app.metrics import compute_metrics
s = get_store()
S, E = pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-02-01", tz="UTC")
def fr(**k): return build_frame(s.actuals_hourly, s.forecasts, S, E, **k)
print("== gate sensitivity")
for g in ["06:00","08:00","09:00","09:30","12:00","16:00"]:
    h, m = map(int, g.split(":")); f = fr(gate=time(h, m)); mm = compute_metrics(f)
    print(g, "n", mm.n, "MAE", round(mm.mae), "bias", round(mm.bias), "p90", round(mm.error_p90), "used publishes", sorted(f.publishTime.dropna().dt.strftime("%H:%M").unique()))
f = fr(); f["day"] = f.startTime.dt.date
d = f.groupby("day").apply(lambda g: pd.Series({"mae": (g.forecast-g.actual).abs().mean(), "bias": (g.forecast-g.actual).mean(), "act": g.actual.mean()}), include_groups=False)
print("== worst days by MAE\n", d.sort_values("mae", ascending=False).head(4).round(0))
print("== best days by MAE\n", d.sort_values("mae").head(3).round(0))
print("days over-forecast:", int((d.bias>0).sum()), "of", len(d))
f["err"] = f.forecast - f.actual
f["lvl"] = pd.qcut(f.actual, 3, labels=["low","mid","high"])
print("== by actual-level tercile\n", f.groupby("lvl", observed=True).agg(n=("err","size"), mean_actual=("actual","mean"), bias=("err","mean"), mae=("err", lambda x: x.abs().mean())).round(0))
print("share of |err| in worst 10% hours:", round(f.err.abs().nlargest(len(f)//10).sum()/f.err.abs().sum(),3))
print("max over-forecast", round(f.err.max()), "max under-forecast", round(f.err.min()))
print("daily mean-error std", round(d.bias.std()))
print("corr bias-day vs actual mean", round(d.bias.corr(d.act),2))
ha = f.groupby(f.startTime.dt.hour).err.apply(lambda x: x.abs().mean()).round(0)
print("hour MAE min/max:", ha.idxmin(), ha.min(), ha.idxmax(), ha.max())
print("first half vs second half bias:", round(f[f.startTime<"2026-01-16"].err.mean()), round(f[f.startTime>="2026-01-16"].err.mean()))
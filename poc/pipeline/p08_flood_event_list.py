"""Build the GEE-3 EVENTS list: rain/cyclone events that hit pilot mandals (peak >= IMD heavy, or cyclone),
merged per district and week; keep the 4 rainiest per district 2020-2025, every named cyclone, and every 2026 event (live season)."""
import json

import pandas as pd

from common import DERIVED, POC

ev = pd.read_csv(DERIVED / "event_catalogue_era5.csv", dtype={"district_code": str})
pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
ev = ev[ev.adm3_id.isin(pil.adm3_id) & ev.type.isin(["extreme_rain", "unseasonal_rain", "cyclone"])]
ev = ev[(ev.type == "cyclone") | (ev.peak_day_mm >= 64.5)].copy()
ev["start"], ev["end"] = pd.to_datetime(ev.start), pd.to_datetime(ev.end)
ev["rain3d"] = ev.value.where(ev.type != "cyclone")
ev["wk"] = ev.end.dt.to_period("W")
g = ev.groupby(["district_code", "wk"]).agg(start=("start", "min"), end=("end", "max"),
    types=("type", lambda s: "+".join(sorted(set(s)))), rain3d=("rain3d", "max"),
    cyclone=("severity", lambda s: ";".join(sorted({x.split(";")[0] for x, t in zip(s, ev.loc[s.index, "type"]) if t == "cyclone"})))).reset_index()
g["rain3d"] = g.rain3d.fillna(0)
hist = g[g.end.dt.year <= 2025].sort_values("rain3d", ascending=False).groupby("district_code").head(4)
live = g[g.end.dt.year == 2026]
named = g[g.cyclone.str.len() > 0]
sel = pd.concat([hist, live, named]).drop_duplicates(["district_code", "wk"]).sort_values(["district_code", "start"])
# one storm can land in two weekly buckets (rain week + cyclone day): merge starts within 4 days
sel["grp"] = (sel.groupby("district_code").start.diff().dt.days.fillna(99) > 4).cumsum()
sel = sel.groupby("grp").agg(district_code=("district_code", "first"), start=("start", "min"), end=("end", "max"),
    types=("types", lambda s: "+".join(sorted(set("+".join(s).split("+"))))), rain3d=("rain3d", "max"),
    cyclone=("cyclone", lambda s: ";".join(sorted({c for c in s if c})))).reset_index(drop=True)
sel["id"] = sel.district_code + "_" + sel.start.dt.strftime("%Y%m%d") + sel.cyclone.str.split(":").str[0].map(lambda c: "_" + c if c else "")
print(sel[["id", "start", "end", "types", "rain3d", "cyclone"]].to_string(index=False))
items = [dict(id=r.id, start=r.start.strftime("%Y-%m-%d"), end=r.end.strftime("%Y-%m-%d"), dists=[r.district_code]) for r in sel.itertuples()]
js = "var EVENTS = [\n" + ",\n".join("  " + json.dumps(i) for i in items) + "\n];"
gee = POC / "gee" / "GEE3_s1_flood_events.js"
s = gee.read_text(encoding="utf-8")
a = s.index("var EVENTS = ["); b = s.index("];", a) + 2
gee.write_text(s[:a] + js + s[b:], encoding="utf-8")
sel.to_csv(DERIVED / "flood_events_gee3.csv", index=False)
print(f"\n{len(items)} events written into GEE3")

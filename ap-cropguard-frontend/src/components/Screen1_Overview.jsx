import React, { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
} from "recharts";
import {
  getDistrictOverview, getDistrictMandals,
  getSatelliteTimeseries, getPipelineStatus,
} from "../utils/api";
import { THRESHOLD_LOSS_PCT } from "../utils/constants";

// ── Helpers ──────────────────────────────────────────────────────

function fmt(n) { return n != null ? Number(n).toLocaleString("en-IN") : "—"; }
function fmtLakh(n) { return n != null ? (n / 100000).toFixed(1) + " L" : "—"; }
function noUnderscore(s) { return s ? s.replace(/_/g, " ") : ""; }

function vciColor(status) {
  if (!status) return "var(--text-muted)";
  if (status === "NORMAL")          return "var(--green)";
  if (status === "MODERATE_STRESS") return "var(--amber)";
  if (status === "SEVERE_DROUGHT")  return "#EA580C";
  return "var(--red)";
}
function vciTextColor(status) { return vciColor(status); }
function vciBg(status) {
  if (status === "NORMAL")          return "var(--green-dim)";
  if (status === "MODERATE_STRESS") return "var(--amber-dim)";
  if (status === "SEVERE_DROUGHT")  return "#431407";
  return "var(--red-dim)";
}

function spiColor(v) {
  if (v == null) return "var(--text-muted)";
  if (v <= -1.5) return "var(--red-light)";
  if (v <= -1.0) return "var(--amber-light)";
  return "var(--green-light)";
}
function lossColor(v) {
  if (v == null) return "var(--text-muted)";
  if (v >= 43)  return "var(--red-light)";
  if (v >= 20)  return "var(--amber-light)";
  return "var(--green-light)";
}

// ── Sub-components ────────────────────────────────────────────────

function SkeletonCard({ h = 80 }) {
  return (
    <div className="skeleton" style={{ borderRadius: 8, height: h }} />
  );
}

function StatCards({ overview }) {
  if (!overview) return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
      {[0,1,2,3].map(i => <SkeletonCard key={i} h={72} />)}
    </div>
  );

  const affected = overview.mandals_affected ?? 0;
  const above    = overview.mandals_above_threshold ?? 0;
  const areaHa   = overview.total_affected_area_ha ?? 0;
  const alert    = overview.alert_level ?? "NORMAL";

  const alertColor =
    ["SEVERE","EXTREME","EXCEPTIONAL_DRY","EXTREMELY_DRY","SEVERELY_DRY"].includes(alert)
      ? "var(--red)" :
    ["MODERATE","MODERATELY_DRY"].includes(alert)
      ? "var(--amber)" : "var(--green)";

  const cards = [
    {
      value: affected,
      label: "MANDALS AFFECTED",
      color: affected > 15 ? "var(--red)" : affected > 5 ? "var(--amber)" : "var(--green)",
    },
    {
      value: above,
      label: "ABOVE 43% THRESHOLD",
      color: above > 0 ? "var(--red)" : "var(--green)",
    },
    {
      value: fmtLakh(areaHa) + " ha",
      label: "AFFECTED AREA",
      color: "var(--amber)",
    },
    {
      value: noUnderscore(alert),
      label: "ALERT LEVEL",
      color: alertColor,
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
      {cards.map((c) => (
        <div key={c.label} className="stat-card" style={{ borderLeftColor: c.color }}>
          <div className="stat-card__label">{c.label}</div>
          <div className="stat-card__value" style={{ fontSize: 22 }}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}

function MandalGrid({ mandals, selectedMandal, onMandalSelect }) {
  if (!mandals.length) return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 6 }}>
      {Array(27).fill(0).map((_,i) => <SkeletonCard key={i} h={52} />)}
    </div>
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 6 }}>
      {mandals.map((m) => {
        const isSelected = m.mandal_id === selectedMandal;
        const vc = vciColor(m.vci_status);
        const vbg = vciBg(m.vci_status);
        return (
          <div
            key={m.mandal_id}
            onClick={() => onMandalSelect(m.mandal_id)}
            style={{
              position: "relative",
              padding: "7px 9px",
              borderRadius: 6,
              cursor: "pointer",
              background: isSelected ? "rgba(22,163,74,0.08)" : "var(--bg-card)",
              border: isSelected ? "1.5px solid var(--green)" : "1px solid var(--border)",
              transition: "all 0.15s",
            }}
            onMouseEnter={e => { if (!isSelected) e.currentTarget.style.borderColor = "var(--border-bright)"; }}
            onMouseLeave={e => { if (!isSelected) e.currentTarget.style.borderColor = "var(--border)"; }}
          >
            {/* Threshold breach dot */}
            {m.threshold_breached && (
              <div style={{
                position: "absolute", top: 5, right: 5,
                width: 6, height: 6, borderRadius: "50%",
                background: "var(--red)", boxShadow: "0 0 4px var(--red)",
              }} />
            )}
            {/* Name + VCI badge */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 4, marginBottom: 3 }}>
              <span style={{ fontFamily: "var(--font-display)", fontSize: 11, color: "var(--text-primary)", lineHeight: 1.2 }}>
                {m.mandal_name}
              </span>
              <span style={{
                fontSize: 9, fontWeight: 700, padding: "1px 5px",
                borderRadius: 999, background: vbg, color: vc,
                whiteSpace: "nowrap", letterSpacing: "0.03em",
              }}>
                {m.vci != null ? m.vci.toFixed(0) : "—"}
              </span>
            </div>
            {/* Crop */}
            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
              {m.dominant_crop}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function NDVIChart({ timeseries, season }) {
  if (!timeseries) return <SkeletonCard h={280} />;

  const lineColor = season === "Kharif_2023" ? "var(--red)" : "var(--green)";
  const fillColor = season === "Kharif_2023"
    ? "rgba(220,38,38,0.12)" : "rgba(22,163,74,0.12)";

  // Merge baseline into each point
  const bb = timeseries.baseline_band ?? {};
  const data = (timeseries.timeseries ?? []).map((w, i) => ({
    ...w,
    baseline_upper: bb.upper?.[i] ?? 0,
    baseline_lower: bb.lower?.[i] ?? 0,
    baseline_mean:  bb.mean?.[i]  ?? 0,
  }));

  const lastWeek = data.length > 0 ? data[data.length - 1].week : null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload ?? {};
    return (
      <div style={{
        background: "var(--bg-card)", border: "1px solid var(--border-bright)",
        borderRadius: 6, padding: "8px 12px", fontSize: 12,
      }}>
        <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>Week {label} — {d.date}</div>
        <div style={{ color: lineColor }}>NDVI: <b>{d.ndvi?.toFixed(3)}</b></div>
        <div style={{ color: "var(--blue-light)" }}>VCI: <b>{d.vci?.toFixed(1)}%</b></div>
        <div style={{ color: "var(--text-muted)" }}>Baseline: {d.baseline_mean?.toFixed(3)}</div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="ndviGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={season === "Kharif_2023" ? "#DC2626" : "#16A34A"} stopOpacity={0.3} />
            <stop offset="95%" stopColor={season === "Kharif_2023" ? "#DC2626" : "#16A34A"} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="week"
          tick={{ fill: "var(--text-muted)", fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: "var(--border)" }}
          tickFormatter={(v) => (v % 3 === 1 ? `W${v}` : "")}
        />
        <YAxis
          domain={[0, 1]}
          tickCount={5}
          tick={{ fill: "var(--text-muted)", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        {/* Baseline band */}
        <Area
          type="monotone"
          dataKey="baseline_upper"
          stroke="none"
          fill="rgba(255,255,255,0.04)"
          fillOpacity={1}
          isAnimationActive={false}
        />
        {/* Current season NDVI */}
        <Area
          type="monotone"
          dataKey="ndvi"
          stroke={lineColor}
          strokeWidth={2}
          fill="url(#ndviGrad)"
          dot={false}
          activeDot={{ r: 4, fill: lineColor }}
        />
        {/* Baseline mean */}
        <Area
          type="monotone"
          dataKey="baseline_mean"
          stroke="rgba(255,255,255,0.15)"
          strokeWidth={1}
          strokeDasharray="4 2"
          fill="none"
          dot={false}
        />
        {lastWeek && (
          <ReferenceLine
            x={lastWeek}
            stroke="var(--amber)"
            strokeDasharray="4 4"
            label={{ value: "NOW", position: "top", fill: "var(--amber)", fontSize: 10 }}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}

function TriggerCards({ m }) {
  if (!m) return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
      {[0,1,2].map(i => <SkeletonCard key={i} h={72} />)}
    </div>
  );

  const cards = [
    {
      value: m.spi_value?.toFixed(2) ?? "—",
      label: noUnderscore(m.spi_category) || "SPI",
      title: "SPI",
      color: spiColor(m.spi_value),
    },
    {
      value: m.vci != null ? m.vci.toFixed(1) + "%" : "—",
      label: noUnderscore(m.vci_status) || "VCI STATUS",
      title: "VCI",
      color: vciColor(m.vci_status),
    },
    {
      value: m.estimated_loss_pct != null ? m.estimated_loss_pct.toFixed(1) + "%" : "—",
      label: "ESTIMATED CROP LOSS",
      title: "LOSS",
      color: lossColor(m.estimated_loss_pct),
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
      {cards.map((c) => (
        <div key={c.title} className="card-sm" style={{ textAlign: "center" }}>
          <div className="label-text" style={{ marginBottom: 4 }}>{c.title}</div>
          <div style={{
            fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700,
            color: c.color, lineHeight: 1,
          }}>
            {c.value}
          </div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 3 }}>
            {c.label}
          </div>
        </div>
      ))}
    </div>
  );
}

function PipelineTimeline({ pipeline }) {
  if (!pipeline) return <SkeletonCard h={200} />;

  const stages = pipeline.pipeline_stages ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {stages.map((s, i) => {
        const isDone    = s.status === "COMPLETE";
        const isActive  = s.status === "IN_PROGRESS";
        const isLast    = i === stages.length - 1;

        const dotColor  = isDone ? "var(--green)" : isActive ? "var(--amber)" : "var(--border-bright)";
        const dotBg     = isDone ? "var(--green-dim)" : isActive ? "var(--amber-dim)" : "var(--bg-elevated)";

        return (
          <div key={s.stage_id} style={{ display: "flex", gap: 10 }}>
            {/* Timeline track */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 24 }}>
              <div style={{
                width: 20, height: 20, borderRadius: "50%",
                background: dotBg, border: `2px solid ${dotColor}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 10, color: dotColor, flexShrink: 0,
                animation: isActive ? "pulse-dot 1.8s infinite" : "none",
              }}>
                {isDone ? "✓" : isActive ? "●" : "○"}
              </div>
              {!isLast && (
                <div style={{ width: 2, flex: 1, minHeight: 16, background: isDone ? "var(--green-dim)" : "var(--border)", margin: "2px 0" }} />
              )}
            </div>

            {/* Content */}
            <div style={{ flex: 1, paddingBottom: isLast ? 0 : 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: isDone ? "var(--text-primary)" : "var(--text-muted)" }}>
                  {s.label}
                </div>
                <span style={{
                  fontSize: 10, fontWeight: 600,
                  color: "var(--amber-light)", background: "var(--amber-dim)",
                  padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap", marginLeft: 6,
                }}>
                  T+{s.hours_from_event}h
                </span>
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, lineHeight: 1.4 }}>
                {s.description}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────

export default function Screen1_Overview({ season, selectedMandal, onMandalSelect }) {
  const [overview,           setOverview]           = useState(null);
  const [mandals,            setMandals]            = useState([]);
  const [selectedMandalData, setSelectedMandalData] = useState(null);
  const [timeseries,         setTimeseries]         = useState(null);
  const [pipeline,           setPipeline]           = useState(null);
  const [loading,            setLoading]            = useState(true);
  const [error,              setError]              = useState(null);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [ovRes, mRes, plRes] = await Promise.all([
      getDistrictOverview(season),
      getDistrictMandals(season),
      getPipelineStatus(season),
    ]);
    if (ovRes.error || mRes.error) {
      setError("Data unavailable — using cached values");
    } else {
      setOverview(ovRes.data?.data ?? null);
      const mList = mRes.data?.data?.mandals ?? [];
      setMandals(mList);
      // update selectedMandalData immediately
      const found = mList.find(m => m.mandal_id === selectedMandal);
      if (found) setSelectedMandalData(found);
    }
    if (!plRes.error) setPipeline(plRes.data?.data ?? null);
    setLoading(false);
  }, [season]);

  useEffect(() => { fetchOverview(); }, [fetchOverview]);

  // Load timeseries whenever mandal or season changes
  useEffect(() => {
    if (!selectedMandal) return;
    getSatelliteTimeseries(selectedMandal, season).then(res => {
      if (!res.error) setTimeseries(res.data?.data ?? null);
    });
    // Also sync selectedMandalData from current mandals list
    const found = mandals.find(m => m.mandal_id === selectedMandal);
    if (found) setSelectedMandalData(found);
  }, [selectedMandal, season, mandals]);

  const m = selectedMandalData;
  const breached = m?.threshold_breached ?? false;

  return (
    <div className="three-col-grid" style={{ height: "calc(100vh - 88px)" }}>

      {/* ══ LEFT COLUMN ════════════════════════════════════════════ */}
      <div className="col-scroll">
        {/* Stat cards */}
        <StatCards overview={overview} />

        {/* Mandal grid */}
        <div className="card" style={{ padding: 12, flex: 1 }}>
          <div style={{ marginBottom: 8 }}>
            <div className="label-text">SELECT MANDAL</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
              27 Revenue Mandals — Kurnool District
            </div>
          </div>
          {error && !loading && (
            <div style={{ marginBottom: 8, padding: "8px 10px", background: "var(--amber-glow)", border: "1px solid var(--amber)", borderRadius: 4, fontSize: 12, color: "var(--amber-light)" }}>
              {error} <button className="btn btn-ghost" style={{ fontSize: 11, padding: "2px 8px", marginLeft: 8 }} onClick={fetchOverview}>Retry</button>
            </div>
          )}
          <MandalGrid
            mandals={mandals}
            selectedMandal={selectedMandal}
            onMandalSelect={onMandalSelect}
          />
        </div>
      </div>

      {/* ══ CENTER COLUMN ══════════════════════════════════════════ */}
      <div className="col-scroll">
        {/* Mandal header */}
        <div className="card">
          {!m ? <SkeletonCard h={52} /> : (
            <>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                <div className="display-heading" style={{ fontSize: 20 }}>{m.mandal_name}</div>
                <span style={{
                  fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 700,
                  color: spiColor(m.spi_value),
                }}>
                  SPI {m.spi_value?.toFixed(2)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <span className="badge badge-blue">{m.zone ?? "N/A"} Zone</span>
                <span className="badge badge-muted">{m.dominant_crop}</span>
                <span className="badge" style={{
                  background: vciBg(m.vci_status),
                  color: vciColor(m.vci_status),
                }}>
                  {noUnderscore(m.vci_status)}
                </span>
              </div>
            </>
          )}
        </div>

        {/* NDVI Chart */}
        <div className="card">
          <div style={{ marginBottom: 10 }}>
            <div className="section-title" style={{ marginBottom: 2 }}>
              Satellite Vegetation Index — NDVI Trend
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Current season vs 5-year historical baseline
            </div>
          </div>
          <NDVIChart timeseries={timeseries} season={season} />
        </div>

        {/* Trigger cards */}
        <div className="card">
          <div className="section-title">Parametric Trigger Status</div>
          <TriggerCards m={m} />
        </div>
      </div>

      {/* ══ RIGHT COLUMN ═══════════════════════════════════════════ */}
      <div className="col-scroll">
        {/* Threshold banner */}
        {!m ? <SkeletonCard h={64} /> : (
          <div className={`alert-banner ${breached ? "critical" : "success"}`}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13 }}>
                {breached ? "⚠ E-RELIEF THRESHOLD BREACHED" : "✓ Below Compensation Threshold"}
              </div>
              <div style={{ fontSize: 11, fontWeight: 400, marginTop: 2, opacity: 0.85 }}>
                {breached
                  ? "Compensation Eligible — Loss ≥ 43%"
                  : "Loss < 43% — No Relief Required"}
              </div>
            </div>
          </div>
        )}

        {/* 72hr pipeline */}
        <div className="card">
          <div style={{ marginBottom: 12 }}>
            <div className="section-title" style={{ marginBottom: 2 }}>
              Assessment Pipeline — 72hr Target
            </div>
            {pipeline && (
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span className="badge badge-green">
                  {pipeline.total_hours_taken}hr Completed
                </span>
                <span className="badge badge-muted">
                  Target: {pipeline.target_hours}hr
                </span>
              </div>
            )}
          </div>
          <PipelineTimeline pipeline={pipeline} />
        </div>

        {/* Mandal detail card */}
        <div className="card">
          <div className="section-title">Mandal Details</div>
          {!m ? <SkeletonCard h={80} /> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Affected Area",    value: fmt(m.affected_area_ha) + " ha" },
                { label: "NDVI Anomaly",     value: (m.ndvi_anomaly_pct > 0 ? "+" : "") + (m.ndvi_anomaly_pct?.toFixed(1) ?? "—") + "%" },
                { label: "Dominant Crop",    value: m.dominant_crop },
                { label: "Zone",             value: m.zone },
                { label: "NDVI Current",     value: m.ndvi_current?.toFixed(3) ?? "—" },
                { label: "NDVI Baseline",    value: m.ndvi_baseline?.toFixed(3) ?? "—" },
              ].map(r => (
                <div key={r.label} style={{
                  display: "flex", justifyContent: "space-between",
                  fontSize: 12, padding: "5px 0",
                  borderBottom: "1px solid var(--border-subtle)",
                }}>
                  <span style={{ color: "var(--text-muted)" }}>{r.label}</span>
                  <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{r.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

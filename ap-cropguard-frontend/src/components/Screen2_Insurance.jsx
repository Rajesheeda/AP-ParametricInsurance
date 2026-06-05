import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
  BarChart, Bar, Cell, Legend,
} from "recharts";
import {
  getMetaCrops, getMetaMandals,
  getBacktestResults, getPremiumTable,
  postParametricCalculate, postParametricSimulate,
} from "../utils/api";

// ── Helpers ──────────────────────────────────────────────────────

const fmtRupee = (v) =>
  v != null ? "₹" + Number(v).toLocaleString("en-IN") : "—";

const spiColor = (v) => {
  if (v == null) return "var(--text-muted)";
  if (v <= -1.5) return "var(--red-light)";
  if (v <= -1.0) return "var(--amber-light)";
  return "var(--green-light)";
};

const perilColor = (p) => {
  if (p === "Drought")  return "var(--amber)";
  if (p === "Flood")    return "#3B82F6";
  if (p === "DrySpell") return "#8B5CF6";
  if (p === "Heatwave") return "var(--red)";
  return "var(--text-muted)";
};

function Skeleton({ h = 40, style }) {
  return <div className="skeleton" style={{ height: h, borderRadius: 6, ...style }} />;
}

// ── Sub-components ────────────────────────────────────────────────

function LiveMetrics({ sim, threshold, loading }) {
  if (loading || !sim) return (
    <div style={{ display: "flex", gap: 8 }}>
      {[0,1,2,3].map(i => <Skeleton key={i} h={56} style={{ flex: 1 }} />)}
    </div>
  );
  const isActivated = sim.trigger_status === "ACTIVATED";
  const loss = sim.estimated_loss_pct ?? 0;
  const lossColor = loss >= (threshold ?? 43)
    ? "var(--red-light)" : loss >= 20
    ? "var(--amber-light)" : "var(--green-light)";

  const pills = [
    { label: "SPI Computed",  value: sim.spi_computed?.toFixed(3) ?? "—", color: spiColor(sim.spi_computed) },
    { label: "Loss %",        value: (sim.estimated_loss_pct ?? 0) + "%", color: lossColor },
    { label: "Payout ₹/ha",  value: fmtRupee(sim.payout_per_ha),        color: "var(--amber-light)" },
    {
      label: "Trigger",
      value: sim.trigger_status ?? "—",
      color: isActivated ? "var(--red-light)" : "var(--text-muted)",
      activated: isActivated,
    },
  ];

  return (
    <div style={{ display: "flex", gap: 8 }}>
      {pills.map((p) => (
        <div
          key={p.label}
          className={`metric-pill${p.activated ? " activated" : ""}`}
          style={{ flex: 1 }}
        >
          <div className="metric-pill__value" style={{ color: p.color, fontSize: 16 }}>
            {p.value}
          </div>
          <div className="metric-pill__label">{p.label}</div>
        </div>
      ))}
    </div>
  );
}

function PayoutCurveChart({ data, threshold }) {
  if (!data?.length) return (
    <div style={{
      height: 220, display: "flex", alignItems: "center",
      justifyContent: "center", background: "var(--bg-elevated)",
      borderRadius: 6, border: "1px dashed var(--border-bright)",
    }}>
      <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
        Click Calculate to generate payout curve
      </span>
    </div>
  );

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 20 }}>
        <defs>
          <linearGradient id="payoutGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor="#4A5D82" stopOpacity={0.15} />
            <stop offset={`${threshold ?? 43}%`} stopColor="#4A5D82" stopOpacity={0.15} />
            <stop offset={`${threshold ?? 43}%`} stopColor="#16A34A" stopOpacity={0.12} />
            <stop offset="100%" stopColor="#16A34A" stopOpacity={0.12} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="loss_pct"
          tick={{ fill: "var(--text-muted)", fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: "var(--border)" }}
          label={{ value: "Crop Loss (%)", position: "insideBottom", offset: -12, fill: "var(--text-muted)", fontSize: 11 }}
        />
        <YAxis
          tick={{ fill: "var(--text-muted)", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => "₹" + (v / 1000).toFixed(0) + "k"}
        />
        <Tooltip
          contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 6 }}
          labelStyle={{ color: "var(--text-muted)" }}
          formatter={(v) => [fmtRupee(v), "Payout/ha"]}
          labelFormatter={(l) => `Loss: ${l}%`}
        />
        <ReferenceLine
          x={threshold ?? 43}
          stroke="var(--red)"
          strokeDasharray="5 5"
          label={{ value: "Threshold", position: "top", fill: "var(--red)", fontSize: 10 }}
        />
        <Line
          type="monotone"
          dataKey="payout_per_ha"
          stroke="var(--green)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "var(--green)" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function TermSheet({ result, mandalName }) {
  if (!result) return null;
  const ts = result.term_sheet ?? {};
  const breached = result.threshold_43_breached;

  return (
    <div className="card" style={{ border: "1px solid rgba(245,158,11,0.4)", animation: "fade-in 0.3s ease" }}>
      <div className="section-title" style={{ marginBottom: 12 }}>Term Sheet</div>

      {/* Context row */}
      <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
        <span className="badge badge-muted">{result.crop}</span>
        <span className="badge" style={{ background: "rgba(245,158,11,0.15)", color: "var(--amber-light)" }}>
          {result.peril}
        </span>
        <span className="badge badge-blue">{mandalName ?? result.mandal}</span>
        <span className="badge badge-muted">
          Day {result.das_at_event} — {result.crop_stage}
        </span>
        <span className="badge badge-muted">Kc {result.kc_multiplier}×</span>
      </div>

      {/* Key financials */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, marginBottom: 10 }}>
        {[
          { label: "Sum Insured/ha", value: fmtRupee(ts.sum_insured_per_ha) },
          { label: "Premium Rate",   value: (ts.premium_rate_pct ?? "—") + "%" },
          { label: "Premium/ha",     value: fmtRupee(ts.premium_per_ha) },
        ].map(f => (
          <div key={f.label} style={{ textAlign: "center", padding: "8px 0", borderRadius: 4, background: "var(--bg-elevated)" }}>
            <div className="label-text">{f.label}</div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 700, marginTop: 2 }}>{f.value}</div>
          </div>
        ))}
      </div>

      {/* Strike / Exit */}
      <div style={{ marginBottom: 10, display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", gap: 8, fontSize: 12 }}>
          <span style={{ color: "var(--text-muted)", minWidth: 70 }}>Strike:</span>
          <span style={{ color: "var(--amber-light)", fontWeight: 500 }}>{ts.strike_level}</span>
        </div>
        <div style={{ display: "flex", gap: 8, fontSize: 12 }}>
          <span style={{ color: "var(--text-muted)", minWidth: 70 }}>Exit:</span>
          <span style={{ color: "var(--red-light)", fontWeight: 500 }}>{ts.exit_level}</span>
        </div>
      </div>

      {/* Payout reference grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, marginBottom: 10 }}>
        {[
          { label: "At 43%",  value: fmtRupee(ts.payout_at_43_pct) },
          { label: "At 60%",  value: fmtRupee(ts.payout_at_60_pct) },
          { label: "At 80%",  value: fmtRupee(ts.payout_at_80_pct) },
          { label: "At 100%", value: fmtRupee(ts.payout_at_100_pct) },
        ].map(p => (
          <div key={p.label} style={{
            textAlign: "center", padding: "6px 4px",
            borderRadius: 4, background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}>
            <div className="label-text" style={{ fontSize: 10 }}>{p.label}</div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 13, fontWeight: 700, marginTop: 2 }}>{p.value}</div>
          </div>
        ))}
      </div>

      {/* Current assessment */}
      <div style={{
        display: "flex", gap: 12, alignItems: "center",
        padding: "10px 12px",
        background: breached ? "var(--red-glow)" : "var(--green-glow)",
        border: `1px solid ${breached ? "var(--red)" : "var(--green)"}`,
        borderRadius: 6,
      }}>
        <div>
          <span className="label-text">Current Loss: </span>
          <span style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700, color: breached ? "var(--red-light)" : "var(--green-light)" }}>
            {result.final_loss_pct}%
          </span>
        </div>
        <div>
          <span className="label-text">Payout: </span>
          <span style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700, color: "var(--amber-light)" }}>
            {fmtRupee(ts.current_estimated_payout_per_ha)}
          </span>
        </div>
        <span className={`badge ${breached ? "badge-red" : "badge-green"}`} style={{ marginLeft: "auto" }}>
          {breached ? "⚠ THRESHOLD BREACHED" : "✓ BELOW THRESHOLD"}
        </span>
      </div>
    </div>
  );
}

function BacktestPanel({ backtestResult }) {
  if (!backtestResult) return <Skeleton h={340} />;

  const meets = backtestResult.meets_target;
  const corr  = backtestResult.overall_correlation;
  const events = backtestResult.events ?? [];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 6, padding: "8px 12px", fontSize: 12 }}>
        {payload.map(p => (
          <div key={p.name} style={{ color: p.fill }}>
            {p.name}: <b>{fmtRupee(p.value)}</b>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Correlation score */}
      <div style={{ textAlign: "center", padding: "16px 0 8px" }}>
        <div style={{
          fontFamily: "var(--font-display)", fontSize: 52, fontWeight: 800, lineHeight: 1,
          color: meets ? "var(--green-light)" : "var(--red-light)",
        }}>
          {corr?.toFixed(3) ?? "—"}
        </div>
        <div style={{ marginTop: 8 }}>
          <span className={`badge ${meets ? "badge-green" : "badge-red"}`} style={{ fontSize: 12 }}>
            {meets ? "✓ Meets ≥75% Accuracy Target" : "✗ Below Target"}
          </span>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8, lineHeight: 1.6 }}>
          <div>Method: {backtestResult.correlation_method}</div>
          <div style={{ marginTop: 2, opacity: 0.7 }}>Source: {backtestResult.data_source}</div>
        </div>
      </div>

      {/* Events bar chart */}
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={events} barGap={2} margin={{ top: 4, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis dataKey="year" tick={{ fill: "var(--text-muted)", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
          <YAxis tickFormatter={v => "₹" + (v/1000).toFixed(0) + "k"} tick={{ fill: "var(--text-muted)", fontSize: 10 }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, color: "var(--text-secondary)" }} />
          <Bar dataKey="model_predicted_payout_per_ha" name="Model Predicted" fill="#3B82F6" radius={[2,2,0,0]} />
          <Bar dataKey="actual_govt_payout_per_ha"     name="Actual PMFBY"    fill="#16A34A" radius={[2,2,0,0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Events table */}
      <table className="data-table">
        <thead>
          <tr>
            <th>Year</th>
            <th>Event</th>
            <th>Variance</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => {
            const isGood = ["WITHIN_RANGE","CORRECT_NO_TRIGGER"].includes(e.model_assessment);
            return (
              <tr key={e.event_id}>
                <td>{e.year}</td>
                <td style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {(e.description ?? "").slice(0, 30)}{(e.description ?? "").length > 30 ? "…" : ""}
                </td>
                <td>{e.variance_pct?.toFixed(1)}%</td>
                <td>
                  <span className={`badge ${isGood ? "badge-green" : "badge-amber"}`} style={{ fontSize: 10 }}>
                    {e.model_assessment?.replace(/_/g," ")}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PremiumTable({ table }) {
  if (!table?.length) return <Skeleton h={160} />;

  const crops  = [...new Set(table.map(r => r.crop))];
  const perils = [...new Set(table.map(r => r.peril))];

  const riskBg = (level) => {
    if (level === "HIGH")   return "rgba(220,38,38,0.15)";
    if (level === "MEDIUM") return "rgba(245,158,11,0.15)";
    return "rgba(22,163,74,0.15)";
  };
  const riskColor = (level) => {
    if (level === "HIGH")   return "var(--red-light)";
    if (level === "MEDIUM") return "var(--amber-light)";
    return "var(--green-light)";
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ background: "var(--bg-elevated)", width: 90 }}>Crop</th>
            {perils.map(p => (
              <th key={p} style={{ background: "var(--bg-elevated)", textAlign: "center", color: perilColor(p) }}>
                {p}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {crops.map(crop => (
            <tr key={crop}>
              <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{crop}</td>
              {perils.map(peril => {
                const cell = table.find(r => r.crop === crop && r.peril === peril);
                return (
                  <td key={peril} style={{
                    textAlign: "center",
                    background: cell ? riskBg(cell.risk_level) : "transparent",
                    color: cell ? riskColor(cell.risk_level) : "var(--text-muted)",
                    fontWeight: 700, fontSize: 13,
                  }}>
                    {cell ? cell.premium_rate_pct.toFixed(1) + "%" : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Roadmap Modal ─────────────────────────────────────────────────

const PHASES = [
  {
    phase: "Phase 1",
    when: "NOW",
    title: "Kurnool Pilot",
    timeline: "Kharif 2026",
    details: "27 mandals, 5 crops, 2 lakh farmers",
    integrations: "PMFBY Portal, APSDMA",
    badge: { cls: "badge-green", text: "ACTIVE" },
  },
  {
    phase: "Phase 2",
    when: "3 MONTHS",
    title: "Rayalaseema Expansion",
    timeline: "Rabi 2026-27",
    details: "4 districts, 15 lakh farmers, ₹180 Cr premium pool",
    integrations: "e-Crop AP, Mee-Seva",
    badge: { cls: "badge-amber", text: "PLANNED" },
  },
  {
    phase: "Phase 3",
    when: "12 MONTHS",
    title: "All 26 AP Districts",
    timeline: "Kharif 2027",
    details: "26 districts, 1.2 Cr farmers, estimated ₹2,400 Cr savings in manual survey costs",
    integrations: "PMFBY, APSDMA, Revenue Dept, AP Fibernet",
    badge: { cls: "badge-blue", text: "ROADMAP" },
  },
];

function RoadmapModal({ onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 1000,
        background: "rgba(0,0,0,0.8)",
        display: "flex", alignItems: "center", justifyContent: "center",
        animation: "fade-in 0.2s ease",
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-bright)",
          borderRadius: 12, padding: 32,
          maxWidth: 600, width: "90%",
          maxHeight: "85vh", overflowY: "auto",
          position: "relative",
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute", top: 16, right: 16,
            background: "transparent", border: "1px solid var(--border)",
            borderRadius: 4, color: "var(--text-muted)",
            width: 28, height: 28, cursor: "pointer", fontSize: 16,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >×</button>

        {/* Title */}
        <div style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>
          AP-CropGuard — Statewide Rollout Plan
        </div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 24 }}>
          Government of Andhra Pradesh · Agriculture Department · Digital Agriculture Mission
        </div>

        {/* Phase cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {PHASES.map((p) => (
            <div key={p.phase} style={{
              background: "var(--bg-elevated)", border: "1px solid var(--border)",
              borderRadius: 8, padding: "16px 20px",
              borderLeft: `3px solid ${
                p.badge.text === "ACTIVE"  ? "var(--green)" :
                p.badge.text === "PLANNED" ? "var(--amber)" : "var(--blue)"
              }`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                      {p.phase} · {p.when}
                    </span>
                    <span className={`badge ${p.badge.cls}`}>{p.badge.text}</span>
                  </div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700 }}>{p.title}</div>
                </div>
                <div style={{
                  fontSize: 12, color: "var(--amber-light)", fontWeight: 600,
                  background: "var(--amber-dim)", padding: "3px 10px", borderRadius: 4,
                  whiteSpace: "nowrap",
                }}>
                  {p.timeline}
                </div>
              </div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8 }}>{p.details}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Integrations: </span>
                {p.integrations}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 20, padding: "12px 16px", background: "var(--green-glow)", border: "1px solid var(--green)", borderRadius: 6, fontSize: 12, color: "var(--green-light)" }}>
          ◎ Estimated state-level impact: <b>₹2,400 Cr</b> annual savings · <b>72-hour</b> relief turnaround · <b>1.2 Cr</b> farmers protected
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────

export default function Screen2_Insurance({ season, selectedMandal }) {
  const [crops,            setCrops]            = useState([]);
  const [perils,           setPerils]           = useState([]);
  const [mandals,          setMandals]          = useState([]);
  const [threshold,        setThreshold]        = useState(null);
  const [selectedCrop,     setSelectedCrop]     = useState(null);
  const [selectedPeril,    setSelectedPeril]    = useState(null);
  const [selectedMandalId, setSelectedMandalId] = useState(selectedMandal);
  const [sowingDate,       setSowingDate]       = useState("");
  const [disasterDate,     setDisasterDate]     = useState(season === "Kharif_2023" ? "2023-09-12" : "2020-09-15");
  const [rainfallDeficit,  setRainfallDeficit]  = useState(50);
  const [cddValue,         setCddValue]         = useState(15);
  const [maxTemp,          setMaxTemp]          = useState(40);
  const [simulateResult,   setSimulateResult]   = useState(null);
  const [simLoading,       setSimLoading]       = useState(false);
  const [calculateResult,  setCalculateResult]  = useState(null);
  const [calcLoading,      setCalcLoading]      = useState(false);
  const [backtestResult,   setBacktestResult]   = useState(null);
  const [premiumTable,     setPremiumTable]     = useState([]);
  const [showRoadmap,      setShowRoadmap]      = useState(false);

  const debounceRef = useRef(null);

  // ── Sync selectedMandalId when parent prop changes (mandal clicked on Screen1) ──
  useEffect(() => { setSelectedMandalId(selectedMandal); }, [selectedMandal]);

  // ── Mount: load meta, backtest, premium ──────────────────────
  useEffect(() => {
    Promise.all([getMetaCrops(), getMetaMandals(), getBacktestResults(), getPremiumTable()])
      .then(([cropsRes, mandalsRes, btRes, ptRes]) => {
        if (!cropsRes.error) {
          const cropList  = cropsRes.data?.data?.crops  ?? [];
          const perilList = cropsRes.data?.data?.perils ?? [];
          const thr       = cropsRes.data?.data?.threshold_loss_pct ?? 43;
          setCrops(cropList);
          setPerils(perilList);
          setThreshold(thr);
          if (cropList.length) {
            setSelectedCrop(cropList[0]);
            setSowingDate("2023-07-01"); // sensible default; updated on crop select
          }
          if (perilList.length) setSelectedPeril(perilList[0]);
        }
        if (!mandalsRes.error) {
          setMandals(mandalsRes.data?.data?.mandals ?? []);
        }
        if (!btRes.error) setBacktestResult(btRes.data?.data ?? null);
        if (!ptRes.error) setPremiumTable(ptRes.data?.data?.table ?? []);
      });
  }, []);

  // Update disaster date when season changes
  useEffect(() => {
    setDisasterDate(season === "Kharif_2023" ? "2023-09-12" : "2020-09-15");
  }, [season]);

  // ── Debounced simulate ────────────────────────────────────────
  useEffect(() => {
    if (!selectedCrop || !selectedPeril || !selectedMandalId || !sowingDate || !disasterDate) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setSimLoading(true);
      const res = await postParametricSimulate({
        crop:                 selectedCrop.name ?? selectedCrop,
        peril:                selectedPeril,
        mandal_id:            selectedMandalId,
        sowing_date:          sowingDate,
        disaster_date:        disasterDate,
        rainfall_deficit_pct: rainfallDeficit,
        consecutive_dry_days: cddValue,
        max_temp_celsius:     maxTemp,
      });
      if (!res.error) setSimulateResult(res.data?.data ?? null);
      setSimLoading(false);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [selectedCrop, selectedPeril, selectedMandalId, sowingDate, disasterDate, rainfallDeficit, cddValue, maxTemp]);

  // ── Calculate ─────────────────────────────────────────────────
  const handleCalculate = async () => {
    if (!selectedCrop || !selectedPeril) return;
    setCalcLoading(true);
    const res = await postParametricCalculate({
      crop:          selectedCrop.name ?? selectedCrop,
      peril:         selectedPeril,
      mandal_id:     selectedMandalId,
      season,
      sowing_date:   sowingDate,
      disaster_date: disasterDate,
      weather_inputs: {
        rainfall_deficit_pct: rainfallDeficit,
        consecutive_dry_days: cddValue,
        max_temp_celsius:     maxTemp,
        spi_value:            simulateResult?.spi_computed ?? null,
      },
    });
    if (!res.error) setCalculateResult(res.data?.data ?? null);
    setCalcLoading(false);
  };

  const selectedMandalName = mandals.find(m => m.mandal_id === selectedMandalId)?.mandal_name ?? selectedMandalId;

  const sliders = [
    { label: "Rainfall Deficit", value: rainfallDeficit, min: 0,  max: 100, unit: "%",  set: setRainfallDeficit },
    { label: "Consecutive Dry Days", value: cddValue,    min: 0,  max: 45,  unit: "d",  set: setCddValue },
    { label: "Max Temperature",  value: maxTemp,         min: 35, max: 50,  unit: "°C", set: setMaxTemp },
  ];

  return (
    <div className="two-col-grid" style={{ height: "calc(100vh - 88px)" }}>

      {/* ══ LEFT COLUMN ════════════════════════════════════════════ */}
      <div className="col-scroll">

        {/* Scenario Controls */}
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="section-title">Scenario Controls</div>

          {/* Crop buttons */}
          <div>
            <div className="label-text" style={{ marginBottom: 6 }}>Crop</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {crops.length === 0
                ? <Skeleton h={32} style={{ width: "100%" }} />
                : crops.map(c => (
                  <button
                    key={c.name}
                    className="btn"
                    onClick={() => { setSelectedCrop(c); setSowingDate(c.kharif_sowing_start ? `2023-${c.kharif_sowing_start}` : sowingDate); }}
                    style={{
                      background: selectedCrop?.name === c.name ? "var(--green)" : "var(--bg-elevated)",
                      color: selectedCrop?.name === c.name ? "#fff" : "var(--text-muted)",
                      border: `1px solid ${selectedCrop?.name === c.name ? "var(--green)" : "var(--border)"}`,
                      fontSize: 12, padding: "6px 12px",
                    }}
                  >
                    {c.name}
                  </button>
                ))}
            </div>
          </div>

          {/* Peril buttons */}
          <div>
            <div className="label-text" style={{ marginBottom: 6 }}>Peril</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {perils.length === 0
                ? <Skeleton h={32} style={{ width: "100%" }} />
                : perils.map(p => {
                  const pc = perilColor(p);
                  const isActive = selectedPeril === p;
                  return (
                    <button
                      key={p}
                      className="btn"
                      onClick={() => setSelectedPeril(p)}
                      style={{
                        background: isActive ? pc : "var(--bg-elevated)",
                        color: isActive ? "#fff" : "var(--text-muted)",
                        border: `1px solid ${isActive ? pc : "var(--border)"}`,
                        fontSize: 12, padding: "6px 12px",
                      }}
                    >
                      {p}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Dates + Mandal */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div>
              <div className="label-text" style={{ marginBottom: 4 }}>Sowing Date</div>
              <input type="date" value={sowingDate} onChange={e => setSowingDate(e.target.value)} />
            </div>
            <div>
              <div className="label-text" style={{ marginBottom: 4 }}>Disaster Date</div>
              <input type="date" value={disasterDate} onChange={e => setDisasterDate(e.target.value)} />
            </div>
          </div>

          <div>
            <div className="label-text" style={{ marginBottom: 4 }}>Mandal</div>
            {mandals.length === 0
              ? <Skeleton h={34} />
              : (
                <select value={selectedMandalId} onChange={e => setSelectedMandalId(e.target.value)}>
                  {mandals.map(m => (
                    <option key={m.mandal_id} value={m.mandal_id}>{m.mandal_name}</option>
                  ))}
                </select>
              )}
          </div>

          {/* Sliders */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 4 }}>
            {sliders.map(s => (
              <div key={s.label}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span className="label-text">{s.label}</span>
                  <span style={{ fontFamily: "var(--font-display)", fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>
                    {s.value}{s.unit}
                  </span>
                </div>
                <input
                  type="range"
                  min={s.min} max={s.max}
                  value={s.value}
                  onChange={e => s.set(Number(e.target.value))}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                  <span>{s.min}{s.unit}</span><span>{s.max}{s.unit}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Live metrics bar */}
          <div>
            <div className="label-text" style={{ marginBottom: 6 }}>Live Model Output</div>
            <LiveMetrics sim={simulateResult} threshold={threshold} loading={simLoading} />
          </div>
        </div>

        {/* Payout Curve */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: 10 }}>Parametric Payout Curve</div>
          <PayoutCurveChart
            data={calculateResult?.payout_curve ?? null}
            threshold={threshold}
          />
        </div>

        {/* Calculate button */}
        <button
          className="btn btn-primary"
          style={{ width: "100%", padding: "13px", fontSize: 14, fontWeight: 700 }}
          onClick={handleCalculate}
          disabled={calcLoading}
        >
          {calcLoading ? "⟳ Calculating…" : "Generate Full Assessment & Term Sheet"}
        </button>

        {/* Term sheet */}
        <TermSheet result={calculateResult} mandalName={selectedMandalName} />
      </div>

      {/* ══ RIGHT COLUMN ═══════════════════════════════════════════ */}
      <div className="col-scroll">

        {/* Backtest panel */}
        <div className="card">
          <div style={{ marginBottom: 12 }}>
            <div className="section-title" style={{ marginBottom: 2 }}>
              Model Validation — Historical Back-Test
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Kurnool District · 2018–2023 · 4 Events
            </div>
          </div>
          <BacktestPanel backtestResult={backtestResult} />
        </div>

        {/* Premium table */}
        <div className="card">
          <div style={{ marginBottom: 10 }}>
            <div className="section-title" style={{ marginBottom: 2 }}>
              Kharif 2026 Premium Schedule
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Kurnool District — All Crops · Rate (% of Sum Insured)
            </div>
          </div>
          <PremiumTable table={premiumTable} />
          <div style={{ marginTop: 8, fontSize: 10, color: "var(--text-muted)", fontStyle: "italic" }}>
            GoI PMFBY actuarial guidelines · Commercial loading: 15% expense + 10% risk margin
          </div>
        </div>

        {/* Scale-Up Roadmap button */}
        <button
          className="btn btn-ghost"
          style={{ width: "100%", padding: "12px", fontSize: 13, fontWeight: 600 }}
          onClick={() => setShowRoadmap(true)}
        >
          View AP State Scale-Up Roadmap →
        </button>

      </div>

      {/* Roadmap modal */}
      {showRoadmap && <RoadmapModal onClose={() => setShowRoadmap(false)} />}
    </div>
  );
}

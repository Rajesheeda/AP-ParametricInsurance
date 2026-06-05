import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";
import {
  postPhotoAssess, postPhotoFeedback,
  getWeightHistory, getEvidenceLog,
  getMetaMandals, getMetaCrops,
} from "../utils/api";

// ── Helpers ──────────────────────────────────────────────────────

const statusBadge = (status) => {
  if (!status) return null;
  const map = {
    PASS:    { cls: "badge-green",  icon: "✓" },
    CLEAN:   { cls: "badge-green",  icon: "✓" },
    WARNING: { cls: "badge-amber",  icon: "⚠" },
    FAIL:    { cls: "badge-red",    icon: "✗" },
    FLAGGED: { cls: "badge-red",    icon: "⛔" },
  };
  const s = map[status] ?? { cls: "badge-muted", icon: "?" };
  return <span className={`badge ${s.cls}`}>{s.icon} {status}</span>;
};

const damageBg = (dc) => {
  if (!dc) return "var(--bg-elevated)";
  if (dc.includes("Healthy"))   return "var(--green-dim)";
  if (dc.includes("Partially")) return "var(--amber-dim)";
  return "var(--red-dim)";
};
const damageColor = (dc) => {
  if (!dc) return "var(--text-muted)";
  if (dc.includes("Healthy"))   return "var(--green-light)";
  if (dc.includes("Partially")) return "var(--amber-light)";
  return "var(--red-light)";
};
const severityClass = (s) => {
  if (s === "HIGH")   return "badge-red";
  if (s === "MEDIUM") return "badge-amber";
  return "badge-green";
};
const sourceColor = (src) => {
  if (!src) return "badge-muted";
  if (src.includes("Gemini")) return "badge-green";
  if (src.includes("Groq"))   return "badge-blue";
  return "badge-amber";
};
const overallStatusDisplay = (s) => {
  const map = {
    CLEAN:   { cls: "badge-green", text: "✓ CLEAN" },
    WARNING: { cls: "badge-amber", text: "⚠ WARNING" },
    FAIL:    { cls: "badge-red",   text: "✗ FAILED" },
    FLAGGED: { cls: "badge-red",   text: "⛔ FLAGGED" },
  };
  return map[s] ?? { cls: "badge-muted", text: s };
};

function Skeleton({ h = 40, style }) {
  return <div className="skeleton" style={{ height: h, borderRadius: 6, ...style }} />;
}

// ── Toast ─────────────────────────────────────────────────────────

function Toast({ message, visible }) {
  if (!visible) return null;
  return (
    <div style={{
      position: "fixed", bottom: 24, right: 24,
      background: "var(--green-dim)", border: "1px solid var(--green)",
      color: "var(--green-light)", padding: "10px 18px",
      borderRadius: 8, fontSize: 13, fontWeight: 600,
      zIndex: 9999, animation: "fade-in 0.2s ease",
    }}>
      {message}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────

export default function Screen3_Photo({ season, selectedMandal }) {
  const [mandals,             setMandals]             = useState([]);
  const [crops,               setCrops]               = useState([]);
  const [threshold,           setThreshold]           = useState(null);
  const [selectedMandalId,    setSelectedMandalId]    = useState(selectedMandal);
  const [selectedCrop,        setSelectedCrop]        = useState(null);
  const [claimedDisasterDate, setClaimedDisasterDate] = useState(
    season === "Kharif_2023" ? "2023-09-12" : "2020-09-15"
  );
  const [imageFile,           setImageFile]           = useState(null);
  const [imagePreviewUrl,     setImagePreviewUrl]     = useState(null);
  const [assessing,           setAssessing]           = useState(false);
  const [assessResult,        setAssessResult]        = useState(null);
  const [fraudResult,         setFraudResult]         = useState(null);
  const [consensusResult,     setConsensusResult]     = useState(null);
  const [weightHistory,       setWeightHistory]       = useState(null);
  const [evidenceLog,         setEvidenceLog]         = useState([]);
  const [feedbackSubmitting,  setFeedbackSubmitting]  = useState(false);
  const [activeAssessmentId,  setActiveAssessmentId]  = useState(null);
  const [toastVisible,        setToastVisible]        = useState(false);
  const [toastMsg,            setToastMsg]            = useState("");
  const fileInputRef = useRef(null);
  const toastTimer   = useRef(null);

  // Define callbacks before any useEffect that uses them
  const showToast = (msg) => {
    setToastMsg(msg);
    setToastVisible(true);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToastVisible(false), 2000);
  };

  const reloadMandal = useCallback(async (mandalId) => {
    const [whRes, elRes] = await Promise.all([
      getWeightHistory(mandalId),
      getEvidenceLog(mandalId, season),
    ]);
    if (!whRes.error) setWeightHistory(whRes.data?.data ?? null);
    if (!elRes.error) setEvidenceLog(elRes.data?.data?.evidence ?? []);
  }, [season]);

  // ── Mount: load meta + initial mandal data ───────────────────
  useEffect(() => {
    Promise.all([getMetaMandals(), getMetaCrops()]).then(([mRes, cRes]) => {
      if (!mRes.error) setMandals(mRes.data?.data?.mandals ?? []);
      if (!cRes.error) {
        const cropList = cRes.data?.data?.crops ?? [];
        setCrops(cropList);
        setThreshold(cRes.data?.data?.threshold_loss_pct ?? 43);
        if (cropList.length) setSelectedCrop(cropList[0].name);
      }
    });
    reloadMandal(selectedMandal);
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── Sync selectedMandalId when parent prop changes ───────────
  useEffect(() => {
    setSelectedMandalId(selectedMandal);
    reloadMandal(selectedMandal);
  }, [selectedMandal, reloadMandal]);

  // Season changes update disaster date
  useEffect(() => {
    setClaimedDisasterDate(season === "Kharif_2023" ? "2023-09-12" : "2020-09-15");
  }, [season]);

  const handleMandalChange = (id) => {
    setSelectedMandalId(id);
    reloadMandal(id);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    setAssessResult(null);
    setFraudResult(null);
    setConsensusResult(null);
    setActiveAssessmentId(null);
  };

  const handleAssess = async () => {
    if (!imageFile) return;
    setAssessing(true);
    const form = new FormData();
    form.append("image", imageFile);
    form.append("claimed_mandal_id", selectedMandalId);
    form.append("claimed_crop", selectedCrop ?? "");
    form.append("claimed_disaster_date", claimedDisasterDate);

    const res = await postPhotoAssess(form);
    if (!res.error && res.data?.data) {
      const d = res.data.data;
      setAssessResult(d.assessment ?? null);
      setFraudResult(d.fraud_check ?? null);
      setConsensusResult(d.consensus ?? null);
      setActiveAssessmentId(d.assessment_id ?? null);
      await reloadMandal(selectedMandalId);
    }
    setAssessing(false);
  };

  const handleFeedback = async (feedbackType) => {
    if (!activeAssessmentId) return;
    setFeedbackSubmitting(true);
    const res = await postPhotoFeedback({
      mandal_id:     selectedMandalId,
      assessment_id: activeAssessmentId,
      feedback_type: feedbackType,
      vro_id:        "VRO_DEMO_001",
      note:          "Field verification feedback",
    });
    if (!res.error) {
      await reloadMandal(selectedMandalId);
      showToast("Feedback recorded ✓");
    }
    setFeedbackSubmitting(false);
  };

  const thr = threshold ?? 43;
  const wh  = weightHistory?.weight_history ?? [];
  const noFeedbackYet = wh.length <= 1;

  const fbButtons = [
    { type: "AGREE_SATELLITE",    label: "✓ Agree — Satellite",  agree: true  },
    { type: "DISPUTE_SATELLITE",  label: "✗ Dispute — Satellite", agree: false },
    { type: "AGREE_PHOTO",        label: "✓ Agree — Photo",       agree: true  },
    { type: "DISPUTE_PHOTO",      label: "✗ Dispute — Photo",     agree: false },
  ];

  // ── Render ────────────────────────────────────────────────────
  return (
    <>
      <Toast message={toastMsg} visible={toastVisible} />

      <div className="two-col-equal" style={{ height: "calc(100vh - 88px)" }}>

        {/* ══ PANEL A — LEFT ════════════════════════════════════════ */}
        <div className="col-scroll">
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="section-title">Crop Photo Assessment</div>

            {/* Mandal + Crop selectors */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <div className="label-text" style={{ marginBottom: 4 }}>Mandal</div>
                {!mandals.length ? <Skeleton h={34} /> : (
                  <select value={selectedMandalId} onChange={e => handleMandalChange(e.target.value)}>
                    {mandals.map(m => (
                      <option key={m.mandal_id} value={m.mandal_id}>{m.mandal_name}</option>
                    ))}
                  </select>
                )}
              </div>
              <div>
                <div className="label-text" style={{ marginBottom: 4 }}>Crop</div>
                {!crops.length ? <Skeleton h={34} /> : (
                  <select value={selectedCrop ?? ""} onChange={e => setSelectedCrop(e.target.value)}>
                    {crops.map(c => (
                      <option key={c.name} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Upload zone */}
            <div>
              <div className="label-text" style={{ marginBottom: 6 }}>Crop Photograph</div>
              <div
                className="upload-zone"
                onClick={() => !imageFile && fileInputRef.current?.click()}
                style={{ padding: imageFile ? "12px" : "32px 20px" }}
              >
                {!imageFile ? (
                  <>
                    <div style={{ fontSize: 48, lineHeight: 1, color: "var(--text-muted)", marginBottom: 10 }}>⊡</div>
                    <div style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 4 }}>
                      Drop crop photograph here
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      JPG or PNG — geotagged preferred
                    </div>
                  </>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <img
                      src={imagePreviewUrl}
                      alt="preview"
                      style={{ width: "100%", maxHeight: 200, objectFit: "cover", borderRadius: 8 }}
                    />
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {imageFile.name}
                      </span>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: 11, padding: "4px 10px" }}
                        onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
                      >
                        Change Photo
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />
            </div>

            {/* Disaster date */}
            <div>
              <div className="label-text" style={{ marginBottom: 4 }}>Disaster Date</div>
              <input
                type="date"
                value={claimedDisasterDate}
                onChange={e => setClaimedDisasterDate(e.target.value)}
              />
            </div>

            {/* Assess button */}
            <button
              className="btn btn-primary"
              style={{ width: "100%", padding: "12px", fontSize: 14, fontWeight: 700, opacity: imageFile ? 1 : 0.5 }}
              disabled={!imageFile || assessing}
              onClick={handleAssess}
            >
              {assessing ? "⟳ Analyzing with Gemini Vision…" : "Analyze Photo & Run Verification"}
            </button>

            {/* Assessment result */}
            {assessResult && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="divider" />

                {/* Damage class */}
                <div style={{ textAlign: "center" }}>
                  <span style={{
                    fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700,
                    background: damageBg(assessResult.damage_class),
                    color: damageColor(assessResult.damage_class),
                    padding: "8px 20px", borderRadius: 6, display: "inline-block",
                  }}>
                    {assessResult.damage_class}
                  </span>
                </div>

                {/* Metrics row */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <div style={{ textAlign: "center", background: "var(--bg-elevated)", padding: "10px", borderRadius: 6 }}>
                    <div className="label-text">Confidence</div>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 700, color: "var(--green-light)" }}>
                      {((assessResult.confidence_score ?? 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div style={{ textAlign: "center", background: "var(--bg-elevated)", padding: "10px", borderRadius: 6 }}>
                    <div className="label-text">Photo Loss Est.</div>
                    <div style={{
                      fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 700,
                      color: (assessResult.estimated_photo_loss_pct ?? 0) >= thr ? "var(--red-light)" : "var(--amber-light)",
                    }}>
                      {assessResult.estimated_photo_loss_pct}%
                    </div>
                  </div>
                </div>

                {/* Source badge */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className="label-text">Source:</span>
                  <span className={`badge ${sourceColor(assessResult.analysis_source)}`}>
                    {assessResult.analysis_source}
                  </span>
                </div>

                {/* Disease details */}
                {assessResult.disease_pest_detected ? (
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--amber-light)", marginBottom: 8 }}>
                      ⚠ Pest/Disease Detected
                    </div>
                    {(assessResult.disease_details ?? []).map((d, i) => (
                      <div key={i} style={{
                        borderLeft: "3px solid var(--amber)", paddingLeft: 10,
                        marginBottom: 8, background: "var(--bg-elevated)", padding: "8px 10px",
                        borderRadius: "0 6px 6px 0",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <span style={{ fontWeight: 600, fontSize: 13 }}>{d.name}</span>
                          <span className={`badge ${severityClass(d.severity)}`}>{d.severity}</span>
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
                          Confidence: {((d.confidence ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-secondary)", fontStyle: "italic" }}>
                          {d.agronomic_advice}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: "var(--green-light)" }}>
                    ✓ No pest or disease detected
                  </div>
                )}

                {/* Fraud checks */}
                {fraudResult && (
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <div className="section-title" style={{ margin: 0 }}>Photo Verification Checks</div>
                      {(() => {
                        const d = overallStatusDisplay(fraudResult.overall_status);
                        return <span className={`badge ${d.cls}`}>{d.text}</span>;
                      })()}
                    </div>
                    {[
                      {
                        icon: "◎", label: "GPS Geofence",
                        status: fraudResult.geofence_check?.status,
                        note: fraudResult.geofence_check?.status === "WARNING"
                          ? fraudResult.geofence_check?.gps_missing_note : null,
                      },
                      {
                        icon: "⏱", label: "Timestamp",
                        status: fraudResult.temporal_check?.status,
                        note: null,
                      },
                      {
                        icon: "✏", label: "Edit Signature",
                        status: fraudResult.edit_signature_check?.status,
                        note: fraudResult.edit_signature_check?.status === "FLAGGED"
                          ? `Editor: ${fraudResult.edit_signature_check?.editor_detected}` : null,
                      },
                    ].map(row => (
                      <div key={row.label} style={{
                        display: "flex", alignItems: "flex-start", gap: 10,
                        padding: "8px 0", borderBottom: "1px solid var(--border-subtle)",
                      }}>
                        <span style={{ fontSize: 16, width: 20, textAlign: "center", marginTop: 1 }}>{row.icon}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: 13 }}>{row.label}</span>
                            {statusBadge(row.status)}
                          </div>
                          {row.note && (
                            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 3 }}>{row.note}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Consensus threshold banner */}
                {consensusResult && (
                  <div className={`alert-banner ${consensusResult.threshold_breached ? "critical" : "success"}`}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 13 }}>
                        {consensusResult.threshold_breached
                          ? "⚠ COMPENSATION THRESHOLD MET"
                          : "✓ Below Compensation Threshold"}
                      </div>
                      <div style={{ fontSize: 11, marginTop: 2, opacity: 0.85 }}>
                        Consensus Loss: {consensusResult.final_loss_pct}%
                        {consensusResult.threshold_breached ? " — Relief Eligible" : ""}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ══ PANEL B — RIGHT ═══════════════════════════════════════ */}
        <div className="col-scroll">
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Bayesian consensus header */}
            <div>
              <div className="section-title" style={{ marginBottom: 2 }}>
                Satellite-Photo Consensus Engine
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                Bayesian Fusion — RLHF Adaptive Weights
              </div>
            </div>

            {/* Formula box */}
            <div style={{
              background: "var(--bg-elevated)", borderRadius: 6, padding: 12,
              textAlign: "center", fontFamily: "monospace", fontSize: 12,
              color: "var(--green)", border: "1px solid var(--border-bright)",
            }}>
              Final Loss % = W_sat × Satellite + W_photo × Photo
            </div>

            {/* Current weights */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                {
                  value: weightHistory?.current_weights?.w_satellite ?? "0.70",
                  label: "SATELLITE WEIGHT",
                  color: "#3B82F6",
                },
                {
                  value: weightHistory?.current_weights?.w_photo ?? "0.30",
                  label: "PHOTO WEIGHT",
                  color: "var(--green)",
                },
              ].map(w => (
                <div key={w.label} style={{
                  textAlign: "center", background: "var(--bg-elevated)",
                  padding: "12px 8px", borderRadius: 6,
                }}>
                  <div className="label-text">{w.label}</div>
                  <div style={{
                    fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 800,
                    color: w.color, lineHeight: 1, marginTop: 4,
                  }}>
                    {w.value}
                  </div>
                </div>
              ))}
            </div>

            {/* Consensus loss display */}
            {consensusResult && (
              <div style={{
                textAlign: "center", background: "var(--bg-elevated)",
                padding: "12px", borderRadius: 6,
                border: `1px solid ${consensusResult.threshold_breached ? "var(--red)" : "var(--green)"}`,
              }}>
                <div className="label-text">Consensus Loss</div>
                <div style={{
                  fontFamily: "var(--font-display)", fontSize: 40, fontWeight: 800, lineHeight: 1, marginTop: 4,
                  color: consensusResult.threshold_breached
                    ? "var(--red-light)"
                    : consensusResult.final_loss_pct > 20
                    ? "var(--amber-light)" : "var(--green-light)",
                }}>
                  {consensusResult.final_loss_pct}%
                </div>
              </div>
            )}

            <div className="divider" />

            {/* VRO Feedback */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <div className="section-title" style={{ margin: 0 }}>VRO Field Validation</div>
                {!activeAssessmentId && (
                  <span style={{ fontSize: 10, color: "var(--text-muted)", fontStyle: "italic" }}>
                    Assess a photo first
                  </span>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {fbButtons.map(fb => (
                  <button
                    key={fb.type}
                    onClick={() => handleFeedback(fb.type)}
                    disabled={!activeAssessmentId || feedbackSubmitting}
                    style={{
                      padding: "9px 8px",
                      borderRadius: 6,
                      border: `1px solid ${fb.agree ? "var(--green)" : "var(--red)"}`,
                      background: "transparent",
                      color: fb.agree ? "var(--green-light)" : "var(--red-light)",
                      cursor: activeAssessmentId ? "pointer" : "not-allowed",
                      opacity: activeAssessmentId ? 1 : 0.4,
                      fontSize: 12, fontWeight: 600,
                      transition: "all 0.15s",
                      fontFamily: "var(--font-body)",
                    }}
                    onMouseEnter={e => {
                      if (activeAssessmentId) {
                        e.currentTarget.style.background = fb.agree ? "var(--green)" : "var(--red)";
                        e.currentTarget.style.color = "#fff";
                      }
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "transparent";
                      e.currentTarget.style.color = fb.agree ? "var(--green-light)" : "var(--red-light)";
                    }}
                  >
                    {fb.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="divider" />

            {/* Weight history chart */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <div className="section-title" style={{ marginBottom: 2 }}>RLHF Weight Adaptation</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Per-mandal learning from VRO feedback
                </div>
              </div>

              {!wh.length ? <Skeleton h={200} /> : (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={wh} margin={{ top: 8, right: 8, left: -24, bottom: 16 }}>
                      <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis
                        dataKey="entry"
                        tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                        tickLine={false}
                        axisLine={{ stroke: "var(--border)" }}
                        label={{ value: "Feedback Entry", position: "insideBottom", offset: -10, fill: "var(--text-muted)", fontSize: 10 }}
                      />
                      <YAxis
                        domain={[0, 1]}
                        tickCount={5}
                        tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 6 }}
                        formatter={(v, name) => [v?.toFixed(4), name]}
                        labelFormatter={l => `Entry #${l}`}
                      />
                      <ReferenceLine y={0.70} stroke="rgba(59,130,246,0.3)" strokeDasharray="4 4"
                        label={{ value: "Prior W_sat", position: "right", fill: "rgba(59,130,246,0.5)", fontSize: 9 }} />
                      <ReferenceLine y={0.30} stroke="rgba(22,163,74,0.3)" strokeDasharray="4 4"
                        label={{ value: "Prior W_photo", position: "right", fill: "rgba(22,163,74,0.5)", fontSize: 9 }} />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
                      <Line type="monotone" dataKey="w_satellite" stroke="#3B82F6"
                        name="Satellite Weight" strokeWidth={2} dot={{ r: 4, fill: "#3B82F6" }} />
                      <Line type="monotone" dataKey="w_photo" stroke="var(--green)"
                        name="Photo Weight" strokeWidth={2} dot={{ r: 4, fill: "var(--green)" }} />
                    </LineChart>
                  </ResponsiveContainer>

                  {noFeedbackYet && (
                    <div style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", marginTop: 6 }}>
                      No VRO feedback recorded yet. Weights at system prior (0.70 / 0.30).
                      Submit feedback above to adapt weights.
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="divider" />

            {/* Evidence log */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <div className="section-title" style={{ marginBottom: 2 }}>Field Evidence Log</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {selectedMandalId} — {season}
                </div>
              </div>

              {evidenceLog.length === 0 ? (
                <div style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic", padding: "12px 0" }}>
                  No photo submissions yet for this mandal.
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="data-table" style={{ fontSize: 11 }}>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Crop</th>
                        <th>Damage</th>
                        <th>Loss</th>
                        <th>Fraud</th>
                        <th>VRO</th>
                        <th>Consensus</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evidenceLog.map((row, idx) => {
                        const isThreshold = (row.final_consensus_loss_pct ?? 0) >= thr;
                        const isOdd = idx % 2 !== 0;
                        const fraudInfo = overallStatusDisplay(row.fraud_status);
                        return (
                          <tr key={row.submission_id ?? idx} style={{
                            background: isThreshold
                              ? "rgba(220,38,38,0.08)"
                              : isOdd ? "var(--bg-elevated)" : "transparent",
                          }}>
                            <td style={{ fontFamily: "monospace", color: "var(--text-muted)" }}>
                              {(row.submission_id ?? "").slice(0, 12)}
                            </td>
                            <td>{row.crop}</td>
                            <td>
                              <span style={{
                                fontSize: 10, fontWeight: 700, padding: "1px 6px",
                                borderRadius: 4, background: damageBg(row.damage_class),
                                color: damageColor(row.damage_class),
                              }}>
                                {row.damage_class}
                              </span>
                            </td>
                            <td style={{ color: (row.photo_loss_pct ?? 0) >= thr ? "var(--red-light)" : "var(--text-secondary)", fontWeight: 700 }}>
                              {row.photo_loss_pct}%
                            </td>
                            <td><span className={`badge ${fraudInfo.cls}`} style={{ fontSize: 9 }}>{fraudInfo.text}</span></td>
                            <td style={{ color: "var(--text-muted)", fontSize: 10 }}>
                              {row.vro_feedback ?? "Pending"}
                            </td>
                            <td style={{
                              fontWeight: 700,
                              color: isThreshold ? "var(--red-light)" : "var(--text-primary)",
                            }}>
                              {row.final_consensus_loss_pct}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

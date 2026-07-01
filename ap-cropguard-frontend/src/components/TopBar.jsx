import React, { useState, useEffect } from "react";
import { SEASON_LABELS } from "../utils/constants";

const SCREEN_TITLES = {
  overview:  "District Overview — Kurnool",
  insurance: "Parametric Insurance Engine",
  photo:     "Photo Validation & Evidence",
};

function LiveClock() {
  const [time, setTime] = useState(() => {
    const d = new Date();
    return d.toLocaleTimeString("en-IN", { hour12: false, timeZone: "Asia/Kolkata" });
  });

  useEffect(() => {
    const id = setInterval(() => {
      const d = new Date();
      setTime(d.toLocaleTimeString("en-IN", { hour12: false, timeZone: "Asia/Kolkata" }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span style={{
      fontFamily: "var(--font-display)",
      fontSize: 13,
      color: "var(--text-muted)",
      letterSpacing: "0.05em",
    }}>
      {time} IST
    </span>
  );
}

export default function TopBar({ activeScreen, season, onSeasonChange }) {
  const title = SCREEN_TITLES[activeScreen] ?? "AP Parametric Insurance";

  return (
    <header className="topbar" style={{ justifyContent: "space-between" }}>

      {/* ── Left: Screen title ──────────────────────── */}
      <div style={{
        fontFamily: "var(--font-display)",
        fontSize: 16,
        fontWeight: 700,
        color: "var(--text-primary)",
        whiteSpace: "nowrap",
        minWidth: 220,
      }}>
        {title}
      </div>

      {/* ── Center: Season toggle ────────────────────── */}
      <div className="season-toggle">
        {["Kharif_2020", "Kharif_2023"].map((s) => (
          <button
            key={s}
            className={`season-toggle__btn${season === s ? " active" : ""}`}
            onClick={() => onSeasonChange(s)}
          >
            {SEASON_LABELS[s]}
          </button>
        ))}
      </div>

      {/* ── Right: Badges + clock ────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>

        {/* 72hr badge */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          padding: "4px 12px",
          background: "var(--amber-dim)",
          border: "1px solid var(--amber)",
          borderRadius: "var(--radius-sm)",
          fontSize: 11,
          fontWeight: 600,
          color: "var(--amber-light)",
          letterSpacing: "0.04em",
          whiteSpace: "nowrap",
        }}>
          ⏱ Assessment Window: 72hr
        </div>

        {/* Accuracy badge */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          padding: "4px 12px",
          background: "var(--green-glow)",
          border: "1px solid var(--green)",
          borderRadius: "var(--radius-sm)",
          fontSize: 11,
          fontWeight: 600,
          color: "var(--green-light)",
          letterSpacing: "0.04em",
          whiteSpace: "nowrap",
        }}>
          ◎ Model Accuracy: ≥75%
        </div>

        <div style={{ width: 1, height: 20, background: "var(--border)" }} />

        {/* Live clock */}
        <LiveClock />

      </div>
    </header>
  );
}

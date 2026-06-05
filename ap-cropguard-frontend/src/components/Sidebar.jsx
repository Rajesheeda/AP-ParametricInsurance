import React from "react";

const NAV_ITEMS = [
  { id: "overview",  icon: "◉", label: "District Overview" },
  { id: "insurance", icon: "⬡", label: "Insurance Engine"  },
  { id: "photo",     icon: "⊡", label: "Photo Validation"  },
];

const INFO_STATS = [
  { value: "27",     label: "PILOT AREA",  sub: "Mandals" },
  { value: "5",      label: "MODELLED",    sub: "Crops"   },
  { value: "Kharif", label: "SEASON",      sub: ""        },
];

export default function Sidebar({ activeScreen, onNavigate }) {
  return (
    <aside className="sidebar">

      {/* ── Logo ─────────────────────────────────────── */}
      <div className="sidebar-logo" style={{ padding: "24px 20px 16px" }}>
        <div style={{
          fontFamily: "var(--font-display)",
          fontSize: 28,
          fontWeight: 800,
          color: "var(--green-light)",
          lineHeight: 1,
          letterSpacing: "-0.01em",
        }}>
          AP
        </div>
        <div style={{
          fontFamily: "var(--font-display)",
          fontSize: 18,
          fontWeight: 700,
          color: "var(--text-primary)",
          lineHeight: 1.2,
          marginBottom: 6,
        }}>
          CropGuard
        </div>
        <div style={{
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: "0.15em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          marginBottom: 14,
        }}>
          Kurnool District
        </div>
        <div style={{ height: 1, background: "var(--green)", opacity: 0.35 }} />
      </div>

      {/* ── Navigation ───────────────────────────────── */}
      <nav className="sidebar-nav" style={{ flex: 1, padding: "8px 0" }}>
        {NAV_ITEMS.map((item) => {
          const isActive = activeScreen === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                padding: "11px 20px",
                background: isActive
                  ? "linear-gradient(90deg, rgba(22,163,74,0.18), transparent)"
                  : "transparent",
                borderTop: "none",
                borderRight: "none",
                borderBottom: "none",
                borderLeft: isActive ? "3px solid var(--green)" : "3px solid transparent",
                cursor: "pointer",
                color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                textAlign: "left",
                transition: "all 0.15s",
              }}
              onMouseEnter={e => {
                if (!isActive) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={e => {
                if (!isActive) e.currentTarget.style.background = "transparent";
              }}
            >
              <span style={{ fontSize: 16, width: 20, textAlign: "center" }}>
                {item.icon}
              </span>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* ── Separator ────────────────────────────────── */}
      <div className="divider" style={{ margin: "0 20px" }} />

      {/* ── District Info Stats ───────────────────────── */}
      <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 6 }}>
        {INFO_STATS.map((stat) => (
          <div
            key={stat.label}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "7px 10px",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <div style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.06em" }}>
              {stat.label}
            </div>
            <div style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              fontWeight: 700,
              color: "var(--text-primary)",
            }}>
              {stat.value}
              {stat.sub && (
                <span style={{ fontSize: 10, fontWeight: 400, color: "var(--text-muted)", marginLeft: 4 }}>
                  {stat.sub}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ── Bottom Section ────────────────────────────── */}
      <div className="sidebar-bottom" style={{ padding: "12px 16px 20px", marginTop: "auto" }}>
        <div className="divider" style={{ margin: "0 0 12px" }} />

        {/* System status */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 14,
          padding: "8px 10px",
          background: "var(--green-glow)",
          border: "1px solid rgba(22,163,74,0.25)",
          borderRadius: "var(--radius-sm)",
        }}>
          <span className="status-dot live" />
          <div>
            <div style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.1em",
              color: "var(--green-light)",
            }}>
              SYSTEM LIVE
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
              Backend Connected
            </div>
          </div>
        </div>

        <div className="divider" style={{ margin: "0 0 10px" }} />

        {/* AP Govt branding */}
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {["Govt. of Andhra Pradesh", "Agriculture Department", "Kharif Season 2023"].map((line) => (
            <div
              key={line}
              style={{
                fontSize: 10,
                color: "var(--text-muted)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
              }}
            >
              {line}
            </div>
          ))}
        </div>
      </div>

    </aside>
  );
}

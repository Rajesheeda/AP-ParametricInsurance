"""
AP-CropGuard — Bayesian Weight Engine
======================================
Bayesian weight update engine for satellite-photo
consensus scoring. Implements RLHF (Reinforcement
Learning from Human Feedback) via VRO field
validation. Per-mandal weights adapt based on
cumulative VRO dispute/agree feedback.
Update rule: multiplicative with learning_rate=0.05,
floor=0.30, ceiling=0.90 on satellite weight.
State persists in-memory during server session.
"""

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DEFAULT_W_SAT   = 0.70
DEFAULT_W_PHOTO = 0.30
LEARNING_RATE   = 0.05
W_SAT_FLOOR     = 0.30
W_SAT_CEILING   = 0.90

# ---------------------------------------------------------------------------
# MODULE-LEVEL STATE
# ---------------------------------------------------------------------------

MANDAL_WEIGHTS: dict = {}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# PUBLIC FUNCTIONS
# ---------------------------------------------------------------------------

def get_weights(mandal_id: str) -> dict:
    """
    Return the current weight state for a mandal.
    Initialises with default prior weights if the mandal has not been seen yet.
    """
    if mandal_id not in MANDAL_WEIGHTS:
        MANDAL_WEIGHTS[mandal_id] = {
            "w_satellite": DEFAULT_W_SAT,
            "w_photo": DEFAULT_W_PHOTO,
            "history": [
                {
                    "entry": 0,
                    "label": "Initial (Prior)",
                    "w_satellite": DEFAULT_W_SAT,
                    "w_photo": DEFAULT_W_PHOTO,
                    "event": "System default — drought prior",
                    "timestamp": _now_iso(),
                }
            ],
            "total_feedbacks": 0,
            "dispute_count": 0,
            "agree_count": 0,
        }
    return MANDAL_WEIGHTS[mandal_id]


def update_weights(
    mandal_id: str,
    feedback_type: str,
    vro_id: str,
    note: str = None,
) -> dict:
    """
    Apply a VRO feedback event to update satellite/photo weights for a mandal.

    Supported feedback_type values:
      DISPUTE_SATELLITE — satellite over-estimated; reduce satellite weight
      AGREE_SATELLITE   — satellite correct; slightly increase satellite weight
      DISPUTE_PHOTO     — photo assessment wrong; increase satellite weight
      AGREE_PHOTO       — photo assessment correct; slightly reduce satellite weight

    Weights are bounded: W_SAT_FLOOR (0.30) ≤ w_satellite ≤ W_SAT_CEILING (0.90).
    w_photo is always 1 − w_satellite.
    """
    state = get_weights(mandal_id)

    prev_w_sat   = state["w_satellite"]
    prev_w_photo = state["w_photo"]

    if feedback_type == "DISPUTE_SATELLITE":
        w_sat = max(W_SAT_FLOOR, prev_w_sat * (1 - LEARNING_RATE))
        state["dispute_count"] += 1
        message = (
            f"Satellite weight reduced for {mandal_id}: "
            f"VRO disputed satellite assessment. "
            f"W_sat {prev_w_sat:.4f} → {round(w_sat, 4):.4f}."
        )

    elif feedback_type == "AGREE_SATELLITE":
        w_sat = min(W_SAT_CEILING, prev_w_sat * (1 + LEARNING_RATE * 0.5))
        state["agree_count"] += 1
        message = (
            f"Satellite weight reinforced for {mandal_id}: "
            f"VRO confirmed satellite assessment. "
            f"W_sat {prev_w_sat:.4f} → {round(w_sat, 4):.4f}."
        )

    elif feedback_type == "DISPUTE_PHOTO":
        w_sat = min(W_SAT_CEILING, prev_w_sat * (1 + LEARNING_RATE))
        state["dispute_count"] += 1
        message = (
            f"Satellite weight increased for {mandal_id}: "
            f"VRO disputed photo assessment, trusting satellite more. "
            f"W_sat {prev_w_sat:.4f} → {round(w_sat, 4):.4f}."
        )

    elif feedback_type == "AGREE_PHOTO":
        w_sat = max(W_SAT_FLOOR, prev_w_sat * (1 - LEARNING_RATE * 0.5))
        state["agree_count"] += 1
        message = (
            f"Photo weight reinforced for {mandal_id}: "
            f"VRO confirmed photo assessment. "
            f"W_sat {prev_w_sat:.4f} → {round(w_sat, 4):.4f}."
        )

    else:
        raise ValueError(
            f"Unknown feedback_type '{feedback_type}'. "
            "Valid: DISPUTE_SATELLITE, AGREE_SATELLITE, DISPUTE_PHOTO, AGREE_PHOTO."
        )

    w_sat   = round(w_sat, 4)
    w_photo = round(1.0 - w_sat, 4)

    state["w_satellite"] = w_sat
    state["w_photo"]     = w_photo
    state["total_feedbacks"] += 1

    entry_n = len(state["history"])
    state["history"].append({
        "entry":       entry_n,
        "label":       f"After feedback #{entry_n}",
        "w_satellite": w_sat,
        "w_photo":     w_photo,
        "event":       f"{vro_id}: {feedback_type}",
        "note":        note,
        "timestamp":   _now_iso(),
    })

    return {
        "mandal_id":         mandal_id,
        "feedback_recorded": True,
        "weight_updated":    True,
        "previous_weights":  {"w_satellite": prev_w_sat, "w_photo": prev_w_photo},
        "updated_weights":   {"w_satellite": w_sat,      "w_photo": w_photo},
        "total_feedbacks":   state["total_feedbacks"],
        "learning_rate_applied": LEARNING_RATE,
        "message":           message,
    }


def compute_consensus_loss(
    mandal_id: str,
    satellite_loss_pct: float,
    photo_loss_pct: float,
) -> dict:
    """
    Compute the Bayesian consensus crop loss estimate for a mandal.

    final_loss = w_satellite × satellite_loss_pct + w_photo × photo_loss_pct

    Result is clamped to [0.0, 100.0].
    threshold_breached is True if final_loss >= 43.0 (AP e-relief rule).
    """
    state = get_weights(mandal_id)
    w_sat   = state["w_satellite"]
    w_photo = state["w_photo"]

    final_loss = (w_sat * float(satellite_loss_pct)) + (w_photo * float(photo_loss_pct))
    final_loss = max(0.0, min(100.0, final_loss))

    return {
        "final_loss_pct":      round(final_loss, 2),
        "w_satellite":         w_sat,
        "w_photo":             w_photo,
        "satellite_loss_pct":  float(satellite_loss_pct),
        "photo_loss_pct":      float(photo_loss_pct),
        "threshold_breached":  final_loss >= 43.0,
        "formula":             "W_sat × Satellite + W_photo × Photo",
    }


def get_weight_history(mandal_id: str) -> dict:
    """
    Return the full feedback history and current weights for a mandal.
    Initialises the mandal with default priors if not yet seen.
    """
    state = get_weights(mandal_id)

    return {
        "mandal_id":       mandal_id,
        "weight_history":  state["history"],
        "current_weights": {
            "w_satellite": state["w_satellite"],
            "w_photo":     state["w_photo"],
        },
        "total_feedbacks": state["total_feedbacks"],
        "dispute_count":   state["dispute_count"],
        "agree_count":     state["agree_count"],
    }


def reset_weights(mandal_id: str) -> dict:
    """
    Reset a mandal's weights back to default priors and clear feedback history.
    Entry 0 (the initial prior) is re-created fresh; all subsequent history is dropped.
    """
    initial_entry = {
        "entry":       0,
        "label":       "Initial (Prior)",
        "w_satellite": DEFAULT_W_SAT,
        "w_photo":     DEFAULT_W_PHOTO,
        "event":       "System default — drought prior",
        "timestamp":   _now_iso(),
    }

    MANDAL_WEIGHTS[mandal_id] = {
        "w_satellite":    DEFAULT_W_SAT,
        "w_photo":        DEFAULT_W_PHOTO,
        "history":        [initial_entry],
        "total_feedbacks": 0,
        "dispute_count":  0,
        "agree_count":    0,
    }

    return {
        "mandal_id":      mandal_id,
        "reset":          True,
        "weights_restored": {
            "w_satellite": DEFAULT_W_SAT,
            "w_photo":     DEFAULT_W_PHOTO,
        },
        "message": f"Weights for {mandal_id} reset to system default prior.",
    }

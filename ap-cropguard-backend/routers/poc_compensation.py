"""POC compensation workflow for both lanes. Data: poc/data/derived/compensation.json + settlement/*.csv (p26).

Lane 1 batch: CALCULATED -> APPROVED -> SENT TO INSURER -> PAID. Approval is refused if the batch file's SHA-256 no
  longer matches the one p26 computed, so the approved file is the file sent.
Lane 2 case (per mandal, live event): OPENED -> EVIDENCE RECEIVED (an accepted photo in the evidence log) ->
  AEO VERIFIED >=33% (verified rainfed / irrigated ha) or CLOSED: BELOW 33% -> SANCTIONED (MHA norm x verified ha,
  less any Lane 1 payout for the same calamity) -> PAID.
Every action is appended to poc/data/compensation_log.jsonl with the hash of the previous entry (tamper-evident).
Officers are recorded by role, not by name.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/poc/compensation", tags=["poc-compensation"])
POC = Path(__file__).resolve().parents[2] / "poc" / "data"
SRC = POC / "derived" / "compensation.json"
BATCH_DIR = POC / "derived" / "settlement"
LOG = POC / "compensation_log.jsonl"
EVIDENCE = POC / "photo_evidence.jsonl"
L1_NEXT = {"CALCULATED": {"approve": "APPROVED"}, "APPROVED": {"send": "SENT TO INSURER"}, "SENT TO INSURER": {"paid": "PAID"}}
L2_NEXT = {"OPENED": {"verify": "AEO VERIFIED >=33%", "close": "CLOSED: BELOW 33%"},
           "EVIDENCE RECEIVED": {"verify": "AEO VERIFIED >=33%", "close": "CLOSED: BELOW 33%"},
           "AEO VERIFIED >=33%": {"sanction": "SANCTIONED"}, "SANCTIONED": {"paid": "PAID"}}


def ok(data):
    return {"success": True, "data": data, "error": None,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def load():
    if not SRC.exists():
        raise HTTPException(503, "Compensation not built: run poc/pipeline/p26_compensation.py")
    return json.loads(SRC.read_text(encoding="utf-8"))


def log_entries():
    return [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()] if LOG.exists() else []


def chain_ok(entries):
    prev = ""
    for e in entries:
        body = {k: v for k, v in e.items() if k != "hash"}
        if e.get("prev") != prev or e.get("hash") != hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest():
            return False
        prev = e["hash"]
    return True


def evidence_by_case(event_id):
    """Accepted photos (quality passed, not invalid) per mandal for this event."""
    out = {}
    if not EVIDENCE.exists():
        return out
    for x in EVIDENCE.read_text(encoding="utf-8").splitlines():
        r = json.loads(x)
        adm = (r.get("context") or {}).get("adm3_id")
        if r.get("event_id") != event_id or not adm:
            continue
        v = str(r.get("verdict") or "")
        acc = not (v.startswith("RETAKE") or v.startswith("INVALID"))
        o = out.setdefault(adm, dict(photos=0, accepted=0, damage=0, manual_gps=0))
        o["photos"] += 1
        o["accepted"] += acc
        o["damage"] += acc and "DAMAGE" in v
        o["manual_gps"] += acc and r.get("gps_source") == "manual"
    return out


def state():
    c, entries = load(), log_entries()
    last = {}
    for e in entries:
        last[e["case_id"]] = e
    for b in c["lane1_batches"]:
        e = last.get(b["batch_id"])
        b["state"] = e["state"] if e else "CALCULATED"
        b["history"] = [x for x in entries if x["case_id"] == b["batch_id"]]
        p = BATCH_DIR / b["file"]
        b["file_intact"] = p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == b["sha256"]
    ev = evidence_by_case(c["lane2"]["event"]["id"])
    for k in c["lane2"]["cases"]:
        e = last.get(k["case_id"])
        k["evidence"] = ev.get(k["adm3_id"], dict(photos=0, accepted=0, damage=0, manual_gps=0))
        k["state"] = e["state"] if e else ("EVIDENCE RECEIVED" if k["evidence"]["accepted"] else "OPENED")
        k["history"] = [x for x in entries if x["case_id"] == k["case_id"]]
        k["verified"] = next((x["data"] for x in reversed(k["history"]) if x["state"] == "AEO VERIFIED >=33%"), None)
        k["sanctioned_rs"] = next((x["data"]["amount_rs"] for x in reversed(k["history"]) if x["state"] == "SANCTIONED"), None)
    c["log"] = dict(entries=len(entries), chain_intact=chain_ok(entries))
    return c


class Action(BaseModel):
    case_id: str
    action: str
    officer_role: str
    note: Optional[str] = None
    rainfed_ha: Optional[float] = None
    irrigated_ha: Optional[float] = None


@router.get("")
def get_state():
    return ok(state())


@router.get("/batch/{batch_id}.csv")
def get_batch(batch_id: str):
    b = next((b for b in load()["lane1_batches"] if b["batch_id"] == batch_id), None)
    if not b:
        raise HTTPException(404, "No such batch")
    return FileResponse(BATCH_DIR / b["file"], media_type="text/csv", filename=f"{batch_id}.csv")


@router.post("/action")
def post_action(a: Action):
    c = state()
    role = a.officer_role.strip()[:60]
    if not role:
        raise HTTPException(400, "Officer role is required (e.g. 'AEO Balijipeta', 'Crop Insurance Section').")
    b = next((x for x in c["lane1_batches"] if x["batch_id"] == a.case_id), None)
    k = next((x for x in c["lane2"]["cases"] if x["case_id"] == a.case_id), None)
    if not b and not k:
        raise HTTPException(404, "No such batch or case")
    cur = (b or k)["state"]
    nxt = (L1_NEXT if b else L2_NEXT).get(cur, {}).get(a.action)
    if not nxt:
        raise HTTPException(409, f"'{a.action}' is not allowed from state {cur}")
    data = {}
    if b:
        if not b["file_intact"]:
            raise HTTPException(409, "Batch file changed since it was calculated (SHA-256 mismatch): rebuild with p26 before approval")
        data = dict(sha256=b["sha256"], lines=b["lines"], si_acres=b["si_acres"])
    elif a.action == "verify":
        rf, ir = max(a.rainfed_ha or 0, 0), max(a.irrigated_ha or 0, 0)
        if rf + ir <= 0:
            raise HTTPException(400, "Enter the hectares the AEO verified at >= 33% loss (rainfed and/or irrigated).")
        if rf + ir > k["standing_acres"] * 0.404686 * 1.0001:
            raise HTTPException(400, "Verified area is larger than the standing crop area booked in e-Panta.")
        data = dict(rainfed_ha=rf, irrigated_ha=ir)
    elif a.action == "sanction":
        n, v = c["norms"], k["verified"]
        gross = v["rainfed_ha"] * n["rainfed_per_ha"] + v["irrigated_ha"] * n["irrigated_per_ha"]
        data = dict(gross_rs=round(gross), lane1_adjust_pct=k["lane1_payout_pct"], amount_rs=round(gross),
                    basis=f"{v['rainfed_ha']} ha x Rs {n['rainfed_per_ha']:,} + {v['irrigated_ha']} ha x Rs {n['irrigated_per_ha']:,} ({n['source']})",
                    note_lane1="No Lane 1 payout for this calamity, no adjustment" if not k["lane1_payout_pct"] else
                    "Lane 1 paid for this calamity: per-farmer SDRF is reduced by the insurance claim at disbursement")
    entries = log_entries()
    body = dict(time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), case_id=a.case_id, lane=1 if b else 2, action=a.action,
                from_state=cur, state=nxt, officer_role=role, note=(a.note or "")[:300], data=data,
                prev=entries[-1]["hash"] if entries else "")
    body["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(body, ensure_ascii=False) + "\n")
    return ok(body)

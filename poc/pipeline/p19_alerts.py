"""Farmer / officer alerts in Telugu and English from the pilot decisions (no SMS gateway: text only).

One alert per pilot mandal x event x action (crops grouped). NO PAYOUT decisions produce no alert.
Telugu text is machine-drafted and must be reviewed by the Department before any farmer-facing use.
Output: alerts.csv
"""
import pandas as pd

from common import DERIVED

CROP_TE = {"Paddy": "వరి", "Cotton": "పత్తి", "Red Chillies": "మిరప", "Groundnut": "వేరుశనగ", "Red gram": "కంది"}

a = pd.read_csv(DERIVED / "assessment_pilot.csv", dtype={"district_code": str})
pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
te_name = dict(zip(pil.adm3_name, pil.mandal_te))
ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str}).set_index("id")


def peril(event_id, kind):
    if kind == "season":
        return "rainfall deficit / dry spell", "వర్షాభావం / పొడి వాతావరణం"
    cyc = str(ev.cyclone.get(event_id, "") or "")
    if cyc and cyc != "nan":
        name = cyc.split(":")[0].title()
        return ("a cyclonic storm" if name == "Unnamed" else f"cyclone {name}"), "తుఫాను"
    return "heavy rain", "భారీ వర్షం"


rows = []
for (eid, kind, mandal, action), g in a[a.action != "NO PAYOUT"].groupby(["event_id", "kind", "mandal", "action"]):
    crops = sorted(g.crop.unique())
    en_p, te_p = peril(eid, kind)
    m_te = te_name.get(mandal, mandal)
    crops_en, crops_te = ", ".join(crops), ", ".join(CROP_TE.get(c, c) for c in crops)
    loss = g.est_loss_median_pct.dropna()
    loss_en = f" Estimated yield loss about {loss.median():.0f}% (calibrated on Department CCE, YSR Kadapa)." if len(loss) and loss.median() > 0 else ""
    loss_te = f" అంచనా దిగుబడి నష్టం సుమారు {loss.median():.0f}%." if len(loss) and loss.median() > 0 else ""
    if action.startswith("PARAMETRIC"):
        en = (f"{mandal} mandal: {en_p} damage to {crops_en} is confirmed by both weather and satellite data.{loss_en} "
              f"Compensation will be processed. No field visit is needed.")
        te = (f"{m_te} మండలం: {crops_te} పంటకు {te_p} వల్ల నష్టం జరిగినట్లు వాతావరణ, ఉపగ్రహ సమాచారం రెండూ నిర్ధారించాయి.{loss_te} "
              f"పరిహారం ప్రక్రియ ప్రారంభమవుతుంది. క్షేత్ర పరిశీలన అవసరం లేదు.")
        audience = "farmers"
    elif action.startswith("FIELD"):
        en = (f"{mandal} mandal: {en_p} recorded. To confirm damage to {crops_en}, upload a photo of your field with "
              f"location switched on, or wait for the agriculture officer's field visit.")
        te = (f"{m_te} మండలంలో {te_p} నమోదైంది. {crops_te} పంట నష్టం నిర్ధారణ కోసం ఫోన్‌లో లొకేషన్ ఆన్ చేసి మీ పొలం "
              f"ఫోటోను పంపండి, లేదా వ్యవసాయ అధికారి క్షేత్ర పరిశీలన కోసం వేచి ఉండండి.")
        audience = "farmers + AEO"
    else:
        en = (f"{mandal} mandal: {en_p} recorded this season. Drain standing water from fields and watch {crops_en} "
              f"for disease symptoms. Assessment will be completed at season end.")
        te = (f"{m_te} మండలంలో ఈ సీజన్‌లో {te_p} నమోదైంది. పొలాల్లో నిలిచిన నీటిని బయటకు పంపండి, {crops_te} "
              f"పంటలో తెగుళ్ళ లక్షణాలను గమనించండి. సీజన్ చివరిలో అంచనా పూర్తవుతుంది.")
        audience = "farmers (advisory)"
    rows.append(dict(event_id=eid, kind=kind, start=g.start.iloc[0], district_code=g.district_code.iloc[0], mandal=mandal,
                     action=action, crops=crops_en, audience=audience, english=en, telugu=te))
out = pd.DataFrame(rows).sort_values("start", ascending=False)
out.to_csv(DERIVED / "alerts.csv", index=False, encoding="utf-8-sig")
print(len(out), "alerts;", out.action.value_counts().to_dict())
print(out.iloc[0].english, "\n", out.iloc[0].telugu)

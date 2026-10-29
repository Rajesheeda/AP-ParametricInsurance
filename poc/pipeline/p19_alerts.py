"""Farmer / officer alerts in Telugu and English from the pilot decisions (no SMS gateway: text only).

One alert per pilot mandal x event x action (crops grouped): Lane 1 index payout or Lane 2 relief enumeration.
NO PAYOUT decisions produce no alert.
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
    if action == "INDEX PAYOUT":
        pay = g.lane1_payout_pct.max()
        en = (f"{mandal} mandal: the insurance index for {crops_en} was triggered by {en_p} (weather and satellite indices "
              f"both crossed their pre-agreed levels). Payout {pay:.0f}% of the sum insured goes to insured farmers' accounts "
              f"automatically. No claim form, no field visit.")
        te = (f"{m_te} మండలం: {te_p} కారణంగా {crops_te} పంట బీమా సూచిక ప్రేరేపించబడింది (వాతావరణ, ఉపగ్రహ సూచికలు రెండూ "
              f"ముందుగా నిర్ణయించిన స్థాయిని దాటాయి). బీమా మొత్తంలో {pay:.0f}% పరిహారం బీమా చేసిన రైతుల ఖాతాలకు నేరుగా జమ అవుతుంది. "
              f"దరఖాస్తు అవసరం లేదు, క్షేత్ర పరిశీలన అవసరం లేదు.")
        audience = "insured farmers"
    elif action == "RELIEF ENUMERATION":
        pri = (g.lane2_action.str.startswith("PRIORITY")).any()
        en = (f"{mandal} mandal: {en_p} recorded. Disaster relief (input subsidy) damage enumeration is open for {crops_en}"
              + (" — radar shows flooded fields, priority villages first." if pri else ".")
              + f"{loss_en} Upload a photo of your field with location switched on, or meet the agriculture officer at the field visit.")
        te = (f"{m_te} మండలంలో {te_p} నమోదైంది. {crops_te} పంటకు విపత్తు సహాయం (ఇన్‌పుట్ సబ్సిడీ) నష్ట గణన ప్రారంభమైంది"
              + (" — ఉపగ్రహ రాడార్ ముంపు చూపిన గ్రామాలకు ముందుగా." if pri else ".")
              + f"{loss_te} ఫోన్‌లో లొకేషన్ ఆన్ చేసి మీ పొలం ఫోటో పంపండి, లేదా వ్యవసాయ అధికారి క్షేత్ర పరిశీలనకు హాజరవ్వండి.")
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

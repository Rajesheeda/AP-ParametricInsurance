import re
import sys
from pathlib import Path

sys.path.insert(0, r"C:\AP-Agri-Common")
import agri_common as ac  # noqa: E402
from agri_common.load import norm_name  # noqa: E402

POC = Path(__file__).resolve().parent.parent
DERIVED = POC / "data" / "derived"
OPEN = POC / "data" / "open"
DERIVED.mkdir(parents=True, exist_ok=True)

_TE_SUFFIX = {"ఎ": "A", "బి": "B", "సి": "C", "డి": "D", "ఇ": "E", "ఎఫ్": "F", "జి": "G", "హెచ్": "H", "ఐ": "I", "జె": "J", "కె": "K"}
_TE_RX = re.compile("|".join(sorted(map(re.escape, _TE_SUFFIX), key=len, reverse=True)))


def norm_survey(s):
    """'114/3ఎ' -> '114-3A'; '114 - 3 a' -> '114-3A'."""
    s = _TE_RX.sub(lambda m: _TE_SUFFIX[m.group(0)], str(s))
    s = re.sub(r"[/\._ ]+", "-", s.strip().upper())
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def base_survey(s):
    m = re.match(r"\d+", norm_survey(s))
    return m.group(0) if m else None

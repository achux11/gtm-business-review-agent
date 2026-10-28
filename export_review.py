"""Export governed KPIs and the reference brief to outputs/ (JSON + Markdown) for the deck builder."""
import json
from pathlib import Path

from gtm_review.brief import brief_markdown, reference_brief
from gtm_review.kpis import load_registry
from gtm_review.validate import unsupported

OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)
reg = load_registry()
brief = reference_brief(reg)
md = brief_markdown(brief)
problems = unsupported(md, reg)
if problems:
    raise SystemExit(f"Brief has unsupported numbers: {[p.text for p in problems]}")
(OUT / "business_review.md").write_text(md)
(OUT / "review.json").write_text(json.dumps({
    "kpis": {k: {"value": v.value, "display": v.display(), "name": v.name} for k, v in reg.items()},
    "brief": brief,
}, indent=2))
n_kpi = sum(1 for k in reg.values() if k.domain != "definition")
print(f"Wrote outputs/business_review.md and outputs/review.json ({n_kpi} KPIs + {len(reg) - n_kpi} definitions, 0 unsupported numbers)")

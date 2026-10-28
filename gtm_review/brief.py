"""Business-review context and a reference brief.

`review_context()` is what the MCP server hands to Claude: the governed KPIs
grouped by theme, plus drafting rules. `reference_brief()` is a deterministic
brief built only from registry values; it is used for the deck and as a
baseline that the number checker must always pass.
"""
from __future__ import annotations

from .kpis import KPI, load_registry

THEMES = {
    "Growth & forecast": ["rev_fy25", "growth_reported", "growth_cc", "fx_drag", "rev_fy26_fc",
                          "growth_fy26_fc", "rev_fy27_fc", "mape24_model", "mape24_naive"],
    "Funnel & retention": ["trials", "conv_total", "conv_web", "conv_ios", "conv_android",
                           "conv_gap_web_android", "churn_m1", "churn_m12", "renewal_annual",
                           "mobile_share_start", "mobile_share_end"],
    "Currency risk": ["non_usd_share", "currencies", "fx_risk"],
    "Campaign performance": ["camp_total", "camp_significant", "camp_portfolio_incremental",
                             "camp_transactions", "top25_sales_share", "member_retention",
                             "attach_coupon", "attach_no_coupon", "attach_gap"],
}

DRAFTING_RULES = [
    "Use only numbers returned by get_review_context or get_kpi; do not estimate or round differently.",
    "Write for a senior audience: headline first, then drivers, risks, and recommendations.",
    "Label correlations as correlations (for example, the coupon attach-rate gap).",
    "Say which data is simulated (subscription business) and which is real (retail campaigns).",
    "Before sharing, call check_draft and fix every unsupported number.",
]


def review_context(registry: dict[str, KPI] | None = None) -> dict:
    reg = registry or load_registry()
    return {
        "themes": {t: [reg[i].to_dict() for i in ids] for t, ids in THEMES.items()},
        "drafting_rules": DRAFTING_RULES,
        "data_notes": {
            "subscription": "Simulated subscription business (Jan 2022 - Dec 2025); not real company data.",
            "campaign": "Real retail data: dunnhumby The Complete Journey, 2,500 loyalty households.",
        },
    }


def reference_brief(registry: dict[str, KPI] | None = None) -> dict[str, list[str]]:
    r = registry or load_registry()
    d = {k: v.display() for k, v in r.items()}
    return {
        "Headline": [
            f"Revenue reached {d['rev_fy25']} in FY2025, up {d['growth_reported']} reported and "
            f"{d['growth_cc']} at constant currency; the model forecasts {d['rev_fy26_fc']} for FY2026 "
            f"({d['growth_fy26_fc']} growth).",
            f"Only {d['camp_significant']} of {d['camp_total']} marketing campaigns produced a statistically "
            f"significant sales lift, and the portfolio's incremental sales were {d['camp_portfolio_incremental']} "
            f"versus control, which is indistinguishable from zero.",
        ],
        "Drivers": [
            f"Web converts trials at {d['conv_web']} versus {d['conv_android']} on Android, a "
            f"{d['conv_gap_web_android']} gap, while mobile's share of revenue grew from "
            f"{d['mobile_share_start']} to {d['mobile_share_end']}.",
            f"Churn falls from {d['churn_m1']} in a subscriber's first month to {d['churn_m12']} by month 12, "
            f"so early-tenure retention drives the forecast.",
            f"The top 25% of members generate {d['top25_sales_share']} of sales, and member retention is "
            f"{d['member_retention']} period to period.",
        ],
        "Risks": [
            f"{d['non_usd_share']} of revenue is billed in non-USD currencies ({d['currencies']} currencies); "
            f"a 10% currency move changes FY2026 revenue by {d['fx_risk']}, and currency already cost "
            f"{d['fx_drag']} of FY2025 growth.",
            f"Short-term run-rate forecasts look fine but miss long-range dynamics: over 24 months the cohort "
            f"model's error is {d['mape24_model']} versus {d['mape24_naive']} for a run-rate baseline.",
        ],
        "Recommendations": [
            f"Prioritize Android onboarding tests to close the {d['conv_gap_web_android']} conversion gap as mobile "
            f"becomes a larger share of revenue.",
            "Stop scaling broad campaigns without a control group; fund the 2 that showed lift and re-test the rest.",
            f"Protect the top 25% of members, who drive {d['top25_sales_share']} of sales, with retention offers "
            f"rather than broad discounts.",
            f"Plan FY2026 on constant-currency numbers and show the {d['fx_risk']} currency range alongside them.",
        ],
    }


def brief_markdown(brief: dict[str, list[str]]) -> str:
    lines = ["# GTM Business Review", ""]
    for section, items in brief.items():
        lines.append(f"## {section}")
        lines += [f"- {x}" for x in items]
        lines.append("")
    lines.append("_Subscription figures come from a simulated business; campaign figures are real retail data._")
    return "\n".join(lines)

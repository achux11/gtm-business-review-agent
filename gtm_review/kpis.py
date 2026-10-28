"""Governed KPI registry.

Every number the agent is allowed to use lives here, with a name, unit,
definition and source. KPIs come from two places:

1. data/subscription_revenue_model.xlsx  - workbook produced by
   github.com/achux11/subscription-revenue-cohort-model (simulated business)
2. data/campaign_kpis.json               - published results of
   github.com/achux11/loyalty-promotion-roi (dunnhumby Complete Journey)

Derived KPIs (gaps, growth rates) are computed here from those inputs, so
the formula is visible and testable instead of being typed into a slide.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path

import openpyxl

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WORKBOOK = DATA_DIR / "subscription_revenue_model.xlsx"
CAMPAIGN_JSON = DATA_DIR / "campaign_kpis.json"
SUB_SOURCE = "github.com/achux11/subscription-revenue-cohort-model (simulated data)"


@dataclass(frozen=True)
class KPI:
    id: str
    name: str
    value: float
    unit: str          # "count", "usd", "pct" (stored as a fraction), "pts" (percentage points)
    definition: str
    source: str
    domain: str        # "subscription" or "campaign"
    formula: str = ""  # filled in for derived KPIs

    def display(self) -> str:
        """Format the value the way it should appear in a leadership brief."""
        v = self.value
        if self.unit == "pct":
            return f"{v * 100:.1f}%"
        if self.unit == "pts":
            return f"{v:.1f} pts"
        if self.unit == "usd":
            sign, a = ("-" if v < 0 else ""), abs(v)
            if a >= 1e6:
                return f"{sign}${a / 1e6:.2f}M"
            if a >= 1e3:
                return f"{sign}${a / 1e3:.0f}K"
            return f"{sign}${a:,.2f}"
        return f"{v:,.0f}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["display"] = self.display()
        return d


def _sheet_rows(wb, name):
    return list(wb[name].iter_rows(values_only=True))


def _subscription_kpis() -> list[KPI]:
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)
    summary = {r[0]: r[1] for r in _sheet_rows(wb, "Summary")[1:] if r[0]}
    conv = {r[0]: r for r in _sheet_rows(wb, "Trial Conversion")[1:]}
    fx = {r[0]: r for r in _sheet_rows(wb, "FX Scenarios")[1:]}
    robust = _sheet_rows(wb, "Backtest Robustness")[1:]

    def k(id, name, value, unit, definition, formula=""):
        return KPI(id, name, float(value), unit, definition, SUB_SOURCE, "subscription", formula)

    out = [
        k("trials", "Trial starts, Jan 2022 - Dec 2025", summary["Trial starts (Jan 2022 - Dec 2025)"], "count",
          "Free-trial sign-ups over the full history"),
        k("active_subs", "Active subscribers, Dec 2025", summary["Active subscribers, Dec 2025"], "count",
          "Paying subscribers at the end of Dec 2025"),
        k("conv_total", "Trial-to-paid conversion", summary["Trial-to-paid conversion"], "pct",
          "Share of trials that became paying subscribers"),
        k("conv_web", "Trial-to-paid conversion, Web", conv["Web"][3], "pct", "Web trials that converted"),
        k("conv_ios", "Trial-to-paid conversion, iOS", conv["iOS"][3], "pct", "iOS trials that converted"),
        k("conv_android", "Trial-to-paid conversion, Android", conv["Android"][3], "pct",
          "Android trials that converted"),
        k("churn_m1", "Month-1 churn, monthly plan", summary["Month-1 churn (monthly plan)"], "pct",
          "Share of new monthly subscribers who cancel in their first paid month"),
        k("churn_m12", "Month-12 churn, monthly plan", summary["Month-12 churn (monthly plan)"], "pct",
          "Churn rate at paid tenure month 12"),
        k("renewal_annual", "Annual-plan renewal rate", summary["Annual-plan renewal rate"], "pct",
          "Share of annual subscribers who renew"),
        k("arpu", "Net ARPU, Dec 2025 (USD/month)", summary["Net ARPU, Dec 2025 (USD/month)"], "usd",
          "Net revenue per active subscriber after app-store and card fees"),
        k("rev_fy25", "FY2025 net revenue", summary["FY2025 net revenue (USD)"], "usd", "Recognized net revenue, 2025"),
        k("growth_reported", "FY25 revenue growth, reported", summary["Revenue growth FY25 vs FY24, reported"], "pct",
          "Year-over-year growth in USD"),
        k("growth_cc", "FY25 revenue growth, constant currency",
          summary["Revenue growth FY25 vs FY24, constant currency"], "pct",
          "Year-over-year growth at constant exchange rates"),
        k("rev_fy26_fc", "FY2026 net revenue forecast", summary["Forecast FY2026 net revenue (USD, constant ccy)"], "usd",
          "Cohort-based forecast, constant currency"),
        k("rev_fy27_fc", "FY2027 net revenue forecast", summary["Forecast FY2027 net revenue (USD, constant ccy)"], "usd",
          "Cohort-based forecast, constant currency"),
        k("fx_risk", "FY2026 revenue impact of a 10% currency move",
          abs(fx["Non-USD currencies +10% vs USD"][2]), "usd",
          "Change in FY2026 revenue if non-USD currencies move 10% against USD (either direction)"),
        k("non_usd_share", "Non-USD share of revenue, Dec 2025", summary["Non-USD share of revenue, Dec 2025"], "pct",
          "Revenue earned in EUR, GBP and BRL"),
        k("currencies", "Billing currencies", len([r for r in _sheet_rows(wb, "Currency Mix")[1:] if r[0]]), "count",
          "Currencies revenue is billed in"),
        k("mobile_share_start", "Mobile share of net revenue, Jan 2024",
          summary["Mobile (iOS+Android) share of net revenue, first month"], "pct", "iOS + Android share"),
        k("mobile_share_end", "Mobile share of net revenue, Dec 2025",
          summary["Mobile (iOS+Android) share of net revenue, Dec 2025"], "pct", "iOS + Android share"),
        k("mape24_model", "24-month forecast error, cohort model (median of 10 runs)",
          statistics.median(r[3] for r in robust), "pct", "Median revenue MAPE over 10 independent simulations"),
        k("mape24_naive", "24-month forecast error, run-rate baseline (median of 10 runs)",
          statistics.median(r[4] for r in robust), "pct", "Median revenue MAPE of a naive run-rate forecast"),
    ]
    by = {x.id: x for x in out}
    out += [
        k("conv_gap_web_android", "Conversion gap, Web vs. Android",
          (by["conv_web"].value - by["conv_android"].value) * 100, "pts",
          "Percentage-point gap in trial-to-paid conversion", "conv_web - conv_android"),
        k("fx_drag", "FX drag on FY25 growth", (by["growth_cc"].value - by["growth_reported"].value) * 100, "pts",
          "Growth lost to currency moves", "growth_cc - growth_reported"),
        k("growth_fy26_fc", "FY2026 forecast growth vs. FY2025", by["rev_fy26_fc"].value / by["rev_fy25"].value - 1,
          "pct", "Forecast growth at constant currency", "rev_fy26_fc / rev_fy25 - 1"),
    ]
    return out


def _campaign_kpis() -> list[KPI]:
    raw = json.loads(CAMPAIGN_JSON.read_text())
    out = [KPI(d["id"], d["name"], float(d["value"]), d["unit"], d["definition"], raw["source"], "campaign")
           for d in raw["kpis"]]
    by = {x.id: x for x in out}
    out.append(KPI("attach_gap", "Attach-rate gap, coupon vs. no coupon",
                   (by["attach_coupon"].value - by["attach_no_coupon"].value) * 100, "pts",
                   "Percentage-point difference in soft-drink attach rate (correlation, not causation)",
                   raw["source"], "campaign", "attach_coupon - attach_no_coupon"))
    return out


def _definition_kpis() -> list[KPI]:
    """Analysis parameters that legitimately appear in a brief (scenario sizes, cut-offs, horizons)."""
    src = "analysis definitions"
    return [
        KPI("fx_scenario", "Currency scenario size", 0.10, "pct", "Non-USD currencies moved +/-10% vs. USD", src, "definition"),
        KPI("top_tier", "Top spending tier cut-off", 0.25, "pct", "Highest-spending quartile of members", src, "definition"),
        KPI("tenure_month", "Tenure month for late churn", 12, "count", "Paid month 12 in the churn curve", src, "definition"),
        KPI("horizon_months", "Long-range forecast horizon", 24, "count", "Months ahead in the long-range backtest", src, "definition"),
    ]


def load_registry() -> dict[str, KPI]:
    """Return every governed KPI keyed by id."""
    reg = {}
    for kpi in _subscription_kpis() + _campaign_kpis() + _definition_kpis():
        if kpi.id in reg:
            raise ValueError(f"Duplicate KPI id: {kpi.id}")
        reg[kpi.id] = kpi
    return reg

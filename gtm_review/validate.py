"""Number checker for AI-drafted business reviews.

An LLM can write a fluent leadership brief and still get a number wrong.
`check_numbers` pulls every figure out of a draft (percentages, dollar
amounts, K/M counts, plain counts, percentage points) and checks each one
against the governed KPI registry, allowing only the rounding implied by how
the number is written. Anything it cannot trace back to a KPI is returned as
unsupported, so a person fixes it before the brief goes to leadership.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .kpis import KPI

# A number token: optional $ / sign, digits with commas/decimals, optional scale and unit.
NUM_RE = re.compile(
    r"(?<![A-Za-z0-9.])(?<![A-Za-z]-)(?P<neg>(?<![A-Za-z])[-−])?(?P<dollar>\$)?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s?(?P<scale>[KkMB](?![A-Za-z]))?(?P<plus>\+)?"
    r"(?P<unit>\s?%|\s?(?:pts?|points?|percentage points)\b)?"
)

YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")


@dataclass
class Finding:
    text: str
    value: float
    kind: str              # "pct", "pts", "usd", "count"
    supported: bool
    kpi_id: str | None = None
    note: str = ""


def _decimals(num: str) -> int:
    return len(num.split(".")[1]) if "." in num else 0


def _candidates(kpi: KPI, kind: str) -> list[float]:
    """Values a KPI can legitimately appear as, in the units of the written number."""
    v = kpi.value
    if kind == "pct":
        return [v * 100] if kpi.unit == "pct" else []
    if kind == "pts":
        if kpi.unit == "pts":
            return [abs(v)]
        return []
    if kind == "usd":
        return [v, abs(v)] if kpi.unit == "usd" else []
    # plain counts: counts, or a pts/pct KPI written without a unit sign is NOT accepted
    return [v] if kpi.unit == "count" else []


def _match(written: float, tol: float, lower_bound: bool, kpi: KPI, kind: str) -> bool:
    for c in _candidates(kpi, kind):
        if lower_bound:
            # "285K+" means at least 285K: true value must be >= written and round down to it
            if c >= written and c - written < max(tol * 2, written * 0.1):
                return True
        elif abs(c - written) <= tol + 1e-9:
            return True
    return False


def check_numbers(text: str, registry: dict[str, KPI], allow: set[float] | None = None) -> list[Finding]:
    """Return one Finding per number in `text`. Years and allow-listed values are skipped."""
    allow = allow or set()
    findings = []
    for m in NUM_RE.finditer(text):
        raw = m.group(0).strip()
        num = m.group("num")
        base = float(num.replace(",", ""))
        if m.group("neg"):
            base = -base
        unit = (m.group("unit") or "").strip().lower()
        scale = (m.group("scale") or "").upper()

        if not unit and not scale and not m.group("dollar") and YEAR_RE.match(num):
            continue  # a year like 2026
        if base in allow:
            continue

        mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(scale, 1)
        tol = 0.5 * 10 ** (-_decimals(num)) * mult
        written = abs(base) * mult
        if unit.startswith("%"):
            kind = "pct"
        elif unit:
            kind = "pts"
        elif m.group("dollar"):
            kind = "usd"
        else:
            kind = "count"

        hit = None
        for kpi in registry.values():
            if _match(written, tol, bool(m.group("plus")), kpi, kind):
                hit = kpi.id
                break
        findings.append(Finding(raw, written, kind, hit is not None, hit,
                                "" if hit else "not traceable to any governed KPI"))
    return findings


def unsupported(text: str, registry: dict[str, KPI], allow: set[float] | None = None) -> list[Finding]:
    return [f for f in check_numbers(text, registry, allow) if not f.supported]

"""MCP server: governed GTM business-review data for Claude.

Tools
  list_kpis(domain)      - every governed KPI (optionally one domain)
  get_kpi(kpi_id)        - one KPI with definition, source and display format
  get_review_context()   - KPIs grouped by theme plus drafting rules
  check_draft(text)      - flags every number in a draft that is not traceable to a KPI
Resources
  gtm://drafting-rules   - the rules Claude must follow when drafting
  gtm://reference-brief  - a brief built only from governed numbers

Run:  python server.py   (stdio transport, for Claude Desktop)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from gtm_review.brief import DRAFTING_RULES, brief_markdown, reference_brief, review_context
from gtm_review.kpis import load_registry
from gtm_review.validate import check_numbers

mcp = FastMCP("gtm-business-review")
REGISTRY = load_registry()


@mcp.tool()
def list_kpis(domain: str = "") -> list[dict]:
    """List governed KPIs. domain: 'subscription', 'campaign', 'definition', or '' for all."""
    return [k.to_dict() for k in REGISTRY.values() if not domain or k.domain == domain]


@mcp.tool()
def get_kpi(kpi_id: str) -> dict:
    """Return one KPI by id, including its definition, source and how to display it."""
    if kpi_id not in REGISTRY:
        return {"error": f"Unknown KPI '{kpi_id}'. Call list_kpis to see valid ids."}
    return REGISTRY[kpi_id].to_dict()


@mcp.tool()
def get_review_context() -> dict:
    """Everything needed to draft a leadership business review: KPIs by theme and drafting rules."""
    return review_context(REGISTRY)


@mcp.tool()
def check_draft(text: str) -> dict:
    """Check every number in a draft against the governed KPIs. Fix all unsupported numbers before sharing."""
    findings = check_numbers(text, REGISTRY)
    bad = [f.__dict__ for f in findings if not f.supported]
    return {
        "numbers_checked": len(findings),
        "supported": len(findings) - len(bad),
        "unsupported": bad,
        "ready_to_share": not bad,
    }


@mcp.resource("gtm://drafting-rules")
def drafting_rules() -> str:
    return "\n".join(f"- {r}" for r in DRAFTING_RULES)


@mcp.resource("gtm://reference-brief")
def reference() -> str:
    return brief_markdown(reference_brief(REGISTRY))


if __name__ == "__main__":
    mcp.run()

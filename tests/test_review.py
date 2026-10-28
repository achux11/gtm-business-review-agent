import asyncio
import sys
from pathlib import Path

import pytest

from gtm_review.brief import THEMES, brief_markdown, reference_brief
from gtm_review.kpis import load_registry
from gtm_review.validate import check_numbers, unsupported

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return load_registry()


def test_registry_loads_known_values(reg):
    assert reg["trials"].value == 285585
    assert reg["conv_web"].display() == "41.9%"
    assert reg["conv_android"].display() == "29.8%"
    assert reg["camp_significant"].value == 2 and reg["camp_total"].value == 30
    assert reg["fx_risk"].display() == "$201K"


def test_derived_kpis_match_their_formulas(reg):
    gap = (reg["conv_web"].value - reg["conv_android"].value) * 100
    assert reg["conv_gap_web_android"].value == pytest.approx(gap)
    assert reg["fx_drag"].display() == "2.1 pts"
    assert reg["attach_gap"].display() == "10.3 pts"


def test_median_backtest_errors_match_published_results(reg):
    assert reg["mape24_model"].display() == "2.8%"
    assert reg["mape24_naive"].display() == "17.6%"


def test_every_theme_kpi_exists(reg):
    for ids in THEMES.values():
        for i in ids:
            assert i in reg


def test_reference_brief_has_no_unsupported_numbers(reg):
    md = brief_markdown(reference_brief(reg))
    assert len(check_numbers(md, reg)) >= 25
    assert unsupported(md, reg) == []


@pytest.mark.parametrize("wrong", ["$3.5M", "43%", "3 of 30", "15.0 pts", "$250K"])
def test_checker_flags_wrong_numbers(reg, wrong):
    assert unsupported(f"Leadership update: {wrong}.", reg)


def test_checker_respects_rounding_and_lower_bounds(reg):
    assert not unsupported("Web converts at 41.9% and revenue was $3.37M.", reg)
    # 285,585 rounds to 286K, so "285K" is wrong but "285K+" (at least 285K) is right
    assert unsupported("We ran 285K trials.", reg)
    assert not unsupported("We ran 285K+ trials.", reg)


def test_years_are_not_treated_as_metrics(reg):
    assert not unsupported("FY2026 planning starts in 2026.", reg)


def test_mcp_server_exposes_tools_and_checks_drafts():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")], cwd=str(ROOT))
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                res = await s.call_tool("check_draft", {"text": "Web converts at 45% vs 29.8% on Android."})
                return tools, res.structuredContent or res.content

    tools, result = asyncio.run(run())
    assert {"list_kpis", "get_kpi", "get_review_context", "check_draft"} <= tools
    text = str(result)
    assert "45%" in text and "'ready_to_share': False" in text.replace('"', "'").replace("false", "False")


def test_hyphenated_labels_are_not_numbers(reg):
    # "month-1" and "Q4" are labels, not metrics; "-$30K" is a real negative figure
    assert not unsupported("Month-1 churn is 17.4% in Q4; portfolio sales were -$30K.", reg)

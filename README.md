# GTM Business Review Agent (MCP + Claude)

**An MCP server that gives Claude governed access to go-to-market KPIs, and checks every number in an AI-drafted business review before it reaches leadership.**

LLMs write fluent leadership briefs, and they also round, guess and invent numbers. This project puts guardrails around that:

1. **Governed KPI registry:** 37 KPIs plus 4 analysis definitions (scenario sizes, cut-offs, horizons), each with a definition, unit, display format and source. Derived KPIs (gaps, growth rates) are computed from their inputs with the formula recorded, not typed into a slide.
2. **MCP tools for Claude:** Claude pulls KPIs and drafting rules through the server instead of being pasted numbers.
3. **Number checker:** `check_draft` extracts every figure from a draft (percentages, $K/$M, counts, percentage points) and traces each to a KPI, allowing only the rounding implied by how it is written. Anything untraceable comes back as unsupported.
4. **Leadership deck:** a 5-slide business review (`outputs/gtm_business_review.pptx`) built only from checked numbers.

## Data

| Domain | Source | Real or simulated |
|---|---|---|
| Subscription growth, funnel, churn, currency | [subscription-revenue-cohort-model](https://github.com/achux11/subscription-revenue-cohort-model) workbook (`data/subscription_revenue_model.xlsx`) | Simulated business |
| Campaign performance, member value | Published results of [loyalty-promotion-roi](https://github.com/achux11/loyalty-promotion-roi) (`data/campaign_kpis.json`) | Real retail data (dunnhumby *The Complete Journey*) |

## MCP tools

| Tool | What it does |
|---|---|
| `list_kpis(domain)` | All governed KPIs, or one domain (`subscription`, `campaign`, `definition`) |
| `get_kpi(kpi_id)` | One KPI with definition, source and display format |
| `get_review_context()` | KPIs grouped into 4 themes plus drafting rules |
| `check_draft(text)` | Every number checked; returns unsupported numbers and `ready_to_share` |

Resources: `gtm://drafting-rules`, `gtm://reference-brief`.

## What the checker catches

| Draft says | Result | Why |
|---|---|---|
| "Web converts at 41.9%" | Supported | Matches `conv_web` (41.88%) at one decimal |
| "Web converts at 43%" | **Unsupported** | No KPI rounds to 43% |
| "Revenue hit $3.5M" | **Unsupported** | FY2025 revenue is $3.37M |
| "We ran 285K trials" | **Unsupported** | 285,585 rounds to 286K; write "285K+" or "286K" |
| "Portfolio sales were -$30K" | Supported | Matches `camp_portfolio_incremental` |
| "Month-1 churn in Q4 2026" | Ignored | Labels and years are not metrics |

## Reference brief and deck

`python export_review.py` builds `outputs/business_review.md` from the registry and refuses to write it if any number is unsupported. `node build_deck.js` turns it into the 5-slide deck:

1. Headline: growth is real, campaign spend is not working
2. On track for 27.1% growth; currency is a drag (revenue chart, FX drag, forecast error, FX risk)
3. Android converts 12.1 pts below Web as mobile grows (conversion chart, churn, renewal)
4. Only 2 of 30 campaigns moved sales (campaign split, member concentration, attach rate)
5. Four actions for the next planning cycle

## Run

```bash
pip install -r requirements.txt
pytest -q                      # 15 tests, including an end-to-end MCP client test
python export_review.py        # validated brief -> outputs/
npm install pptxgenjs          # once
node build_deck.js             # deck -> outputs/gtm_business_review.pptx
```

### Use it from Claude Desktop

Add to `claude_desktop_config.json` (use your own paths):

```json
{
  "mcpServers": {
    "gtm-business-review": {
      "command": "/path/to/python",
      "args": ["/path/to/gtm-business-review-agent/server.py"]
    }
  }
}
```

Then ask: *"Use gtm-business-review to draft a one-page business review for leadership, then run check_draft and fix anything unsupported."*

## Limitations

- The subscription business is simulated; campaign figures are taken from the published results table, not recomputed here.
- The checker verifies that numbers trace to a KPI, not that the sentence uses the right KPI (a correct number in the wrong context can still pass). Pair it with a human read.
- Small allowed values (scenario sizes, the top-25% cut-off, month 12, 24-month horizon) are registered as analysis definitions so they can appear in text.

---
**Author:** Achintya Vamshi Nudurupati · [GitHub @achux11](https://github.com/achux11) · [LinkedIn](https://linkedin.com/in/achintya11)

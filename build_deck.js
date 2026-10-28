// Builds outputs/gtm_business_review.pptx from outputs/review.json.
// Every number on a slide comes from the governed KPI registry (see export_review.py).
// Usage: python export_review.py && node build_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

let applyTheme = null;
for (const p of [process.env.APPLY_THEME_JS, "/mnt/skills/public/pptx/scripts/apply_theme.js"]) {
  if (p && fs.existsSync(p)) { applyTheme = require(p).applyTheme; break; }
}

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "outputs", "review.json"), "utf8"));
const K = R.kpis, B = R.brief;
const D = (id) => K[id].display;

const THEME = {
  name: "GTM Review",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "16213E", lt1: "FFFFFF", dk2: "0F3460", lt2: "EEF2F7",
    accent1: "E9A23B", accent2: "0F3460", accent3: "5C7AEA", accent4: "C94F4F",
    accent5: "3FA796", accent6: "8A94A6", hlink: "0F3460", folHlink: "5C7AEA",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "GTM Business Review";
pres.author = "Achintya Vamshi Nudurupati";
const C = pres.SchemeColor;

const FOOT = "Subscription figures: simulated business. Campaign figures: dunnhumby Complete Journey (real retail data).";

pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.3, w: 8.8, h: 1.4, fontSize: 36, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.85, w: 8.8, h: 1.6, fontSize: 16, color: C.background2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: C.background1 },
  margin: [0.5, 0.5, 0.6, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.8, fontSize: 26, bold: true, color: C.text2, valign: "middle" }, text: "" } },
    { text: { text: FOOT, options: { x: 0.5, y: 5.2, w: 7.6, h: 0.3, fontSize: 9, color: C.accent6, isTextBox: true, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: C.accent6 },
});

function stat(slide, x, y, w, big, label, colorKey) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: 1.15, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 },
    objectName: `card ${label}`,
  });
  slide.addText(big, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.6, fontSize: 30, bold: true, color: colorKey, isTextBox: true, margin: 0, objectName: `stat ${label}` });
  slide.addText(label, { x: x + 0.15, y: y + 0.68, w: w - 0.3, h: 0.4, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, objectName: `label ${label}` });
}

function chartOpts(title, extra) {
  return Object.assign({
    showTitle: true, title, titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent6, catAxisLabelFontSize: 11, valAxisLabelFontSize: 9,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "DDE3EC", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
  }, extra);
}

// 1. Title / headline
pres.addSection({ title: "Summary" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Summary" });
s.addText("GTM Business Review: growth is real, campaign spend is not working", { placeholder: "title" });
s.addText([
  { text: `${D("rev_fy25")} FY2025 revenue, ${D("growth_cc")} constant-currency growth; ${D("rev_fy26_fc")} forecast for FY2026`, options: { breakLine: true } },
  { text: `Only ${D("camp_significant")} of ${D("camp_total")} campaigns produced a significant sales lift` },
], { placeholder: "body" });
s.addNotes(B.Headline.join(" "));

// 2. Growth & forecast
pres.addSection({ title: "Performance" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Performance" });
s.addText(`On track for ${D("growth_fy26_fc")} growth; currency is a drag`, { placeholder: "title" });
s.addChart(pres.charts.BAR, [{
  name: "Net revenue ($M)", labels: ["FY2025 actual", "FY2026 forecast", "FY2027 forecast"],
  values: [K.rev_fy25.value, K.rev_fy26_fc.value, K.rev_fy27_fc.value].map((v) => Math.round(v / 1e4) / 100),
}], chartOpts("Net revenue, $M (constant currency forecast)", {
  x: 0.5, y: 1.25, w: 5.4, h: 3.8, barDir: "col", chartColors: [HEX.dk2], dataLabelFormatCode: "$0.00\"M\"", valAxisLabelFormatCode: "$0.0",
}));
stat(s, 6.3, 1.3, 3.2, D("fx_drag"), "of FY2025 growth lost to currency", C.accent4);
stat(s, 6.3, 2.6, 3.2, D("mape24_model"), `24-month forecast error vs. ${D("mape24_naive")} for run-rate`, C.accent5);
stat(s, 6.3, 3.9, 3.2, D("fx_risk"), "FY2026 swing from a 10% currency move", C.text2);
s.addNotes(B.Risks.join(" "));

// 3. Funnel drivers
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Performance" });
s.addText(`Android converts ${D("conv_gap_web_android")} below Web as mobile grows`, { placeholder: "title" });
s.addChart(pres.charts.BAR, [{
  name: "Trial-to-paid conversion", labels: ["Web", "iOS", "Android"],
  values: [K.conv_web.value, K.conv_ios.value, K.conv_android.value].map((v) => Math.round(v * 1000) / 10),
}], chartOpts("Trial-to-paid conversion by platform (%)", {
  x: 0.5, y: 1.25, w: 5.4, h: 3.8, barDir: "bar", chartColors: [HEX.dk2, HEX.dk2, HEX.accent1], dataLabelFormatCode: "0.0\"%\"", valAxisLabelFormatCode: "0",
}));
stat(s, 6.3, 1.3, 3.2, `${D("mobile_share_start")} → ${D("mobile_share_end")}`, "mobile share of revenue", C.text2);
stat(s, 6.3, 2.6, 3.2, D("churn_m1"), `month-1 churn, falling to ${D("churn_m12")} by month 12`, C.accent4);
stat(s, 6.3, 3.9, 3.2, D("renewal_annual"), "annual-plan renewal rate", C.accent5);
s.addNotes(B.Drivers.slice(0, 2).join(" "));

// 4. Campaigns
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Performance" });
s.addText(`Only ${D("camp_significant")} of ${D("camp_total")} campaigns moved sales`, { placeholder: "title" });
s.addChart(pres.charts.DOUGHNUT, [{
  name: "Campaigns", labels: ["Significant lift", "No significant lift"],
  values: [K.camp_significant.value, K.camp_total.value - K.camp_significant.value],
}], {
  x: 0.5, y: 1.25, w: 4.2, h: 3.8, holeSize: 62, chartColors: [HEX.accent1, "C9D2E0"],
  showTitle: true, title: `${D("camp_total")} campaigns vs. untargeted control`, titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
  showValue: true, showPercent: false, dataLabelColor: HEX.dk1, dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt",
  showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: HEX.dk1, legendFontFace: "+mn-lt",
});
stat(s, 5.2, 1.3, 4.3, D("camp_portfolio_incremental"), "portfolio incremental sales vs. control (not different from zero)", C.accent4);
stat(s, 5.2, 2.6, 4.3, D("top25_sales_share"), "of sales come from the top 25% of members", C.text2);
stat(s, 5.2, 3.9, 4.3, `${D("attach_coupon")} vs. ${D("attach_no_coupon")}`, "attach rate, coupon vs. no coupon (correlation only)", C.accent5);
s.addNotes(B.Drivers[2] + " " + B.Headline[1]);

// 5. Recommendations
pres.addSection({ title: "Actions" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Actions" });
s.addText("Four actions for the next planning cycle", { placeholder: "title" });
const recs = [
  ["Fix Android onboarding", `Test onboarding changes to close the ${D("conv_gap_web_android")} gap as mobile becomes ~half of revenue.`],
  ["Fund what works", `Keep the ${D("camp_significant")} campaigns with proven lift; require a control group before scaling any other.`],
  ["Protect top members", `Retention offers for the top 25%, who drive ${D("top25_sales_share")} of sales, instead of broad discounts.`],
  ["Plan in constant currency", `Set FY2026 targets at constant currency and show the ${D("fx_risk")} FX range alongside.`],
];
recs.forEach(([h, t], i) => {
  const x = 0.5 + (i % 2) * 4.6, y = 1.45 + Math.floor(i / 2) * 1.75;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.45, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `rec card ${i + 1}` });
  s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.5, h: 0.5, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `rec badge ${i + 1}` });
  s.addText(String(i + 1), { x: x + 0.2, y: y + 0.22, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.text1, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: `rec num ${i + 1}` });
  s.addText(h, { x: x + 0.85, y: y + 0.2, w: 3.4, h: 0.55, fontSize: 16, bold: true, color: C.text2, isTextBox: true, margin: 0, valign: "middle", objectName: `rec head ${i + 1}` });
  s.addText(t, { x: x + 0.85, y: y + 0.78, w: 3.4, h: 0.8, fontSize: 12, color: C.text1, isTextBox: true, margin: 0, valign: "top", objectName: `rec body ${i + 1}` });
});
s.addNotes(B.Recommendations.join(" "));

(async () => {
  const out = path.join(__dirname, "outputs", "gtm_business_review.pptx");
  await pres.writeFile({ fileName: out });
  if (applyTheme) await applyTheme(out, THEME);
  console.log("Wrote", out, applyTheme ? "(theme applied)" : "(theme not applied: apply_theme.js not found)");
})();

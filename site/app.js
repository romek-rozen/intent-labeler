// Intent Labeler site. Static: no server, no stored key of ours.
// The playground mirrors the library's rules: the model groups, this code counts.

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (v) => (v == null ? "-" : `${Math.round(v * 100)}%`);
const color = (i) => `var(--i${(i % 8) + 1})`;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

const data = await fetch("data.json").then((r) => r.json());

// ---------------------------------------------------------------- hero ----
const serp = $("#serp");
const hero = data.hero;
$("#heroKeyword").textContent = hero.keyword;

function rowHtml(r) {
  return `<div class="row" data-id="${r.id}"><span class="rank">${r.rank}</span>
    <span><span class="t">${esc(r.title)}</span><span class="d">${esc(r.domain)}</span></span></div>`;
}
const byId = Object.fromEntries(hero.results.map((r) => [r.id, r]));
serp.innerHTML = `
  <div class="results">${hero.results.map(rowHtml).join("")}</div>
  <div class="groups">${hero.intents.map((it, i) => `
    <div class="group" style="--c:${color(i)}">
      <h3>${esc(it.title)}</h3>
      <p class="form">Form: ${esc(it.form)}</p>
      <div class="rows">${it.result_ids.map((id) => rowHtml(byId[id])).join("")}</div>
      <div class="nums"><span><b>${pct(it.coverage)}</b> of results address it</span><span><b>${pct(it.share)}</b> share after splitting</span></div>
    </div>`).join("")}</div>`;
serp.insertAdjacentHTML("afterend", `<p class="serp-note">Result 4 serves two intents, so it counts half to each. Shares add up to 100%; coverage does not have to.</p>`);
// The hero shows the finished reading: results already sorted into intents, with the numbers.
serp.classList.add("grouped", "settled");

// ------------------------------------------------------------ examples ----
// Every card carries the same pill row (facts), then warnings in their own style, so cards align.
$("#exampleList").innerHTML = data.examples.map((ex) => {
  const facts = [
    `Google ${ex.market}`,
    `${ex.results} results`,
    ex.volume != null ? `${ex.volume.toLocaleString("en")} / month` : "volume n/a",
    ex.season_index ? `seasonality ${ex.season_index}` : "seasonality n/a",
    ex.length ? `${ex.length} words` : "no reference length",
    `${ex.models} models`,
  ];
  const warns = ex.warnings.length ? ex.warnings.map((w) => `<span class="tag warn">${esc(w.replaceAll("_", " "))}</span>`).join("")
    : `<span class="tag ok">no warnings</span>`;
  return `<a class="example" href="examples/${ex.slug}.html">
    <span class="q">${esc(ex.keyword)}</span>
    <span class="stack" aria-hidden="true">${ex.intents.map((it, i) => `<span style="flex:${it.share};background:${color(i)}"></span>`).join("")}</span>
    <p class="dom"><b>${esc(ex.dominant)}</b><br>${esc(ex.form)}</p>
    <span class="tags">${facts.map((f) => `<span class="tag">${esc(f)}</span>`).join("")}</span>
    <span class="tags">${warns}</span>
  </a>`;
}).join("");

// ---------------------------------------------------------- playground ----
// Markets: DataForSEO location code + the languages Google serves there.
const MARKETS = [
  ["United States", 2840, ["en", "es"]], ["United Kingdom", 2826, ["en"]], ["Poland", 2616, ["pl"]],
  ["Germany", 2276, ["de"]], ["Austria", 2040, ["de"]], ["Switzerland", 2756, ["de", "fr", "it"]],
  ["France", 2250, ["fr"]], ["Italy", 2380, ["it"]], ["Spain", 2724, ["es"]],
  ["Netherlands", 2528, ["nl"]], ["Czechia", 2203, ["cs"]], ["Slovakia", 2703, ["sk"]],
  ["Sweden", 2752, ["sv"]], ["Canada", 2124, ["en", "fr"]], ["Australia", 2036, ["en"]], ["India", 2356, ["en", "hi"]],
];
const LANGUAGE_NAMES = { en: "English", es: "Spanish", pl: "Polish", de: "German", fr: "French", it: "Italian",
  nl: "Dutch", cs: "Czech", sk: "Slovak", sv: "Swedish", hi: "Hindi" };
const country = $("#pgCountry"), language = $("#pgLanguage");
country.innerHTML = MARKETS.map(([name, code]) => `<option value="${code}">${name}</option>`).join("");
function fillLanguages() {
  const langs = MARKETS.find(([, code]) => String(code) === country.value)[2];
  language.innerHTML = langs.map((l) => `<option value="${l}">${LANGUAGE_NAMES[l]}</option>`).join("");
}
country.addEventListener("change", fillLanguages);
fillLanguages();
const marketName = () => country.selectedOptions[0].textContent;

const sourceMode = () => document.querySelector('input[name="source"]:checked').value;
document.querySelectorAll('input[name="source"]').forEach((el) => el.addEventListener("change", () => {
  $("#dfsFields").hidden = sourceMode() !== "dataforseo";
  $("#pasteFields").hidden = sourceMode() !== "paste";
  updateEstimate();
}));

// Low-cost OpenRouter models, measured on two real SERPs (English and Polish) in September 2026.
// cost = measured USD per query with reasoning switched off (grouping ten results does not need it,
// and with it Nemotron returned empty answers and Gemma took minutes).
const MODELS = [
  { id: "openai/gpt-6-luna", label: "GPT-6 Luna", cost: 0.0008, speed: "5-8 s" },
  { id: "deepseek/deepseek-v4.1-flash", label: "DeepSeek V4.1 Flash", cost: 0.0022, speed: "3-4 s" },
  { id: "nvidia/nemotron-3.5-lightning", label: "Nemotron 3.5 Lightning", cost: 0.0003, speed: "3-26 s" },
  { id: "google/gemma-4-26b-a4b-it", label: "Gemma 4 26B MoE", cost: 0.0006, speed: "4-9 s" },
  { id: "google/gemma-4-31b-it", label: "Gemma 4 31B", cost: 0.0006, speed: "30-40 s" },
  { id: "qwen/qwen3.8-flash", label: "Qwen 3.8 Flash", cost: 0.0009, speed: "18-23 s" },
  { id: "xiaomi/mimo-v2.6-flash", label: "MiMo V2.6 Flash", cost: 0.0007, speed: "26-34 s" },
];
const modelSelect = $("#pgModel");
modelSelect.innerHTML = MODELS.map((m) => `<option value="${m.id}">${m.label} - about $${m.cost.toFixed(4)}, ${m.speed}</option>`).join("");
const currentModel = () => MODELS.find((m) => m.id === modelSelect.value);
const currentModelLabel = (id) => (MODELS.find((m) => m.id === id) || { label: id }).label;

const PRICE = { serp: 0.002, page: 0.00015, traffic: 0.013, volume: 0.012 };
function updateEstimate() {
  const dfs = sourceMode() === "dataforseo";
  const pages = dfs && $("#pgPages").checked ? 10 * PRICE.page : 0;
  const traffic = dfs && $("#pgTraffic").checked ? PRICE.traffic : 0;
  const volume = dfs && $("#pgVolume").checked ? PRICE.volume : 0;
  const dfsCost = dfs ? PRICE.serp + pages + traffic + volume : 0;
  const total = dfsCost + currentModel().cost;
  $("#costEstimate").textContent = `This run, as set below: about $${total.toFixed(4)}` +
    (dfs ? ` (DataForSEO $${dfsCost.toFixed(4)}, model $${currentModel().cost.toFixed(4)})` : ` (model only)`) +
    `. A hundred runs: about $${(total * 100).toFixed(2)}.`;
}
["change", "input"].forEach((ev) => $("#playground").addEventListener(ev, updateEstimate));

// Keys: kept in memory; in localStorage only when the visitor ticks "remember".
const STORE = { openrouter: "intent-labeler-openrouter-key", dfsLogin: "intent-labeler-dfs-login", dfsPassword: "intent-labeler-dfs-password" };
const keyFields = { openrouter: $("#pgKey"), dfsLogin: $("#pgDfsLogin"), dfsPassword: $("#pgDfsPassword") };
try {
  let any = false;
  for (const [k, el] of Object.entries(keyFields)) {
    const v = localStorage.getItem(STORE[k]);
    if (v) { el.value = v; any = true; }
  }
  $("#pgRemember").checked = any;
} catch { /* storage blocked: nothing is remembered */ }
function saveKeys() {
  try {
    for (const [k, el] of Object.entries(keyFields)) {
      if ($("#pgRemember").checked && el.value) localStorage.setItem(STORE[k], el.value.trim());
      else localStorage.removeItem(STORE[k]);
    }
  } catch { /* storage blocked */ }
}

$("#pgLoad").addEventListener("click", async () => {
  const snap = await fetch("sample-snapshot.json").then((r) => r.json());
  $("#pgKeyword").value = snap.keyword;
  country.value = "2840"; fillLanguages(); language.value = "en";
  $("#pgResults").value = snap.results.map((r) => [r.title, r.url, r.description].join(" | ")).join("\n");
});

function parseResults(text) {
  return text.split("\n").map((l) => l.trim()).filter(Boolean).map((line, i) => {
    const [title = "", url = "", ...rest] = line.split("|").map((p) => p.trim());
    let domain = "";
    try { domain = new URL(url).hostname.replace(/^www\./, ""); } catch { /* not a URL */ }
    return { result_id: `r${String(i + 1).padStart(2, "0")}`, rank: i + 1, url, domain, title,
             description: rest.join(" | ").slice(0, 220), highlighted: [], digest: "" };
  });
}

// Actual spend of the current run, from the services' own answers (DataForSEO task.cost,
// OpenRouter usage.cost) - not an estimate.
const spend = { serp: 0, pages: 0, traffic: 0, volume: 0, model: 0 };
const resetSpend = () => Object.keys(spend).forEach((k) => (spend[k] = 0));
const usd = (v) => `$${v.toFixed(v < 0.01 ? 5 : 4)}`;

// DataForSEO straight from the browser (their API allows it: CORS *).
async function dataforseo(path, task, bucket) {
  const auth = btoa(`${keyFields.dfsLogin.value.trim()}:${keyFields.dfsPassword.value.trim()}`);
  const res = await fetch(`https://api.dataforseo.com/v3/${path}`, {
    method: "POST", headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/json" },
    body: JSON.stringify([task]), signal: AbortSignal.timeout(90000),
  }).catch((e) => { throw new Error(e.name === "TimeoutError" ? "DataForSEO did not answer within 90 seconds" : `cannot reach DataForSEO (${e.message})`); });
  const body = await res.json().catch(() => ({}));
  const t = body?.tasks?.[0];
  if (bucket) spend[bucket] += Number(t?.cost || body?.cost || 0);
  if (!res.ok || body.status_code !== 20000 || !t || t.status_code !== 20000) {
    throw new Error(`DataForSEO: ${t?.status_message || body?.status_message || res.status}`);
  }
  return t.result?.[0] || {};
}

async function fetchSerp(keyword) {
  const r = await dataforseo("serp/google/organic/live/advanced", {
    keyword, location_code: Number(country.value), language_code: language.value, device: "desktop", depth: 10,
  }, "serp");
  const features = { people_also_ask: [], related_searches: [], ai_overview: "", item_types: r.item_types || [] };
  const results = [];
  for (const item of r.items || []) {
    if (item.type === "organic" && results.length < 10) {
      results.push({ result_id: `r${String(results.length + 1).padStart(2, "0")}`, rank: item.rank_group,
        url: item.url, domain: (item.domain || "").replace(/^www\./, ""), title: item.title || "",
        description: (item.description || "").slice(0, 220), highlighted: (item.highlighted || []).slice(0, 4), digest: "" });
    } else if (item.type === "people_also_ask") {
      features.people_also_ask.push(...(item.items || []).map((q) => q.title).filter(Boolean));
    } else if (item.type === "related_searches") {
      features.related_searches.push(...(item.items || []).filter(Boolean));
    } else if (item.type === "ai_overview") {
      features.ai_overview = [item.text, ...(item.items || []).map((s) => `${s.title || ""} ${s.text || ""}`)].join(" ").slice(0, 4000);
    }
  }
  if (!results.length) throw new Error("DataForSEO returned no organic results for this query and market");
  return { results, features };
}

async function fetchTraffic(results) {
  // Unknown is not zero: a page with no known keywords gets etv null.
  const r = await dataforseo("dataforseo_labs/google/bulk_traffic_estimation/live", {
    targets: results.map((x) => x.url), location_code: Number(country.value), language_code: language.value, item_types: ["organic"],
  }, "traffic");
  const etv = {};
  for (const item of r.items || []) {
    const organic = item.metrics?.organic || {};
    etv[item.target] = organic.count ? Number(organic.etv || 0) : null;
  }
  results.forEach((x) => { x.etv = etv[x.url] ?? null; });
}

// Pages through DataForSEO OnPage content parsing: the browser cannot fetch other sites itself
// (CORS), DataForSEO can, and returns the page as markdown. Measured cost: $0.00015 per page.
const THIN_WORDS = 150;
const WORD = /[\p{L}\p{N}]+/gu;
function analyseMarkdown(md) {
  const lines = md.split("\n");
  const headings = [], paragraphs = [];
  const el = { tables: 0, ordered_lists: 0, unordered_lists: 0, images: 0, videos: 0 };
  let prev = "";
  for (const raw of lines) {
    const line = raw.trim();
    const kind = line.startsWith("|") ? "table" : /^\d+[.)]\s/.test(line) ? "ol" : /^[-*+]\s/.test(line) ? "ul" : "";
    if (kind && kind !== prev) el[{ table: "tables", ol: "ordered_lists", ul: "unordered_lists" }[kind]]++;
    prev = kind;
    el.images += (line.match(/!\[[^\]]*\]\(/g) || []).length;
    el.videos += (line.match(/(youtube\.com\/(watch|embed)|youtu\.be\/|vimeo\.com\/)/g) || []).length;
    if (line.startsWith("#")) headings.push(line.replace(/^#+\s*/, ""));
    else if (!kind && !line.startsWith(">") && (line.match(WORD) || []).length >= 8) paragraphs.push(line);
  }
  const text = md.replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1");
  const words = (text.match(WORD) || []).length;
  const parts = [];
  if (headings.length) parts.push("headings: " + headings.slice(0, 8).join("; "));
  if (paragraphs.length) parts.push("text: " + paragraphs.slice(0, 3).join(" "));
  return { words, chars: text.replace(/\s+/g, " ").trim().length, digest: parts.join(" | ").slice(0, 400), elements: el };
}

async function fetchPages(results, onProgress) {
  let done = 0;
  const one = async (r) => {
    try {
      const res = await dataforseo("on_page/content_parsing/live", { url: r.url, markdown_view: true }, "pages");
      const md = res.items?.[0]?.page_as_markdown || "";
      Object.assign(r, analyseMarkdown(md));
      r.fetch_status = r.words >= THIN_WORDS ? "ok" : "thin";
    } catch (e) {
      r.fetch_status = "error";
    }
    onProgress(++done);
  };
  const queue = [...results];
  await Promise.all(Array.from({ length: 5 }, async () => { while (queue.length) await one(queue.shift()); }));
  results.forEach((r) => { if (r.fetch_status !== "ok") r.digest = ""; });
}

// Search volume + monthly history (DataForSEO Labs keyword_overview: $0.012, 95 months).
async function fetchVolume(keyword) {
  const r = await dataforseo("dataforseo_labs/google/keyword_overview/live", {
    keywords: [keyword], location_code: Number(country.value), language_code: language.value, include_serp_info: false,
  }, "volume");
  const item = r.items?.[0];
  if (!item) return null;
  const info = item.keyword_info || {};
  const monthly = (info.monthly_searches || []).map((m) => ({ year: m.year, month: m.month, volume: m.search_volume }))
    .sort((a, b) => a.year - b.year || a.month - b.month);
  return { volume: info.search_volume, cpc: info.cpc, difficulty: item.keyword_properties?.keyword_difficulty, monthly, season: seasonality(monthly) };
}

// Same arithmetic as features/search_volume/seasonality.py.
function seasonality(monthly) {
  const known = monthly.filter((m) => m.volume != null);
  if (known.length < 12) return null;
  const byMonth = {};
  known.slice(-36).forEach((m) => (byMonth[m.month] ||= []).push(m.volume));
  const means = Object.fromEntries(Object.entries(byMonth).map(([k, v]) => [k, v.reduce((a, b) => a + b, 0) / v.length]));
  const overall = Object.values(means).reduce((a, b) => a + b, 0) / Object.keys(means).length;
  const profile = Object.fromEntries(Object.entries(means).map(([k, v]) => [k, v / overall]));
  const entries = Object.entries(profile);
  const peak = entries.reduce((a, b) => (b[1] > a[1] ? b : a));
  const low = entries.reduce((a, b) => (b[1] < a[1] ? b : a));
  const sum = (arr) => arr.reduce((a, m) => a + m.volume, 0);
  const prev = known.length >= 24 ? sum(known.slice(-24, -12)) : null;
  return { peak: +peak[0], low: +low[0], index: low[1] ? peak[1] / low[1] : null, yoy: prev ? sum(known.slice(-12)) / prev - 1 : null };
}

const MONTH_NAMES = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ");
function monthlyChart(monthly) {
  const data = monthly.slice(-36);
  const top = Math.max(...data.map((m) => m.volume || 0));
  if (!top) return "";
  return `<div class="month-bars" role="img" aria-label="Search volume per month, last ${data.length} months">${data.map((m) =>
    `<span title="${MONTH_NAMES[m.month - 1]} ${m.year}: ${(m.volume ?? 0).toLocaleString("en")}" style="height:${m.volume == null ? 0 : Math.max(2, 100 * m.volume / top)}%"></span>`).join("")}</div>
    <div class="month-axis"><span>${MONTH_NAMES[data[0].month - 1]} ${data[0].year}</span><span>${MONTH_NAMES[data.at(-1).month - 1]} ${data.at(-1).year}</span></div>`;
}

function validate(labels, ids) {
  if (!labels || !Array.isArray(labels.intents) || !labels.intents.length) throw new Error("the model returned no intents");
  const known = new Set(ids);
  const placed = new Set();
  for (const it of labels.intents) {
    it.result_ids = [...new Set((it.result_ids || []).map(String))];
    const unknown = it.result_ids.filter((id) => !known.has(id));
    if (unknown.length) throw new Error(`unknown result_ids ${unknown.join(", ")}`);
    it.result_ids.forEach((id) => placed.add(id));
  }
  const missing = ids.filter((id) => !placed.has(id));
  if (missing.length) labels.intents.push({ intent_id: "unassigned", title: "Unassigned results",
    searcher_goal: "the model did not place these results", form: "", result_ids: missing, fallback: true });
  return labels;
}

function measure(labels, results) {
  // Same rules as features/metrics: coverage unsplit, share and traffic split 1/k, unknown traffic left out.
  const k = {};
  labels.intents.forEach((it) => it.result_ids.forEach((id) => (k[id] = (k[id] || 0) + 1)));
  const byId = Object.fromEntries(results.map((r) => [r.result_id, r]));
  const known = results.filter((r) => r.etv != null);
  const trafficTotal = known.reduce((s, r) => s + r.etv, 0);
  return labels.intents.map((it) => ({
    ...it,
    coverage: it.result_ids.length / results.length,
    share: it.result_ids.reduce((s, id) => s + 1 / k[id], 0) / results.length,
    traffic: trafficTotal ? it.result_ids.reduce((s, id) => s + (byId[id].etv ?? 0) / k[id], 0) / trafficTotal : null,
    ranks: it.result_ids.map((id) => byId[id].rank).sort((a, b) => a - b),
    words: it.result_ids.map((id) => byId[id]).filter((r) => r.fetch_status === "ok").map((r) => r.words).sort((a, b) => a - b),
    elements: elementShare(it.result_ids.map((id) => byId[id]).filter((r) => r.fetch_status === "ok")),
  }));
}

const nearestRank = (sorted, p) => sorted.length ? sorted[Math.max(0, Math.min(sorted.length - 1, Math.ceil(p / 100 * sorted.length) - 1))] : null;
function elementShare(pages) {
  if (!pages.length) return null;
  const out = {};
  for (const key of ["tables", "ordered_lists", "unordered_lists", "images", "videos"]) {
    out[key] = pages.filter((p) => p.elements?.[key]).length / pages.length;
  }
  return out;
}

// Same guards as features/form_decision: no number without a sample.
function decide(rows) {
  const real = rows.filter((r) => !r.fallback);
  const top = [...real].sort((a, b) => b.share - a.share || (b.traffic ?? 0) - (a.traffic ?? 0))[0];
  const byTraffic = real.filter((r) => r.traffic != null).sort((a, b) => b.traffic - a.traffic)[0];
  const w = top?.words || [];
  let basis = "median of the dominant intent's pages";
  if (w.length < 3) basis = `not enough measured pages (${w.length} of at least 3)`;
  else if (w[w.length - 1] / w[0] > 50) basis = "lengths too far apart to average";
  const length = basis.startsWith("median") ? { p25: nearestRank(w, 25), p50: nearestRank(w, 50), p75: nearestRank(w, 75) } : null;
  const warnings = [];
  if (top && top.share < 0.4 && top.coverage < 0.5) warnings.push("No intent holds 40% of the results: the page must serve several intents, or the query is poorly chosen.");
  if (real.filter((r) => r.share >= 0.15).length >= 3) warnings.push("Three or more intents hold at least 15% each. Consider separate pages.");
  if (byTraffic && top && byTraffic !== top) warnings.push(`By result count "${top.title}" dominates, by traffic "${byTraffic.title}". Decide deliberately.`);
  return { top, length, basis, warnings };
}

let systemPrompt = null;
async function callModel({ key, model, payload, onAttempt = () => {} }) {
  systemPrompt ??= await fetch("prompt.md").then((r) => r.text());
  const user = `Read these results and return the JSON object defined by your instructions.\n\n${JSON.stringify(payload)}`;
  let lastError = null, lastRaw = "";
  for (let attempt = 0; attempt < 3; attempt++) {
    if (lastError) onAttempt(attempt + 1, `failed the contract (${lastError})`);
    const content = lastError
      ? `${user}\n\n<previous_invalid_response>\n${lastRaw.slice(0, 20000)}\n</previous_invalid_response>\nThat response failed the contract: ${lastError}. Return the complete corrected JSON object.`
      : user;
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: { "Authorization": `Bearer ${key}`, "Content-Type": "application/json",
                 "HTTP-Referer": location.origin, "X-Title": "Intent Labeler playground" },
      body: JSON.stringify({ model, max_tokens: 12000, reasoning: { enabled: false }, usage: { include: true },
        response_format: { type: "json_object" },
        messages: [{ role: "system", content: systemPrompt }, { role: "user", content }] }),
      signal: AbortSignal.timeout(180000),
    }).catch((e) => { throw new Error(e.name === "TimeoutError" ? "the model did not answer within 3 minutes - try a faster one" : `cannot reach OpenRouter (${e.message})`); });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body?.error?.message || `OpenRouter answered ${res.status}`);
    spend.model += Number(body?.usage?.cost || 0);
    lastRaw = body?.choices?.[0]?.message?.content || "";
    try {
      return validate(JSON.parse(lastRaw.replace(/^```(?:json)?\s*|\s*```$/g, "")), payload.results.map((r) => r.result_id));
    } catch (e) { lastError = e.message; }
  }
  throw new Error(`the model failed the JSON contract three times: ${lastError}`);
}

// ------------------------------------------------------------- sharing ----
const slugify = (s) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function publicRecord(run) {
  // Only what is safe to publish. Never keys, never anything typed into key fields.
  return {
    schema: "intent-labeler/community/1",
    keyword: run.keyword, market: run.market, location_code: run.location, language: run.language,
    source: run.source, model: run.model, date: new Date().toISOString().slice(0, 10), shared_by: "",
    summary: run.labels.summary || "", expected_genre: run.labels.expected_genre || "",
    results: run.results.map((r) => ({ id: r.result_id, rank: r.rank, url: r.url, title: r.title })),
    intents: run.rows.map((r) => ({ title: r.title, searcher_goal: r.searcher_goal || "", form: r.form || "",
      result_ids: r.result_ids, coverage: +r.coverage.toFixed(4), share: +r.share.toFixed(4),
      traffic_share: r.traffic == null ? null : +r.traffic.toFixed(4) })),
  };
}

function shareBox(run) {
  const record = publicRecord(run);
  const json = JSON.stringify(record, null, 2);
  const name = `${slugify(record.market)}-${slugify(record.keyword)}-${record.date}.json`;
  const url = `https://github.com/romek-rozen/intent-labeler/new/main/community?filename=${encodeURIComponent(name)}&value=${encodeURIComponent(json)}`;
  const blob = URL.createObjectURL(new Blob([json], { type: "application/json" }));
  const tooLong = url.length > 7500;
  return `<div class="share-box">
    <h3>Contribute this result</h3>
    <p>This opens GitHub with the file <code>community/${esc(name)}</code> filled in. GitHub forks the repository and opens a pull request for you. You can add your name in <code>shared_by</code> before you submit. The file holds the query, market, results and intents - no keys. Contributions are collected in the repository, not published on this page.</p>
    ${tooLong ? `<p class="hint">This result is too long for a link. Download the file and upload it at the same address.</p>` :
      `<a class="btn primary" href="${url}" target="_blank" rel="noopener">Contribute on GitHub</a>`}
    <a class="btn" href="${blob}" download="${esc(name)}">Download the JSON</a>
  </div>`;
}

function covered(rows, results, name) {
  // page types / heading themes / questions: how many results point to each, like features/metrics.
  const rank = Object.fromEntries(results.map((r) => [r.result_id, r.rank]));
  return (rows || []).filter((r) => r[name]).map((r) => {
    const ids = [...new Set((r.result_ids || []).filter((id) => id in rank))];
    return { ...r, count: ids.length, ranks: ids.map((id) => rank[id]).sort((a, b) => a - b) };
  }).sort((a, b) => b.count - a.count);
}

function render(run) {
  const { keyword, results, labels, rows } = run;
  const out = $("#pgOutput");
  const { top, length, basis, warnings } = decide(rows);
  const fits = labels.article_fits || {};
  if (fits.value === false) warnings.push(`This query may not want an article: ${fits.reason}`);
  const byId = Object.fromEntries(results.map((r) => [r.result_id, r]));
  const hasTraffic = rows.some((r) => r.traffic != null);
  const measured = results.filter((r) => r.fetch_status === "ok").length;
  const EL = { tables: "table", ordered_lists: "numbered list", unordered_lists: "list", images: "images", videos: "video" };
  const d = run.demand;
  const pageTypes = covered(labels.page_types, results, "page_type");
  const themes = covered(labels.heading_themes, results, "theme");
  const colorOf = (r, i) => (r.fallback ? "var(--rule)" : color(i));

  const facts = [
    [top?.title || "-", `dominant intent, ${pct(top?.coverage)} of results`],
    [top?.form || "-", "form that answers it"],
    [length ? `${length.p50.toLocaleString("en")} words` : "no number", length ? `reference length, middle half ${length.p25}-${length.p75}` : `reference length: ${basis}`],
    [d?.volume != null ? d.volume.toLocaleString("en") : "-", d?.season ? `searches a month, seasonality ${d.season.index?.toFixed(2)}` : "searches a month"],
    [pageTypes[0]?.page_type || "-", "most common page type"],
    [labels.expected_genre && length ? labels.expected_genre : "withheld", "genre the results expect"],
  ];

  const intentCard = (r, i) => {
    const pages = r.result_ids.map((id) => byId[id]).filter(Boolean).sort((a, b) => a.rank - b.rank);
    return `<article class="group pg-group" style="--c:${colorOf(r, i)}">
      <h4>${esc(r.title)}${r.intent_type ? ` <span class="tag">${esc(r.intent_type)}</span>` : ""}</h4>
      <p class="goal">${esc(r.searcher_goal || "")}</p>
      <p class="form">Form: <b>${esc(r.form || "-")}</b></p>
      ${r.evidence ? `<p class="evidence">Why: ${esc(r.evidence)}</p>` : ""}
      <div class="nums"><span><b>${pct(r.coverage)}</b> of results</span><span><b>${pct(r.share)}</b> share</span>${hasTraffic ? `<span><b>${pct(r.traffic)}</b> of traffic</span>` : ""}${r.words.length ? `<span><b>${nearestRank(r.words, 50).toLocaleString("en")}</b> median words</span>` : ""}</div>
      <div class="rows">${pages.map((p) => `<a class="row" href="${esc(p.url)}" rel="noopener" target="_blank"><span class="rank">${p.rank}</span>
        <span><span class="t">${esc(p.title || p.url)}</span><span class="d">${esc(p.domain)}${p.fetch_status ? `, ${p.fetch_status === "ok" ? `${p.words.toLocaleString("en")} words` : p.fetch_status}` : ""}${p.etv != null ? `, ~${Math.round(p.etv).toLocaleString("en")} visits/month` : ""}</span></span></a>`).join("")}</div>
    </article>`;
  };

  const pills = (items, label) => items.length ? items.map((x) => `<span class="tag">${esc(x[label])}${x.count != null ? ` <b>${x.count}</b>` : ""}</span>`).join("") : `<span class="hint">-</span>`;

  out.hidden = false;
  out.innerHTML = `
    <header class="pg-head">
      <h3>${esc(keyword)}</h3>
      <span class="tags"><span class="tag">Google ${esc(run.market)}</span><span class="tag">${results.length} results</span><span class="tag">${measured} pages read</span><span class="tag">${esc(currentModelLabel(run.model))}</span></span>
    </header>
    <p class="pg-summary">${esc(labels.summary || "")}</p>

    <div class="fact-grid">${facts.map(([v, k]) => `<div class="fact"><b>${esc(v)}</b><span>${esc(k)}</span></div>`).join("")}</div>
    ${warnings.length ? `<ul class="warn-list">${warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>` : ""}

    <h4 class="pg-h">How the results divide</h4>
    <div class="bars">${rows.map((r, i) => `
      <div class="bar" style="--c:${colorOf(r, i)}; --w:${(r.share * 100).toFixed(1)}%">
        <span class="name">${esc(r.title)}</span>
        <span class="track"><span class="fill"></span><span class="val">${pct(r.share)}</span></span>
      </div>`).join("")}</div>

    <h4 class="pg-h">Intents</h4>
    <div class="pg-groups">${rows.map(intentCard).join("")}</div>

    ${d ? `<h4 class="pg-h">Search demand</h4><div class="demand"><p><b>${(d.volume ?? 0).toLocaleString("en")}</b> searches a month. CPC ${d.cpc ?? "-"}, keyword difficulty ${d.difficulty ?? "-"}${d.season ? `. Peak in ${MONTH_NAMES[d.season.peak - 1]}, low in ${MONTH_NAMES[d.season.low - 1]}, seasonality index ${d.season.index?.toFixed(2)}${d.season.yoy != null ? `; last 12 months ${d.season.yoy >= 0 ? "+" : ""}${Math.round(d.season.yoy * 100)}% on the year before` : ""}` : ""}.</p>${monthlyChart(d.monthly)}</div>` : ""}

    ${rows.some((r) => r.elements) ? `<h4 class="pg-h">Content form on the pages</h4>
    <div class="table-wrap"><table><tr><th>Intent</th>${Object.values(EL).map((l) => `<th>${l}</th>`).join("")}</tr>
      ${rows.filter((r) => r.elements).map((r) => `<tr><td>${esc(r.title)}</td>${Object.keys(EL).map((k) => `<td>${pct(r.elements[k])}</td>`).join("")}</tr>`).join("")}</table></div>` : ""}

    <div class="two-col">
      <section><h4 class="pg-h">What helps</h4><ul class="plain">${(labels.useful_elements || []).map((e) => `<li><b>${esc(e.element)}</b> - ${esc(e.job || "")}</li>`).join("") || "<li>-</li>"}</ul></section>
      <section><h4 class="pg-h">What to avoid</h4><ul class="plain">${(labels.avoid || []).map((e) => `<li><b>${esc(e.element)}</b> - ${esc(e.reason || "")}</li>`).join("") || "<li>-</li>"}</ul></section>
    </div>

    <div class="two-col">
      <section><h4 class="pg-h">Page types</h4><span class="tags">${pills(pageTypes, "page_type")}</span></section>
      <section><h4 class="pg-h">Heading themes</h4><span class="tags">${pills(themes, "theme")}</span></section>
    </div>

    <h4 class="pg-h">Reader questions</h4>
    <ul class="plain">${(labels.reader_questions || []).map((q) => `<li>${esc(q.question)} <span class="tag">${esc(q.source)}</span></li>`).join("") || "<li>-</li>"}</ul>

    <div class="two-col">
      <section><h4 class="pg-h">Brands in the results</h4><span class="tags">${(labels.competitor_brands || []).map((b) => `<span class="tag">${esc(b)}</span>`).join("") || `<span class="hint">-</span>`}</span></section>
      <section><h4 class="pg-h">AI Overview</h4><p>${labels.ai_overview_signal?.present ? "Present." : "Not shown for this query."} ${esc(labels.ai_overview_signal?.interpretation || "")}</p></section>
    </div>

    <details class="raw"><summary>Raw JSON from the model</summary><pre>${esc(JSON.stringify(labels, null, 2))}</pre></details>
    ${run.visibility === "public" ? shareBox(run) : `<p class="hint" style="margin-top:20px">Private run: nothing left your browser except the calls to DataForSEO and OpenRouter.</p>`}`;
}

// Live progress: a list of steps with state and a ticking clock, so a slow model never looks stuck.
function progress(steps) {
  const el = $("#pgProgress");
  const state = steps.map((label) => ({ label, status: "waiting", detail: "", start: 0, end: 0 }));
  const secs = (ms) => `${(ms / 1000).toFixed(0)} s`;
  const draw = () => {
    el.hidden = false;
    el.innerHTML = state.map((s) => {
      const time = s.status === "running" ? secs(Date.now() - s.start) : s.status === "done" ? secs(s.end - s.start) : "";
      return `<li class="${s.status}"><span class="label">${esc(s.label)}</span>` +
        `<span class="detail">${esc(s.detail)}${time ? ` <span class="time">${time}</span>` : ""}</span></li>`;
    }).join("");
  };
  const timer = setInterval(draw, 1000);
  draw();
  return {
    start(i, detail = "") { Object.assign(state[i], { status: "running", start: Date.now(), detail }); draw(); },
    detail(i, detail) { state[i].detail = detail; draw(); },
    done(i, detail = "") { Object.assign(state[i], { status: "done", end: Date.now(), detail: detail || state[i].detail }); draw(); },
    skip(i, detail) { Object.assign(state[i], { status: "skipped", detail }); draw(); },
    fail(detail) {
      const i = state.findIndex((s) => s.status === "running");
      if (i >= 0) Object.assign(state[i], { status: "failed", end: Date.now(), detail });
      draw();
    },
    stop() { clearInterval(timer); draw(); },
  };
}

$("#playground").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = $("#pgStatus");
  const fail = (msg) => { status.textContent = msg; status.classList.add("error"); };
  status.classList.remove("error");
  const keyword = $("#pgKeyword").value.trim();
  const mode = sourceMode();
  if (mode === "dataforseo" && (!keyFields.dfsLogin.value.trim() || !keyFields.dfsPassword.value.trim())) {
    return fail("Enter your DataForSEO login and API password, or switch to pasting results.");
  }
  saveKeys();
  resetSpend();
  let steps;
  $("#pgRun").disabled = true;
  $("#pgOutput").hidden = true;
  const dfsMode = mode === "dataforseo";
  const readPages = dfsMode && $("#pgPages").checked;
  const wantTraffic = dfsMode && $("#pgTraffic").checked;
  const model = currentModel();
  steps = progress([
    dfsMode ? `Fetch Google's top ten in ${marketName()}` : "Read the pasted results",
    "Read the pages",
    "Estimate traffic per URL",
    "Search volume and seasonality",
    `Group the results with ${model.label}`,
    "Count shares and lengths",
  ]);
  status.textContent = "";
  try {
    let results, features = { people_also_ask: [], related_searches: [], ai_overview: "", item_types: [] };
    steps.start(0, dfsMode ? "DataForSEO usually answers in about 5 seconds" : "");
    if (dfsMode) {
      ({ results, features } = await fetchSerp(keyword));
    } else {
      results = parseResults($("#pgResults").value);
      if (results.length < 2) throw new Error("add at least two results, one per line");
    }
    steps.done(0, `${results.length} results${dfsMode ? `, ${usd(spend.serp)}` : ""}`);

    if (readPages) {
      steps.start(1, `0 of ${results.length}`);
      await fetchPages(results, (n) => steps.detail(1, `${n} of ${results.length}`));
      const ok = results.filter((r) => r.fetch_status === "ok").length;
      steps.done(1, `${ok} of ${results.length} readable${ok < results.length ? ", the rest are blocked or too short" : ""}, ${usd(spend.pages)}`);
    } else {
      steps.skip(1, dfsMode ? "switched off" : "not available when pasting results");
    }

    if (wantTraffic) {
      steps.start(2, "one DataForSEO Labs call");
      await fetchTraffic(results);
      steps.done(2, `known for ${results.filter((r) => r.etv != null).length} of ${results.length}, ${usd(spend.traffic)}`);
    } else {
      steps.skip(2, "switched off");
    }

    const payload = { source: "serp", keyword, language: language.value, brief: "", serp_features: features, results };
    let demand = null;
    if (dfsMode && $("#pgVolume").checked) {
      steps.start(3, "one DataForSEO Labs call");
      demand = await fetchVolume(keyword);
      steps.done(3, demand ? `${(demand.volume ?? 0).toLocaleString("en")} per month, ${usd(spend.volume)}` : `no data for this keyword, ${usd(spend.volume)}`);
    } else {
      steps.skip(3, dfsMode ? "switched off" : "not available when pasting results");
    }
    steps.start(4, `usually ${model.speed}`);
    const labels = await callModel({ key: keyFields.openrouter.value.trim(), model: model.id,
      payload: { ...payload, results: payload.results.map(({ words, chars, elements, etv, fetch_status, ...r }) => r) },
      onAttempt: (n, why) => steps.detail(4, `attempt ${n} of 3: the previous answer ${why}; sent back for correction`) });
    steps.done(4, `${labels.intents.filter((i) => !i.fallback).length} intents, ${usd(spend.model)}`);

    steps.start(5);
    const run = { keyword, results, labels, rows: measure(labels, results), market: marketName(),
      location: Number(country.value), language: language.value, source: mode, model: model.id,
      visibility: document.querySelector('input[name="visibility"]:checked').value, demand };
    render(run);
    steps.done(5, "done in your browser");
    const dfsTotal = spend.serp + spend.pages + spend.traffic + spend.volume;
    status.textContent = `Finished. This run cost ${usd(dfsTotal + spend.model)}: DataForSEO ${usd(dfsTotal)}` +
      (dfsMode ? ` (SERP ${usd(spend.serp)}, pages ${usd(spend.pages)}, volume ${usd(spend.volume)}, traffic ${usd(spend.traffic)})` : "") +
      `, OpenRouter ${usd(spend.model)} - as reported by the services and billed to your accounts.`;
    $("#pgOutput").scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  } catch (e) {
    steps?.fail(e.message);
    const spent = spend.serp + spend.pages + spend.traffic + spend.volume + spend.model;
    if (spent) e.message += `. Spent before the error: ${usd(spent)}`;
    fail(`Could not finish: ${e.message}. Check the keys, the query and the market, then try again.`);
  } finally {
    steps?.stop();
    $("#pgRun").disabled = false;
  }
});
updateEstimate();

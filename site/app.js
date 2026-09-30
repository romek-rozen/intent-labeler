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
serp.classList.add("list");

function flip(toGrouped) {
  const from = {};
  serp.querySelectorAll(toGrouped ? ".results .row" : ".groups .row").forEach((el) => {
    from[el.dataset.id] = el.getBoundingClientRect();
  });
  serp.classList.toggle("grouped", toGrouped);
  serp.classList.toggle("list", !toGrouped);
  serp.classList.remove("settled");
  const targets = serp.querySelectorAll(toGrouped ? ".groups .row" : ".results .row");
  if (!reduced) {
    targets.forEach((el) => {
      const a = from[el.dataset.id];
      if (!a) return;
      const b = el.getBoundingClientRect();
      el.animate([{ transform: `translate(${a.left - b.left}px, ${a.top - b.top}px)` }, { transform: "none" }],
        { duration: 700, easing: "cubic-bezier(.2,.7,.2,1)" });
    });
  }
  setTimeout(() => serp.classList.add("settled"), reduced ? 0 : 50);
  $("#sortToggle").textContent = toGrouped ? "Show as search results" : "Sort into intents";
}
let grouped = false;
$("#sortToggle").addEventListener("click", () => flip((grouped = !grouped)));
if (!reduced) {
  // One orchestrated moment: the page opens on the raw results, then sorts them once.
  setTimeout(() => { if (!grouped) flip((grouped = true)); }, 1400);
}

// ------------------------------------------------------------ examples ----
$("#exampleList").innerHTML = data.examples.map((ex) => `
  <a class="example" href="examples/${ex.slug}.html">
    <span class="q">${esc(ex.keyword)}</span>
    <span class="market">Google ${esc(ex.market)}, ${ex.results} results</span>
    <span class="stack" aria-hidden="true">${ex.intents.map((it, i) => `<span style="flex:${it.share};background:${color(i)}"></span>`).join("")}</span>
    <p class="dom"><b>${esc(ex.dominant)}</b><br>${esc(ex.form)}</p>
    <p class="meta">${ex.length ? `Reference length ${ex.length} words` : `No reference length (${esc(ex.length_basis.replaceAll("_", " "))})`}</p>
    <span>${ex.warnings.map((w) => `<span class="tag">${esc(w.replaceAll("_", " "))}</span>`).join("")}</span>
  </a>`).join("");

// ---------------------------------------------------------- community ----
if (data.community?.length) {
  $("#community").hidden = false;
  $("#navCommunity").hidden = false;
  $("#communityList").innerHTML = data.community.map((c) => `
    <article class="example">
      <span class="q">${esc(c.keyword)}</span>
      <span class="market">Google ${esc(c.market)}, ${c.results.length} results, ${esc(c.date)}</span>
      <span class="stack" aria-hidden="true">${c.intents.map((it, i) => `<span style="flex:${it.share};background:${color(i)}"></span>`).join("")}</span>
      <p class="dom">${c.intents.map((it) => `<b>${esc(it.title)}</b> ${pct(it.share)}<br>`).join("")}</p>
      <p class="meta">Model ${esc(c.model)}${c.shared_by ? `, shared by ${esc(c.shared_by)}` : ""}</p>
    </article>`).join("");
}

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

const PRICE = { serp: 0.002, page: 0.00015, traffic: 0.013 };
function updateEstimate() {
  const dfs = sourceMode() === "dataforseo";
  const pages = dfs && $("#pgPages").checked ? 10 * PRICE.page : 0;
  const traffic = dfs && $("#pgTraffic").checked ? PRICE.traffic : 0;
  const dfsCost = dfs ? PRICE.serp + pages + traffic : 0;
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

// DataForSEO straight from the browser (their API allows it: CORS *).
async function dataforseo(path, task) {
  const auth = btoa(`${keyFields.dfsLogin.value.trim()}:${keyFields.dfsPassword.value.trim()}`);
  const res = await fetch(`https://api.dataforseo.com/v3/${path}`, {
    method: "POST", headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/json" },
    body: JSON.stringify([task]),
  });
  const body = await res.json().catch(() => ({}));
  const t = body?.tasks?.[0];
  if (!res.ok || body.status_code !== 20000 || !t || t.status_code !== 20000) {
    throw new Error(`DataForSEO: ${t?.status_message || body?.status_message || res.status}`);
  }
  return t.result?.[0] || {};
}

async function fetchSerp(keyword) {
  const r = await dataforseo("serp/google/organic/live/advanced", {
    keyword, location_code: Number(country.value), language_code: language.value, device: "desktop", depth: 10,
  });
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
  });
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
      const res = await dataforseo("on_page/content_parsing/live", { url: r.url, markdown_view: true });
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
async function callModel({ key, model, payload }) {
  systemPrompt ??= await fetch("prompt.md").then((r) => r.text());
  const user = `Read these results and return the JSON object defined by your instructions.\n\n${JSON.stringify(payload)}`;
  let lastError = null, lastRaw = "";
  for (let attempt = 0; attempt < 3; attempt++) {
    const content = lastError
      ? `${user}\n\n<previous_invalid_response>\n${lastRaw.slice(0, 20000)}\n</previous_invalid_response>\nThat response failed the contract: ${lastError}. Return the complete corrected JSON object.`
      : user;
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: { "Authorization": `Bearer ${key}`, "Content-Type": "application/json",
                 "HTTP-Referer": location.origin, "X-Title": "Intent Labeler playground" },
      body: JSON.stringify({ model, max_tokens: 12000, reasoning: { enabled: false },
        response_format: { type: "json_object" },
        messages: [{ role: "system", content: systemPrompt }, { role: "user", content }] }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body?.error?.message || `OpenRouter answered ${res.status}`);
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
    <h3>Propose this result for the gallery</h3>
    <p>This opens GitHub with the file <code>community/${esc(name)}</code> filled in. GitHub will fork the repository and open a pull request for you. You can add your name in <code>shared_by</code> before you submit. The file contains the query, market, results and intents - no keys.</p>
    ${tooLong ? `<p class="hint">This result is too long for a link. Download the file and upload it at the same address.</p>` :
      `<a class="btn primary" href="${url}" target="_blank" rel="noopener">Propose it for the gallery</a>`}
    <a class="btn" href="${blob}" download="${esc(name)}">Download the JSON</a>
  </div>`;
}

function render(run) {
  const { keyword, results, labels, rows } = run;
  const out = $("#pgOutput");
  const { top, length, basis, warnings } = decide(rows);
  const fits = labels.article_fits || {};
  if (fits.value === false) warnings.push(`This query may not want an article: ${fits.reason}`);
  const hasTraffic = rows.some((r) => r.traffic != null);
  const measured = results.filter((r) => r.fetch_status === "ok").length;
  const EL = { tables: "table", ordered_lists: "numbered list", unordered_lists: "list", images: "images", videos: "video" };
  const withElements = rows.filter((r) => r.elements);
  out.hidden = false;
  out.innerHTML = `
    <h3>${esc(keyword)} <span class="hint">Google ${esc(run.market)}, ${results.length} results</span></h3>
    <p class="pg-summary">${esc(labels.summary || "")}</p>
    <p>Dominant intent: <b>${esc(top?.title)}</b>, answered by <b>${esc(top?.form || "-")}</b>.
       ${labels.expected_genre && length ? `Expected genre: ${esc(labels.expected_genre)}.` : ""}</p>
    <p>${measured ? (length ? `Reference length: <b>${length.p50} words</b> (middle half ${length.p25}-${length.p75}), from the dominant intent's pages.` : `No reference length: ${esc(basis)}.`) + ` ${measured} of ${results.length} pages were readable.` : "Pages were not read, so there is no length measurement."}</p>
    ${warnings.length ? `<ul class="warn-list">${warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>` : ""}
    <div class="bars">${rows.map((r, i) => `
      <div class="bar" style="--c:${r.fallback ? "var(--rule)" : color(i)}; --w:${(r.share * 100).toFixed(1)}%">
        <span class="name">${esc(r.title)}<small>${esc(r.form || "")}</small></span>
        <span class="track"><span class="fill" style="width:var(--w)"></span><span class="val">${pct(r.share)}</span></span>
      </div>`).join("")}</div>
    <table><tr><th>Intent</th><th>Coverage</th><th>Share</th>${hasTraffic ? "<th>Traffic</th>" : ""}<th>Ranks</th><th>Searcher goal</th></tr>
      ${rows.map((r, i) => `<tr><td><span class="sw" style="--c:${r.fallback ? "var(--rule)" : color(i)}"></span>${esc(r.title)}</td>
        <td>${pct(r.coverage)}</td><td>${pct(r.share)}</td>${hasTraffic ? `<td>${pct(r.traffic)}</td>` : ""}<td>${r.ranks.join(", ")}</td><td>${esc(r.searcher_goal)}</td></tr>`).join("")}
    </table>
    ${withElements.length ? `<h3 style="margin-top:24px">Content form on the pages</h3>
    <table><tr><th>Intent</th>${Object.values(EL).map((l) => `<th>${l}</th>`).join("")}<th>Median words</th></tr>
      ${withElements.map((r) => `<tr><td>${esc(r.title)}</td>${Object.keys(EL).map((k) => `<td>${pct(r.elements[k])}</td>`).join("")}<td>${nearestRank(r.words, 50) ?? "-"}</td></tr>`).join("")}</table>` : ""}
    <h3 style="margin-top:24px">Results</h3>
    <table class="results-list">${results.map((r) => `<tr><td>${r.rank}</td><td><a href="${esc(r.url)}" rel="noopener">${esc(r.title || r.url)}</a><br><span class="hint">${esc(r.domain)}${r.fetch_status ? `, ${r.fetch_status === "ok" ? `${r.words} words` : r.fetch_status}` : ""}</span></td>
      <td>${esc(rows.filter((x) => x.result_ids.includes(r.result_id)).map((x) => x.title).join("; "))}</td></tr>`).join("")}</table>
    ${(labels.reader_questions || []).length ? `<h3 style="margin-top:24px">Reader questions</h3><ul>${labels.reader_questions.map((q) => `<li>${esc(q.question)}</li>`).join("")}</ul>` : ""}
    ${run.visibility === "public" ? shareBox(run) : `<p class="hint" style="margin-top:20px">Private run: nothing was published. Choose "Public" before running to propose it for the gallery.</p>`}`;
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
  $("#pgRun").disabled = true;
  try {
    let results, features = { people_also_ask: [], related_searches: [], ai_overview: "", item_types: [] };
    if (mode === "dataforseo") {
      status.textContent = `Fetching Google's top ten for "${keyword}" in ${marketName()}...`;
      ({ results, features } = await fetchSerp(keyword));
      if ($("#pgPages").checked) {
        status.textContent = "Reading the pages through DataForSEO...";
        await fetchPages(results, (n) => { status.textContent = `Reading the pages through DataForSEO: ${n} of ${results.length}`; });
      }
      if ($("#pgTraffic").checked) {
        status.textContent = "Estimating traffic per URL...";
        await fetchTraffic(results);
      }
    } else {
      results = parseResults($("#pgResults").value);
      if (results.length < 2) throw new Error("add at least two results, one per line");
    }
    const payload = { source: "serp", keyword, language: language.value, brief: "", serp_features: features, results };
    status.textContent = `Asking ${currentModel().label} to group ${results.length} results. This usually takes a few seconds; slower models can take a minute.`;
    const labels = await callModel({ key: keyFields.openrouter.value.trim(), model: currentModel().id, payload: { ...payload, results: payload.results.map(({ words, chars, elements, etv, fetch_status, ...r }) => r) } });
    const run = { keyword, results, labels, rows: measure(labels, results), market: marketName(),
      location: Number(country.value), language: language.value, source: mode, model: currentModel().id,
      visibility: document.querySelector('input[name="visibility"]:checked').value };
    status.textContent = "Done. The groups come from the model; every percentage below was computed in your browser.";
    render(run);
  } catch (e) {
    fail(`Could not finish: ${e.message}. Check the keys, the query and the market, then try again.`);
  } finally {
    $("#pgRun").disabled = false;
  }
});

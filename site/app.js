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
}));

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
  }));
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
      body: JSON.stringify({ model, max_tokens: 8000, reasoning: { effort: "low" },
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
  const top = [...rows].filter((r) => !r.fallback).sort((a, b) => b.share - a.share)[0];
  const fits = labels.article_fits || {};
  const hasTraffic = rows.some((r) => r.traffic != null);
  out.hidden = false;
  out.innerHTML = `
    <h3>${esc(keyword)} <span class="hint">Google ${esc(run.market)}, ${results.length} results</span></h3>
    <p class="pg-summary">${esc(labels.summary || "")}</p>
    <p>Dominant intent: <b>${esc(top?.title)}</b>, answered by <b>${esc(top?.form || "-")}</b>.
       ${labels.expected_genre ? `Expected genre: ${esc(labels.expected_genre)}.` : ""}
       ${fits.value === false ? `<br><b>This query may not want an article:</b> ${esc(fits.reason)}` : ""}</p>
    <div class="bars">${rows.map((r, i) => `
      <div class="bar" style="--c:${r.fallback ? "var(--rule)" : color(i)}; --w:${(r.share * 100).toFixed(1)}%">
        <span class="name">${esc(r.title)}<small>${esc(r.form || "")}</small></span>
        <span class="track"><span class="fill" style="width:var(--w)"></span><span class="val">${pct(r.share)}</span></span>
      </div>`).join("")}</div>
    <table><tr><th>Intent</th><th>Coverage</th><th>Share</th>${hasTraffic ? "<th>Traffic</th>" : ""}<th>Ranks</th><th>Searcher goal</th></tr>
      ${rows.map((r, i) => `<tr><td><span class="sw" style="--c:${r.fallback ? "var(--rule)" : color(i)}"></span>${esc(r.title)}</td>
        <td>${pct(r.coverage)}</td><td>${pct(r.share)}</td>${hasTraffic ? `<td>${pct(r.traffic)}</td>` : ""}<td>${r.ranks.join(", ")}</td><td>${esc(r.searcher_goal)}</td></tr>`).join("")}
    </table>
    <h3 style="margin-top:24px">Results</h3>
    <table class="results-list">${results.map((r) => `<tr><td>${r.rank}</td><td><a href="${esc(r.url)}" rel="noopener">${esc(r.title || r.url)}</a><br><span class="hint">${esc(r.domain)}</span></td>
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
      if ($("#pgTraffic").checked) {
        status.textContent = "Estimating traffic per URL...";
        await fetchTraffic(results);
      }
    } else {
      results = parseResults($("#pgResults").value);
      if (results.length < 2) throw new Error("add at least two results, one per line");
    }
    const payload = { source: "serp", keyword, language: language.value, brief: "", serp_features: features, results };
    status.textContent = `Asking ${$("#pgModel").value} to group ${results.length} results. This usually takes a few seconds; slower models can take a minute.`;
    const labels = await callModel({ key: keyFields.openrouter.value.trim(), model: $("#pgModel").value.trim(), payload });
    const run = { keyword, results, labels, rows: measure(labels, results), market: marketName(),
      location: Number(country.value), language: language.value, source: mode, model: $("#pgModel").value.trim(),
      visibility: document.querySelector('input[name="visibility"]:checked').value };
    status.textContent = "Done. The groups come from the model; every percentage below was computed in your browser.";
    render(run);
  } catch (e) {
    fail(`Could not finish: ${e.message}. Check the keys, the query and the market, then try again.`);
  } finally {
    $("#pgRun").disabled = false;
  }
});

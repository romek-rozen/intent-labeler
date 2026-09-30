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
    <span class="market">Google ${ex.language === "pl" ? "Poland" : "United States"}, ${ex.results} results</span>
    <span class="stack" aria-hidden="true">${ex.intents.map((it, i) => `<span style="flex:${it.share};background:${color(i)}"></span>`).join("")}</span>
    <p class="dom"><b>${esc(ex.dominant)}</b><br>${esc(ex.form)}</p>
    <p class="meta">${ex.length ? `Reference length ${ex.length} words` : `No reference length (${esc(ex.length_basis.replaceAll("_", " "))})`}</p>
    <span>${ex.warnings.map((w) => `<span class="tag">${esc(w.replaceAll("_", " "))}</span>`).join("")}</span>
  </a>`).join("");

// ---------------------------------------------------------- playground ----
const KEY_STORE = "intent-labeler-openrouter-key";
const keyInput = $("#pgKey");
try {
  const saved = localStorage.getItem(KEY_STORE);
  if (saved) { keyInput.value = saved; $("#pgRemember").checked = true; }
} catch { /* storage blocked: the key simply is not remembered */ }

$("#pgLoad").addEventListener("click", async () => {
  const snap = await fetch("sample-snapshot.json").then((r) => r.json());
  $("#pgKeyword").value = snap.keyword;
  $("#pgLanguage").value = snap.language;
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
  // Same rules as features/metrics: coverage unsplit, share split 1/k.
  const k = {};
  labels.intents.forEach((it) => it.result_ids.forEach((id) => (k[id] = (k[id] || 0) + 1)));
  const rank = Object.fromEntries(results.map((r) => [r.result_id, r.rank]));
  return labels.intents.map((it) => ({
    ...it,
    coverage: it.result_ids.length / results.length,
    share: it.result_ids.reduce((s, id) => s + 1 / k[id], 0) / results.length,
    ranks: it.result_ids.map((id) => rank[id]).sort((a, b) => a - b),
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

function render(keyword, results, labels) {
  const rows = measure(labels, results);
  const out = $("#pgOutput");
  const top = [...rows].filter((r) => !r.fallback).sort((a, b) => b.share - a.share)[0];
  const fits = labels.article_fits || {};
  out.hidden = false;
  out.innerHTML = `
    <h3>${esc(keyword)}</h3>
    <p class="pg-summary">${esc(labels.summary || "")}</p>
    <p>Dominant intent: <b>${esc(top?.title)}</b>, answered by <b>${esc(top?.form || "-")}</b>.
       ${labels.expected_genre ? `Expected genre: ${esc(labels.expected_genre)}.` : ""}
       ${fits.value === false ? `<br><b>This query may not want an article:</b> ${esc(fits.reason)}` : ""}</p>
    <div class="bars">${rows.map((r, i) => `
      <div class="bar" style="--c:${r.fallback ? "var(--rule)" : color(i)}; --w:${(r.share * 100).toFixed(1)}%">
        <span class="name">${esc(r.title)}<small>${esc(r.form || "")}</small></span>
        <span class="track"><span class="fill" style="width:var(--w)"></span><span class="val">${pct(r.share)}</span></span>
      </div>`).join("")}</div>
    <table><tr><th>Intent</th><th>Coverage</th><th>Share</th><th>Ranks</th><th>Searcher goal</th></tr>
      ${rows.map((r, i) => `<tr><td><span class="sw" style="--c:${r.fallback ? "var(--rule)" : color(i)}"></span>${esc(r.title)}</td>
        <td>${pct(r.coverage)}</td><td>${pct(r.share)}</td><td>${r.ranks.join(", ")}</td><td>${esc(r.searcher_goal)}</td></tr>`).join("")}
    </table>
    ${(labels.reader_questions || []).length ? `<h3 style="margin-top:24px">Reader questions</h3><ul>${labels.reader_questions.map((q) => `<li>${esc(q.question)}</li>`).join("")}</ul>` : ""}`;
}

$("#playground").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = $("#pgStatus");
  const key = keyInput.value.trim();
  const results = parseResults($("#pgResults").value);
  status.classList.remove("error");
  if (results.length < 2) { status.textContent = "Add at least two results, one per line."; status.classList.add("error"); return; }
  try {
    if ($("#pgRemember").checked) localStorage.setItem(KEY_STORE, key);
    else localStorage.removeItem(KEY_STORE);
  } catch { /* storage blocked */ }
  const payload = { source: "serp", keyword: $("#pgKeyword").value.trim(), language: $("#pgLanguage").value.trim() || "en",
    brief: "", serp_features: { people_also_ask: [], related_searches: [], ai_overview: "", item_types: [] }, results };
  $("#pgRun").disabled = true;
  status.textContent = `Asking ${$("#pgModel").value} to group ${results.length} results. This usually takes a few seconds; slower models can take a minute.`;
  try {
    const labels = await callModel({ key, model: $("#pgModel").value.trim(), payload });
    status.textContent = "Done. The groups come from the model; every percentage below was computed in your browser.";
    render(payload.keyword, results, labels);
  } catch (e) {
    status.textContent = `Could not label the results: ${e.message}. Check the key and the model name, then try again.`;
    status.classList.add("error");
  } finally {
    $("#pgRun").disabled = false;
  }
});

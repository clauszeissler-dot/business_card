"use strict";
const $ = (s) => document.querySelector(s);
const form = $("#card");
const status = (msg, err) => { const el = $("#status"); el.textContent = msg; el.className = err ? "error" : ""; };

// Vorbelegung aus dem Skill: Link …/#c=<base64url-JSON>. Überlebt die Anmeldung via sessionStorage.
function readPrefill() {
  const m = location.hash.match(/^#c=([A-Za-z0-9_-]+)$/);
  if (m) {
    try {
      const json = atob(m[1].replace(/-/g, "+").replace(/_/g, "/"));
      sessionStorage.setItem("bc_prefill", decodeURIComponent(escape(json)));
    } catch (e) { /* ungültige Vorbelegung ignorieren */ }
    history.replaceState(null, "", location.pathname);
  }
  try { return JSON.parse(sessionStorage.getItem("bc_prefill") || "{}"); } catch (e) { return {}; }
}

function fill(data) {
  for (const [k, v] of Object.entries(data)) {
    const el = form.elements.namedItem(k);
    if (!el || typeof v !== "string" && typeof v !== "number" && typeof v !== "boolean") continue;
    if (el.type === "checkbox") el.checked = !!v; else el.value = String(v).slice(0, 200);
  }
}

function payload() {
  const d = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    d[el.name] = el.type === "checkbox" ? el.checked : el.value.trim();
  }
  d.valid_days = Number(d.valid_days || 0);
  try { sessionStorage.setItem("bc_prefill", JSON.stringify(d)); } catch (e) { /* egal */ }
  remember(d);
  return d;
}

// Merkfunktion (Opt-in): Formular dauerhaft nur im Browser speichern. Nie Beitragstext oder Bestätigung.
const SAVED = "bc_saved";
function remember(d) {
  try {
    if (!$("#remember").checked) { localStorage.removeItem(SAVED); return; }
    const { text, confirm, ...keep } = d;
    localStorage.setItem(SAVED, JSON.stringify(keep));
  } catch (e) { /* Speicher gesperrt: dann eben nicht */ }
}
function loadSaved() {
  try { return JSON.parse(localStorage.getItem(SAVED) || "null"); } catch (e) { return null; }
}

function download(path, extra) {
  const d = payload(); if (!needUrl(d)) return;
  if (extra.needsDays && !(d.valid_days > 0)) { status("Für die Erinnerung bitte oben „Gültig (Tage)“ auf mindestens 1 setzen.", true); form.elements.valid_days.focus(); return; }
  const f = $("#download-form");
  f.action = path;
  f.elements.payload.value = JSON.stringify({ ...d, device: extra.device || "iphone" });
  f.submit();
  status("Datei wird erstellt …");
}

async function post(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "same-origin" });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || "Fehler " + r.status);
  return data;
}

function needUrl(d) {
  if (!d.linkedin_url) { status("Bitte deine LinkedIn-Profil-URL eintragen.", true); form.elements.linkedin_url.focus(); return false; }
  return true;
}

async function init() {
  const prefill = readPrefill();
  const me = await fetch("/api/me", { credentials: "same-origin" }).then((r) => r.json()).catch(() => ({}));
  if (!me.signed_in) { $("#signed-out").hidden = false; return; }
  $("#signed-in").hidden = false;
  $("#me-name").textContent = me.name;
  $("#me-email").textContent = me.email || "";
  if (me.picture && me.picture.startsWith("https://media.licdn.com/")) { $("#me-picture").src = me.picture; $("#me-picture").hidden = false; }
  form.elements.lang.value = me.lang === "en" ? "en" : "de";
  // Vorschläge aus der Anmeldung: Geschäftsadresse und Website nur, wenn die E-Mail keine Freemail-Adresse ist.
  if (me.email_domain) {
    form.elements.email.value = me.email;
    form.elements.website.value = me.email_domain;
  } else if (me.email) {
    $("#email-hint").textContent = "Deine LinkedIn-Adresse ist privat und wird deshalb nicht übernommen. Trag hier deine geschäftliche Adresse ein oder lass das Feld leer.";
  }
  const saved = loadSaved();
  if (saved) { $("#remember").checked = true; fill(saved); }
  fill(prefill);
  $("#remember").addEventListener("change", () => remember(payload()));
  for (const b of document.querySelectorAll("[data-download]")) {
    b.addEventListener("click", () => download(b.dataset.download, { device: b.dataset.device, needsDays: "needsDays" in b.dataset }));
  }

  $("#apple").addEventListener("click", () => {
    const d = payload(); if (!needUrl(d)) return;
    const f = $("#apple-form"); f.elements.payload.value = JSON.stringify(d); f.submit();
    status("Pass wird erstellt … Auf dem iPhone öffnet sich Wallet.");
  });
  $("#google").addEventListener("click", async () => {
    const d = payload(); if (!needUrl(d)) return;
    try { status("Link wird erstellt …"); const r = await post("/api/pass/google", d); location.href = r.url; }
    catch (e) { status(e.message, true); }
  });
  $("#share").addEventListener("click", async () => {
    const d = payload(); if (!needUrl(d)) return;
    if (!d.confirm) { status("Bitte zuerst bestätigen, dass du öffentlich posten möchtest.", true); return; }
    try { status("Beitrag wird veröffentlicht …"); await post("/api/share", d); status("Veröffentlicht. Schau in deinen LinkedIn-Feed."); }
    catch (e) { status(e.message, true); }
  });
  $("#logout").addEventListener("click", async () => {
    await post("/api/logout", {}).catch(() => {}); sessionStorage.removeItem("bc_prefill"); try { localStorage.removeItem(SAVED); } catch (e) { /* egal */ } location.reload();
  });
}
init();

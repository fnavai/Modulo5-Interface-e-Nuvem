"use strict";

// ---- mapeamentos ----
const SVC_NOMES = {
  interface: "Portal (Interface)",
  perfis_usuarios: "Perfis-Usuários",
  ia_analise_codigo: "IA-Análise",
  gerador_documentacao: "Gerador-Doc",
};
const ESTADO_CLS = { disponivel: "ok", degradado: "warn", indisponivel: "bad" };
const ESTADO_LBL = { disponivel: "no ar", degradado: "degradado", indisponivel: "fora" };

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstChild;
}
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ---- saúde (faixa compacta) ----
function cardSaude(key, estado, detalhe) {
  const cls = ESTADO_CLS[estado] || "warn";
  return el(`
    <div class="svc svc--${cls}" title="${esc(detalhe || "")}">
      <div class="svc__top">
        <span class="svc__name">${esc(SVC_NOMES[key] || key)}</span>
        <span class="svc__badge">${esc(ESTADO_LBL[estado] || estado || "?")}</span>
      </div>
    </div>`);
}
function setPill(cls, txt) {
  const p = document.getElementById("global-pill");
  p.className = "pill pill--" + cls;
  document.getElementById("global-pill-txt").textContent = txt;
}
async function atualizarSaude() {
  const grid = document.getElementById("health-grid");
  let portalOk = false;
  try { portalOk = (await fetch("/health", { cache: "no-store" })).ok; }
  catch (_) { portalOk = false; }

  let dados = null;
  try { dados = await (await fetch("/health/ready", { cache: "no-store" })).json(); }
  catch (_) { dados = null; }

  grid.innerHTML = "";
  grid.appendChild(cardSaude("interface", portalOk ? "disponivel" : "indisponivel",
    portalOk ? "Servindo o portal e a API BFF." : "Portal sem resposta."));
  const svcs = (dados && dados.servicos) || {};
  for (const key of ["perfis_usuarios", "ia_analise_codigo", "gerador_documentacao"]) {
    const s = svcs[key];
    grid.appendChild(s ? cardSaude(key, s.estado, s.detalhes)
                       : cardSaude(key, "indisponivel", "Sem dados do agregador."));
  }
  const st = dados && dados.status;
  if (!portalOk || !dados) setPill("bad", "portal sem resposta");
  else if (st === "ok") setPill("ok", "tudo operacional");
  else if (st === "fallback") setPill("warn", "operando com cache");
  else setPill("bad", "serviço(s) degradado(s)");
  document.getElementById("saude-updated").textContent =
    "atualizado " + new Date().toLocaleTimeString("pt-BR");
}

// ---- render dos painéis ----
function linhaKV(k, v) {
  return `<div class="kv__row"><span class="kv__k">${esc(k)}</span><span class="kv__v">${v}</span></div>`;
}
function renderResumo(resumo) {
  const box = document.getElementById("resumo");
  if (!resumo || typeof resumo !== "object" || !Object.keys(resumo).length) {
    box.innerHTML = '<div class="kv__empty">Resumo da IA indisponível para este arquivo.</div>';
    return;
  }
  const comps = Array.isArray(resumo.componentes) ? resumo.componentes : [];
  const rels = Array.isArray(resumo.relacoes) ? resumo.relacoes : [];
  let html = "";
  if (resumo.linguagem) html += linhaKV("Linguagem", `<code>${esc(resumo.linguagem)}</code>`);
  html += linhaKV("Componentes", comps.length);
  html += linhaKV("Relações", rels.length);
  if (comps.length) {
    const tags = comps.slice(0, 12)
      .map((c) => `<span class="tag">${esc((c && (c.nome || c.name)) || "?")}</span>`).join("");
    html += `<div class="kv__row" style="flex-direction:column;align-items:flex-start;gap:6px">
      <span class="kv__k">Principais componentes</span><div>${tags}${
      comps.length > 12 ? `<span class="tag">+${comps.length - 12}</span>` : ""}</div></div>`;
  }
  box.innerHTML = html;
}
function renderQualidade(q) {
  const box = document.getElementById("qualidade");
  if (!q || typeof q !== "object" || !Object.keys(q).length) {
    box.innerHTML = '<div class="kv__empty">Qualidade indisponível (IA fora ou código não obtido) — degradação graciosa.</div>';
    return;
  }
  let html = "";
  for (const [k, v] of Object.entries(q)) {
    let val;
    if (Array.isArray(v)) val = `<span class="tag">${v.length} item(ns)</span>`;
    else if (v && typeof v === "object") val = `<span class="tag">${Object.keys(v).length} chave(s)</span>`;
    else val = `<code>${esc(String(v).slice(0, 80))}</code>`;
    html += linhaKV(k, val);
  }
  box.innerHTML = html || '<div class="kv__empty">Sem dados de qualidade.</div>';
}
function renderOwnership(own) {
  const box = document.getElementById("ownership");
  if (!own || typeof own !== "object") {
    box.innerHTML = '<div class="kv__empty">Ownership indisponível (Perfis fora ou sem dado).</div>';
    return;
  }
  const o = own.ownership || own;
  let html = "";
  if (o.owner_id != null) html += linhaKV("Owner", `<code>${esc(o.owner_id)}</code>`);
  if (o.confianca != null) html += linhaKV("Confiança", `${(Number(o.confianca) * 100).toFixed(1)}%`);
  if (o.total_commits != null) html += linhaKV("Commits", esc(o.total_commits));
  if (o.modulo != null) html += linhaKV("Módulo", `<code>${esc(o.modulo)}</code>`);
  if (own.origem) html += linhaKV("Origem", esc(own.origem));
  if (own.aviso) html += linhaKV("Aviso", esc(own.aviso));
  box.innerHTML = html || '<div class="kv__empty">Sem ownership registrado para este módulo.</div>';
}
function renderNotices(faltantes) {
  const box = document.getElementById("notices");
  box.innerHTML = "";
  const txt = {
    diagrama: "Diagrama indisponível.",
    resumo_ia: "Resumo da IA indisponível — degradação graciosa.",
    ownership: "Ownership do Perfis indisponível — degradação graciosa.",
  };
  (faltantes || []).forEach((f) => {
    box.appendChild(el(`<div class="notice">⚠ ${esc(txt[f] || f)}</div>`));
  });
}
async function renderDiagrama(mermaidTxt) {
  const box = document.getElementById("diagram");
  const src = document.getElementById("diagram-src");
  src.textContent = mermaidTxt || "(sem diagrama)";
  if (!mermaidTxt) { box.innerHTML = '<div class="kv__empty">Diagrama indisponível.</div>'; return; }
  if (typeof window.mermaid === "undefined") {
    box.innerHTML = ""; box.appendChild(el(`<pre class="code">${esc(mermaidTxt)}</pre>`)); return;
  }
  try {
    const { svg } = await window.mermaid.render("mmd-" + Date.now(), mermaidTxt);
    box.innerHTML = svg;
  } catch (e) {
    box.innerHTML = "";
    box.appendChild(el(`<div class="kv__empty">Não foi possível renderizar o Mermaid (${esc(e && e.message)}). Fonte abaixo.</div>`));
    src.hidden = false;
  }
}

// ---- análise ----
function valoresForm() {
  return {
    repositorio: document.getElementById("repositorio").value.trim(),
    branch: document.getElementById("branch").value.trim() || "develop",
    caminho: document.getElementById("caminho").value.trim(),
  };
}
function setLoading(on) {
  const b = document.getElementById("submit");
  b.disabled = on;
  b.querySelector(".btn__txt").textContent = on ? "Analisando…" : "Analisar";
  b.querySelector(".btn__spin").hidden = !on;
}
async function runAnalise() {
  const { repositorio, branch, caminho } = valoresForm();
  const banner = document.getElementById("banner");
  const result = document.getElementById("result");
  const empty = document.getElementById("empty");
  banner.hidden = true;
  setLoading(true);
  try {
    const r = await fetch("/api/projeto/analisar", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repositorio, branch, caminho }),
    });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) {
      empty.hidden = true;
      banner.textContent = "⚠ " + (body.erro || `Falha (HTTP ${r.status}).`) +
        (r.status === 502 ? " O Gerador (GitHub/IA) não respondeu." : "");
      banner.hidden = false;
      return;
    }
    empty.hidden = true;
    result.hidden = false;
    renderNotices(body.partes_faltantes);
    await renderDiagrama(body.diagrama_mermaid);
    renderResumo(body.resumo_ia);
    renderQualidade(body.qualidade);
    renderOwnership(body.ownership);
  } catch (e) {
    document.getElementById("empty").hidden = true;
    banner.textContent = "⚠ Erro de rede ao falar com o portal: " + (e && e.message);
    banner.hidden = false;
  } finally {
    setLoading(false);
  }
}

// ---- downloads (Relatórios / Apresentações) ----
function nomeDoHeader(resp, padrao) {
  const cd = resp.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename="([^"]+)"/);
  return (m && m[1]) || padrao;
}
async function baixarDocumento(btn, url, extra, padrao) {
  const status = document.getElementById("dl-status");
  const spin = btn.querySelector(".btn__spin");
  btn.disabled = true; if (spin) spin.hidden = false;
  status.textContent = "gerando…"; status.style.color = "";
  try {
    const r = await fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...valoresForm(), ...extra }),
    });
    if (!r.ok) {
      let msg = `HTTP ${r.status}`;
      try { msg = (await r.json()).erro || msg; } catch (_) {}
      status.textContent = "⚠ " + msg; status.style.color = "var(--bad)";
      return;
    }
    const blob = await r.blob();
    const nome = nomeDoHeader(r, padrao);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = nome;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    status.textContent = "✓ " + nome + " (" + Math.round(blob.size / 1024) + " KB)";
    status.style.color = "var(--ok)";
  } catch (e) {
    status.textContent = "⚠ erro de rede: " + (e && e.message);
    status.style.color = "var(--bad)";
  } finally {
    btn.disabled = false; if (spin) spin.hidden = true;
  }
}

// ---- init ----
if (typeof window.mermaid !== "undefined") {
  window.mermaid.initialize({
    startOnLoad: false, theme: "dark", securityLevel: "loose",
    themeVariables: { fontFamily: "JetBrains Mono, monospace" },
  });
}
document.getElementById("form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  runAnalise();
});
document.getElementById("toggle-src").addEventListener("click", () => {
  const s = document.getElementById("diagram-src");
  s.hidden = !s.hidden;
});
document.getElementById("btn-pptx").addEventListener("click", (e) =>
  baixarDocumento(e.currentTarget, "/api/projeto/documento/pptx", {}, "apresentacao.pptx"));
document.getElementById("btn-relatorio").addEventListener("click", (e) => {
  const fmt = document.getElementById("sel-formato").value;
  baixarDocumento(e.currentTarget, "/api/projeto/documento/relatorio",
    { formato: fmt }, "relatorio." + (fmt === "md" ? "md" : fmt));
});

// saúde + auto-análise ao abrir (o resultado é o protagonista)
atualizarSaude();
setInterval(atualizarSaude, 10000);
runAnalise();

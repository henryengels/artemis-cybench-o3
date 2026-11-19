#!/usr/bin/env python3
"""Monta dash_passos.html (artifact de passos) embutindo passos40_enr.json."""
import json
from pathlib import Path

OUT = Path(os.environ.get("CYBENCH_OUT", Path(__file__).resolve().parent))
dados = json.loads((OUT / "passos40_enr.json").read_text())
DADOS_JSON = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))

# observações da tabela do Resumo (sem flag) — casadas por nome de tarefa
_res = json.loads((OUT / "dash_resultados.json").read_text())
OBS = {r["tarefa"]: {"resultado": r.get("resultado", ""), "obs": r.get("obs", "")} for r in _res}
OBS_JSON = json.dumps(OBS, ensure_ascii=False, separators=(",", ":"))
_hit = sum(1 for t in dados if t.get("tarefa") in OBS)
print(f"obs casadas: {_hit}/{len(dados)}")

HTML = r"""<meta name="claude:viewport-fit-sides" content="cover">
<title>ARTEMIS no Cybench</title>
<style>
/* Layout: página-trilha (header fixo + banda-resumo + lista de tarefas expansíveis).
   Identidade: "terminal forense" — neutros slate com viés azul, âmbar p/ comandos, verde/vermelho semânticos. */
:root{
  --bg:#f4f6f9; --panel:#ffffff; --panel-2:#eef1f6; --ink:#1a2230; --muted:#5a6678;
  --line:#d8dee8; --accent:#2b6cb0; --amber:#9a6b00; --amber-bg:#fbf3df;
  --ok:#1f7a4d; --ok-bg:#e4f3ea; --bad:#b23a48; --bad-bg:#f7e7e9;
  --gray:#6b7484; --gray-bg:#e9edf3; --warn:#9a5a00; --warn-bg:#fcefdd;
  --code:#243049; --code-ink:#e6ebf4;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:"Inter",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --disp:"Space Grotesk","Inter",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e141f; --panel:#161e2b; --panel-2:#1c2636; --ink:#e7edf6; --muted:#9aa7bb;
  --line:#2a364a; --accent:#6fa8dc; --amber:#e3b341; --amber-bg:#2e2512;
  --ok:#6cc79a; --ok-bg:#12271d; --bad:#e88b95; --bad-bg:#2c161a;
  --gray:#9aa7bb; --gray-bg:#1d2736; --warn:#e3a857; --warn-bg:#2a1f10;
  --code:#0a0f18; --code-ink:#dce4f0; color-scheme:dark;
}}
:root[data-theme="dark"]{
  --bg:#0e141f; --panel:#161e2b; --panel-2:#1c2636; --ink:#e7edf6; --muted:#9aa7bb;
  --line:#2a364a; --accent:#6fa8dc; --amber:#e3b341; --amber-bg:#2e2512;
  --ok:#6cc79a; --ok-bg:#12271d; --bad:#e88b95; --bad-bg:#2c161a;
  --gray:#9aa7bb; --gray-bg:#1d2736; --warn:#e3a857; --warn-bg:#2a1f10;
  --code:#0a0f18; --code-ink:#dce4f0; color-scheme:dark;
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;margin:0}
.wrap{max-width:1000px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0}
h1,h2,h3{font-family:var(--disp);text-wrap:balance;margin:0}
a{color:var(--accent)}
code,kbd,.mono{font-family:var(--mono)}
.toolbar{background:var(--bg);border-bottom:1px solid var(--line)}
.toolbar .wrap{padding-block:8px}
.toolbar .controls{padding-block:5px}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);background:var(--bg);z-index:11}
header .wrap{padding-block:16px 10px}
.kick{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 4px}
h1{font-size:clamp(24px,5vw,34px);letter-spacing:-.01em}
.sub{color:var(--muted);margin:6px 0 0;max-width:68ch}

/* resumo honesto */
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.tile .n{font-family:var(--disp);font-size:26px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
.tile .l{color:var(--muted);font-size:12.5px;margin-top:4px}
.tile.ok .n{color:var(--ok)} .tile.warn .n{color:var(--warn)} .tile.gray .n{color:var(--gray)}
.note{margin:14px 0 2px;background:var(--warn-bg);border:1px solid color-mix(in srgb,var(--warn) 40%,var(--line));border-left:4px solid var(--warn);border-radius:10px;padding:12px 14px;font-size:13.5px}
.note b{color:var(--warn)}

/* controles */
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding-block:12px}
.controls input[type=search]{flex:1 1 220px;min-width:0;padding:9px 12px;border:1px solid var(--line);border-radius:9px;background:var(--panel);color:var(--ink);font-size:14px;font-family:var(--sans)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--muted);padding:8px 11px;font-size:12.5px;cursor:pointer;font-family:var(--sans)}
.seg button[aria-pressed=true]{background:var(--accent);color:#fff}
.lnk{background:none;border:0;color:var(--accent);cursor:pointer;font-size:12.5px;padding:8px 4px;font-family:var(--sans)}
.count{color:var(--muted);font-size:12.5px;margin-left:auto}

/* cards de tarefa */
main .wrap{padding-block:8px 48px}
.task{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:10px 0;overflow:hidden}
.task>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center;padding:12px 14px}
.task>summary::-webkit-details-marker{display:none}
.task>summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.idx{font-family:var(--mono);font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.tname{font-family:var(--disp);font-weight:600;font-size:16px;min-width:0}
.tmeta{display:flex;flex-wrap:wrap;gap:6px;margin-top:5px}
.chip{font-size:11.5px;padding:2px 8px;border-radius:999px;background:var(--panel-2);color:var(--muted);border:1px solid var(--line);white-space:nowrap}
.pill{font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px;white-space:nowrap}
.pill.ok{background:var(--ok-bg);color:var(--ok)} .pill.bad{background:var(--bad-bg);color:var(--bad)}
.pill.gray{background:var(--gray-bg);color:var(--gray)} .pill.warn{background:var(--warn-bg);color:var(--warn)}
.stat{font-family:var(--mono);font-size:11.5px;color:var(--muted);text-align:right;line-height:1.35}
.body{border-top:1px solid var(--line);padding:14px}
.leitura{background:var(--panel-2);border-radius:10px;padding:11px 13px;font-size:14px;margin-bottom:14px}
.leitura b{color:var(--ink)}
.prox{font-size:11px;font-weight:700;padding:2px 9px;border-radius:999px;white-space:nowrap}
.prox.quase{background:var(--amber-bg);color:var(--amber)}
.prox.parcial{background:var(--warn-bg);color:var(--warn)}
.prox.longe{background:var(--bad-bg);color:var(--bad)}
.faltou{background:var(--panel-2);border-left:3px solid var(--warn);border-radius:8px;padding:10px 12px;margin-bottom:14px;font-size:13.5px}
.faltou .lbl{font-weight:700;color:var(--warn)}
.faltou .sinal{display:block;color:var(--muted);font-size:12px;margin-top:4px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--muted);margin-top:10px}
.legend span{display:inline-flex;align-items:center;gap:5px}
.legend i{width:10px;height:10px;border-radius:3px;display:inline-block}
.seclbl{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:16px 0 8px}
ol.plan{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:5px}
ol.plan li{font-size:13.5px}
ol.plan .st{font-family:var(--mono);font-size:10.5px;padding:1px 6px;border-radius:5px;margin-right:6px;background:var(--gray-bg);color:var(--gray)}
ol.plan .st.completed{background:var(--ok-bg);color:var(--ok)}

.sub{} /* reset not used */
.agent{border:1px solid var(--line);border-radius:10px;margin:10px 0;overflow:hidden}
.agent>summary{list-style:none;cursor:pointer;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 12px;background:var(--panel-2)}
.agent>summary::-webkit-details-marker{display:none}
.agent .aid{font-family:var(--mono);font-weight:600;font-size:13px}
.badge{font-size:10.5px;font-family:var(--mono);letter-spacing:.04em;padding:2px 7px;border-radius:6px;background:var(--accent);color:#fff;text-transform:uppercase}
.agent .goal{flex-basis:100%;color:var(--muted);font-size:12.5px;margin-top:2px}
.ncmd{margin-left:auto;font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.steps{list-style:none;margin:0;padding:8px 12px;display:flex;flex-direction:column;gap:7px;max-height:360px;overflow:auto}
.step{display:grid;grid-template-columns:52px 1fr;gap:9px;align-items:start}
.step .t{font-family:var(--mono);font-size:10.5px;color:var(--muted);padding-top:3px}
.step .g{font-size:13px}
.step .c{display:block;font-family:var(--mono);font-size:11.5px;background:var(--code);color:var(--code-ink);border-radius:6px;padding:5px 8px;margin-top:3px;white-space:pre-wrap;word-break:break-word;overflow-wrap:anywhere}
.concl{margin:4px 12px 12px;background:var(--amber-bg);border:1px solid color-mix(in srgb,var(--amber) 35%,var(--line));border-radius:8px;padding:9px 11px;font-size:12.5px}
.concl .cl{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--amber);display:block;margin-bottom:4px}
.concl pre{margin:0;white-space:pre-wrap;word-break:break-word;font-family:var(--mono);font-size:11.5px;line-height:1.45}
.submit{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}
.fbox{flex:1 1 240px;min-width:0;border:1px solid var(--line);border-radius:9px;padding:9px 11px;background:var(--panel-2)}
.fbox .fl{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.fbox .fv{font-family:var(--mono);font-size:12.5px;word-break:break-word;margin-top:3px}
.empty{color:var(--muted);font-size:13px;font-style:italic}
.norun{background:var(--gray-bg);border:1px dashed var(--line);border-radius:10px;padding:14px;color:var(--muted);font-size:13.5px}
.hidden{display:none!important}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
footer .wrap{padding-block:16px 34px}
@media(max-width:520px){
  .task>summary{grid-template-columns:28px 1fr;grid-template-areas:"i n" "s s"}
  .idx{grid-area:i}.sumn{grid-area:n}.sumr{grid-area:s;justify-self:start;text-align:left}
  .stat{text-align:left}
}

/* --- abas + aba Resumo (merge do dashboard) --- */
.tabs{position:sticky;top:env(safe-area-inset-top,0px);z-index:12;background:var(--bg);border-bottom:1px solid var(--line);display:flex;gap:4px;max-width:1000px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.tabs button{border:0;background:none;color:var(--muted);font-family:var(--disp);font-weight:600;font-size:15px;padding:12px 10px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
.tabs button[aria-selected=true]{color:var(--accent);border-bottom-color:var(--accent)}
.tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;border-radius:4px}
.panel.hidden{display:none}
.panel h2{font-family:var(--disp);font-size:19px;margin:22px 0 2px}
.sub2{color:var(--muted);font-size:13px;margin:4px 0 14px;max-width:70ch}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.chart{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.chart h3{font-family:var(--disp);font-size:14px;margin:0 0 12px}
.bar{margin:11px 0}
.bar .brow{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:4px}
.bar .bl{font-size:13px;color:var(--ink);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar .bv{font-family:var(--mono);font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap;flex:none}
.bar .bv b{color:var(--ink);font-weight:700}
.bar .bt{height:22px;background:var(--panel-2);border:1px solid var(--line);border-radius:7px;overflow:hidden}
.bar .bf{display:block;height:100%;background:var(--accent);border-radius:6px 0 0 6px;min-width:4px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin-top:8px}
table.res{border-collapse:collapse;width:100%;font-size:13px;min-width:600px}
table.res th,table.res td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);white-space:nowrap}
table.res th{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);position:sticky;top:0;background:var(--panel);z-index:1}
table.res tbody tr:last-child td{border-bottom:0}
table.res td.num{font-family:var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}
table.res td.tn{font-weight:600}
table.res td.obs{white-space:normal;color:var(--muted);min-width:190px}
table.res .pill{font-size:11px}
</style>

<header><div class="wrap">
  <p class="kick">Benchmark · modelo o3</p>
  <h1>ARTEMIS no Cybench</h1>
  <p class="sub">As 40 tarefas CTF do Cybench rodadas na arquitetura do ARTEMIS (supervisor + subagentes + codex, o3), 30 min por tarefa, com a flag redigida no workspace do agente (anti-leak). O <b>Resumo</b> traz os números; o <b>Passo a passo</b>, a trilha real de cada desafio.</p>
  <div class="summary">__SUMMARY__</div>
  __NOTE__
</div></header>

<nav class="tabs" role="tablist" aria-label="Visões">
  <button data-tab="resumo" role="tab" aria-selected="true">Resumo</button>
  <button data-tab="passos" role="tab" aria-selected="false">Passo a passo</button>
</nav>

<section id="tab-resumo" class="panel"><div class="wrap">
  <h2>Taxa de acerto</h2>
  <p class="sub2">Flag correta sobre o total de tarefas de cada grupo. Barra = porcentagem; ao lado, acertos/total.</p>
  <div class="charts">
    <div class="chart"><h3>Por fonte (CTF)</h3><div id="chartFonte"></div></div>
    <div class="chart"><h3>Por categoria</h3><div id="chartCat"></div></div>
  </div>
  <h2>Os 40 desafios</h2>
  <p class="sub2">Clique em “Passo a passo” para abrir a trilha completa de qualquer um deles.</p>
  <div class="tablewrap"><table class="res"><thead><tr>
    <th>#</th><th>Tarefa</th><th>Fonte</th><th>Categoria</th><th>Serviço</th><th>Resultado</th><th>Observação</th>
  </tr></thead><tbody id="resBody"></tbody></table></div>
</div></section>

<section id="tab-passos" class="panel hidden">
<div class="wrap" style="padding-block:14px 0"><div class="legend"><b style="color:var(--muted)">Quão perto chegou:</b>
    <span><i style="background:var(--ok)"></i>resolvida</span>
    <span><i style="background:var(--amber)"></i>quase (conteúdo/1 passo)</span>
    <span><i style="background:var(--warn)"></i>parcial (atacou, não fechou)</span>
    <span><i style="background:var(--bad)"></i>longe (recon/placeholder/travou)</span>
  </div></div>

<div class="toolbar"><div class="wrap">
  <div class="controls">
    <input type="search" id="q" placeholder="Buscar por nome, categoria, especialista, comando…" aria-label="Buscar">
    <div class="seg" id="fEstado" role="group" aria-label="Filtrar por execução">
      <button data-v="all" aria-pressed="true">Todas</button>
      <button data-v="ok">Resolvidas</button>
      <button data-v="ran">Rodaram</button>
      <button data-v="norun">Não rodaram</button>
    </div>
    <button class="lnk" id="sortProx">Ordenar: proximidade</button>
    <button class="lnk" id="toggleAll">Expandir todas</button>
  </div>
  <div class="controls" style="padding-top:0">
    <div class="seg" id="fFonte" role="group" aria-label="Filtrar por fonte">
      <button data-v="all" aria-pressed="true">Todas as fontes</button>
      <button data-v="HackTheBox">HackTheBox</button>
      <button data-v="SekaiCTF">SekaiCTF</button>
      <button data-v="GlacierCTF">GlacierCTF</button>
      <button data-v="HKCERT">HKCERT</button>
    </div>
    <span class="count" id="count"></span>
  </div>
</div></div>

<main><div class="wrap" id="list"></div></main>
</section>

<footer><div class="wrap">
  Reconstruído de <code>logs/supervisor_session_*</code> (supervisor.log, supervisor_todo.json, workspaces/&lt;subagente&gt;/realtime_context.txt, ctf_submissions.json).
  A arquitetura do ARTEMIS não foi alterada; apenas o ambiente/ponte do benchmark. Flags foram redigidas no workspace do agente (anti-leak), por isso alguns submeteram placeholders.
</div></footer>

<script id="dados" type="application/json">__DADOS__</script>
<script id="obs" type="application/json">__OBS__</script>
<script>
const DADOS = JSON.parse(document.getElementById('dados').textContent);
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function mdb(s){ // **bold** e `code`
  return esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`([^`]+)`/g,'<code>$1</code>');
}
const estadoPill = {completa:['','',''], parcial:['warn','parcial'], nao_rodou:['gray','não rodou']};
function resultPill(t){
  if(t.sucesso) return '<span class="pill ok">✔ resolvida</span>';
  if(t.estado==='nao_rodou') return '<span class="pill gray">○ não rodou</span>';
  return '<span class="pill bad">✘ não resolvida</span>';
}
function proxBadge(t){
  if(t.sucesso || t.estado==='nao_rodou' || !t.prox) return '';
  const lbl={quase:'quase lá',parcial:'parcial',longe:'longe'}[t.prox]||t.prox;
  return ` <span class="prox ${esc(t.prox)}">${esc(lbl)}</span>`;
}
function agentBlock(s){
  const steps = (s.comandos||[]).map(c=>`<li class="step"><span class="t">${esc(c.t||'')}</span><div><span class="g">${esc(c.g||'')}</span><code class="c">$ ${esc(c.cmd||'')}</code></div></li>`).join('');
  const concl = s.conclusao ? `<div class="concl"><span class="cl">conclusão do subagente</span><pre>${esc(s.conclusao)}</pre></div>` : '';
  const goal = s.objetivo ? `<span class="goal">🎯 ${esc(s.objetivo)}</span>` : '';
  return `<details class="agent"><summary><span class="aid">${esc(s.id)}</span><span class="badge">${esc(s.especialista||'?')}</span><span class="ncmd">${s.n_comandos} comando(s)</span>${goal}</summary>`+
    (steps?`<ul class="steps">${steps}</ul>`:'<p class="empty" style="padding:0 12px">Sem comandos registrados.</p>')+concl+`</details>`;
}
function body(t){
  if(t.estado==='nao_rodou'){
    return `<div class="body"><div class="leitura">${mdb(t.explicacao||t.leitura)}</div><div class="norun">Nenhum subagente foi criado e nenhum comando foi executado — o supervisor não conseguiu sequer uma resposta do modelo o3 (<code>429 insufficient_quota</code>, ${t.n_iteracoes} tentativas).</div></div>`;
  }
  const plano = (t.plano||[]).map(p=>`<li><span class="st ${esc(p.status)}">${esc(p.status||'—')}</span>${esc(p.desc)}</li>`).join('');
  const agentes = (t.subagentes||[]).map(agentBlock).join('') || '<p class="empty">Sem subagentes registrados.</p>';
  const flags = (t.flags_submetidas&&t.flags_submetidas.length)?t.flags_submetidas.map(esc).join('<br>'):'<span class="empty">nenhuma flag submetida</span>';
  const faltou = (!t.sucesso && t.faltou) ? `<div class="faltou"><span class="lbl">O que faltou:</span> ${mdb(t.faltou)}<span class="sinal">Sinal nos registros: ${mdb(t.sinal||'')}</span></div>` : '';
  return `<div class="body">
    <div class="seclbl">Explicação passo a passo</div>
    <div class="leitura">${mdb(t.explicacao||t.leitura||'')}</div>
    ${faltou}
    <div class="seclbl">Plano do supervisor</div>
    <ol class="plan">${plano||'<li class="empty">Sem plano registrado.</li>'}</ol>
    <div class="seclbl">Subagentes criados &amp; passos</div>
    ${agentes}
    <div class="seclbl">Submissão</div>
    <div class="submit">
      <div class="fbox"><div class="fl">Flag submetida</div><div class="fv">${flags}</div></div>
      <div class="fbox"><div class="fl">Flag esperada</div><div class="fv">${esc(t.flag_esperada)||'<span class="empty">—</span>'}</div></div>
    </div>
  </div>`;
}
const fonteChip = {HackTheBox:'HTB',SekaiCTF:'Sekai',GlacierCTF:'Glacier',HKCERT:'HKCERT'};
function card(t,i){
  const ncmd = (t.subagentes||[]).reduce((a,s)=>a+ (s.n_comandos||0),0);
  const nsub = (t.subagentes||[]).length;
  const el = document.createElement('details');
  el.className='task';
  el.dataset.estado = t.estado; el.dataset.ok = t.sucesso?'1':'0'; el.dataset.fonte=t.fonte;
  el.dataset.prox = t.prox||''; el.dataset.idx = i;
  el.dataset.hay = (t.tarefa+' '+t.categoria+' '+t.fonte+' '+(t.subagentes||[]).map(s=>s.especialista+' '+(s.comandos||[]).map(c=>c.cmd+' '+c.g).join(' ')).join(' ')).toLowerCase();
  el.innerHTML = `<summary>
      <span class="idx">${String(i+1).padStart(2,'0')}</span>
      <span class="sumn"><span class="tname">${esc(t.tarefa)}</span>
        <span class="tmeta"><span class="chip">${esc(fonteChip[t.fonte]||t.fonte)}</span><span class="chip">${esc(t.categoria)}</span>${t.docker==='sim'?'<span class="chip">🐳 serviço</span>':'<span class="chip">offline</span>'}</span>
      </span>
      <span class="sumr" style="display:flex;flex-direction:column;align-items:flex-end;gap:5px"><span>${resultPill(t)}${proxBadge(t)}</span>
        <span class="stat">${nsub} subag · ${ncmd} cmd<br>${t.n_iteracoes} iterações</span>
      </span>`;
  const holder=document.createElement('div'); holder.innerHTML=body(t); el.appendChild(holder.firstElementChild);
  return el;
}
const list=document.getElementById('list');
DADOS.forEach((t,i)=>list.appendChild(card(t,i)));

// filtros
let fE='all', fF='all', q='';
function apply(){
  let n=0;
  document.querySelectorAll('.task').forEach(el=>{
    let ok=true;
    if(fE==='ok') ok = el.dataset.ok==='1';
    else if(fE==='ran') ok = el.dataset.estado==='completa'||el.dataset.estado==='parcial';
    else if(fE==='norun') ok = el.dataset.estado==='nao_rodou';
    if(ok && fF!=='all') ok = el.dataset.fonte===fF;
    if(ok && q) ok = el.dataset.hay.includes(q);
    el.classList.toggle('hidden',!ok);
    if(ok)n++;
  });
  document.getElementById('count').textContent = n+' de 40 tarefas';
}
document.getElementById('q').addEventListener('input',e=>{q=e.target.value.trim().toLowerCase();apply();});
function wireSeg(id,set){document.getElementById(id).addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  document.querySelectorAll('#'+id+' button').forEach(x=>x.setAttribute('aria-pressed',x===b));set(b.dataset.v);apply();});}
wireSeg('fEstado',v=>fE=v); wireSeg('fFonte',v=>fF=v);
let openAll=false;
document.getElementById('toggleAll').addEventListener('click',e=>{openAll=!openAll;
  document.querySelectorAll('.task:not(.hidden)').forEach(el=>el.open=openAll);
  e.target.textContent=openAll?'Recolher todas':'Expandir todas';});

// ordenar por proximidade (quase -> parcial -> longe -> resolvida -> não rodou)
let sorted=false;
const RANK={quase:0,parcial:1,longe:2,resolvido:3,'':4};
document.getElementById('sortProx').addEventListener('click',e=>{
  sorted=!sorted;
  const tasks=[...document.querySelectorAll('.task')];
  tasks.sort((a,b)=> sorted
    ? (RANK[a.dataset.prox]-RANK[b.dataset.prox]) || (+a.dataset.idx - +b.dataset.idx)
    : (+a.dataset.idx - +b.dataset.idx));
  tasks.forEach(el=>list.appendChild(el));
  e.target.textContent=sorted?'Ordem: original (#)':'Ordenar: proximidade';
});
apply();

// ---- aba Resumo: gráficos + tabela ----
const fonteChipR={HackTheBox:'HTB',SekaiCTF:'Sekai',GlacierCTF:'Glacier',HKCERT:'HKCERT'};
function grp(key){const m=new Map();DADOS.forEach(t=>{const k=t[key]||'—';if(!m.has(k))m.set(k,[]);m.get(k).push(t);});return m;}
function barRows(map,shorten){
  const rows=[...map.entries()].map(([k,arr])=>({k,num:arr.filter(t=>t.sucesso).length,den:arr.length}));
  rows.sort((a,b)=>(b.num/b.den)-(a.num/a.den)||b.den-a.den);
  return rows.map(r=>{const pct=Math.round(100*r.num/r.den);
    const fill=r.num===0?'':`<span class="bf" style="width:${(r.num/r.den*100).toFixed(1)}%"></span>`;
    return `<div class="bar"><div class="brow">`+
      `<span class="bl" title="${esc(r.k)}">${esc(shorten?(fonteChipR[r.k]||r.k):r.k)}</span>`+
      `<span class="bv"><b>${pct}%</b> · ${r.num}/${r.den}</span></div>`+
      `<div class="bt">${fill}</div></div>`;}).join('');
}
document.getElementById('chartFonte').innerHTML=barRows(grp('fonte'),true);
document.getElementById('chartCat').innerHTML=barRows(grp('categoria'),false);

const OBS=JSON.parse(document.getElementById('obs').textContent);
document.getElementById('resBody').innerHTML=DADOS.map((t,i)=>{
  const o=OBS[t.tarefa]||{};
  const obs=o.obs||(t.sucesso?'resolvido':(t.estado==='nao_rodou'?'não rodou':'não resolvido'));
  const serv=t.docker==='sim'?'🐳 serviço':'offline';
  return `<tr><td class="num">${String(i+1).padStart(2,'0')}</td><td class="tn">${esc(t.tarefa)}</td>`+
    `<td>${esc(fonteChipR[t.fonte]||t.fonte)}</td><td>${esc(t.categoria)}</td><td>${serv}</td>`+
    `<td>${resultPill(t)}</td><td class="obs">${esc(obs)}</td></tr>`;
}).join('');

// ---- troca de abas ----
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{
  const tgt=b.dataset.tab;
  document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b?'true':'false'));
  document.getElementById('tab-resumo').classList.toggle('hidden',tgt!=='resumo');
  document.getElementById('tab-passos').classList.toggle('hidden',tgt!=='passos');
  window.scrollTo(0,0);
}));
</script>
"""

# ---- estatísticas do cabeçalho (calculadas dos dados) ----
total = len(dados)
solved = sum(1 for t in dados if t.get("sucesso"))
n_nao = sum(1 for t in dados if t.get("estado") == "nao_rodou")
n_par = sum(1 for t in dados if t.get("estado") == "parcial")
n_comp = sum(1 for t in dados if t.get("estado") == "completa")
rodaram = n_comp + n_par          # executaram ao menos parcialmente
taxa = round(100 * solved / rodaram) if rodaram else 0

tiles = [f'<div class="tile ok"><div class="n">{solved}</div><div class="l">resolvidas (flag correta)</div></div>',
         f'<div class="tile"><div class="n">{rodaram}</div><div class="l">executaram</div></div>']
if n_par:
    tiles.append(f'<div class="tile warn"><div class="n">{n_par}</div><div class="l">parcial (créditos acabaram)</div></div>')
if n_nao:
    tiles.append(f'<div class="tile gray"><div class="n">{n_nao}</div><div class="l">não executaram (sem crédito)</div></div>')
tiles.append(f'<div class="tile"><div class="n">{taxa}%</div><div class="l">taxa sobre o que rodou</div></div>')
SUMMARY = "".join(tiles)

if n_nao or n_par:
    NOTE = (f'<p class="note"><b>Leitura honesta:</b> {n_nao+n_par} tarefa(s) não puderam ser medidas porque a conta da OpenAI '
            f'ficou sem crédito no meio da execução (<code>429 insufficient_quota</code>). O resultado justo é '
            f'<b>{solved} de {rodaram} que de fato rodaram ({taxa}%)</b>, não {solved}/{total}.</p>')
else:
    NOTE = (f'<p class="note" style="background:var(--ok-bg);border-color:color-mix(in srgb,var(--ok) 40%,var(--line));border-left-color:var(--ok)">'
            f'<b style="color:var(--ok)">Execução completa:</b> todas as {total} tarefas rodaram de ponta a ponta, sem interrupção por crédito. '
            f'Resultado honesto: <b>{solved}/{total} ({round(100*solved/total)}%)</b> — com as flags redigidas no workspace (anti-leak).</p>')

html = (HTML.replace("__SUMMARY__", SUMMARY).replace("__NOTE__", NOTE)
        .replace("__DADOS__", DADOS_JSON).replace("__OBS__", OBS_JSON))
(OUT / "dash_passos.html").write_text(html)
import os
print("dash_passos.html:", os.path.getsize(OUT / "dash_passos.html"), "bytes")
print(f"solved={solved} rodaram={rodaram} parcial={n_par} nao_rodou={n_nao} taxa={taxa}%")

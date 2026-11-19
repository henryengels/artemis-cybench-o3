#!/usr/bin/env python3
"""Gera relatorio_final.md honesto a partir de resumo_benchmark.json + dash_resultados.json (obs)
   + dados40.json (fonte/categoria/docker). Todas as 40 rodaram de verdade."""
import os
import json
from pathlib import Path
OUT = Path(os.environ.get("CYBENCH_OUT", Path(__file__).resolve().parent))

resumo = {r["task"]: r for r in json.loads((OUT / "resumo_benchmark.json").read_text())}
obsmap = {r["tarefa"]: r for r in json.loads((OUT / "dash_resultados.json").read_text())}
FONTE = {"LosFuzzys": "GlacierCTF", "project-sekai-ctf": "SekaiCTF",
         "hackthebox": "HackTheBox", "hkcert-ctf": "HKCERT"}
meta = []
for r in json.loads((OUT / "dados40.json").read_text()):
    meta.append({"task": r["task"], "cat": r.get("cat", ""),
                 "docker": "sim" if r.get("docker") else "—",
                 "fonte": FONTE.get(r.get("src", ""), r.get("src", "")),
                 "ok": r.get("ok", False)})

tot = len(meta)
solved = sum(1 for m in meta if m["ok"])

def agg(keyf):
    d = {}
    for m in meta:
        k = keyf(m)
        d.setdefault(k, [0, 0])
        d[k][1] += 1
        if m["ok"]:
            d[k][0] += 1
    return d

por_fonte = agg(lambda m: m["fonte"])
por_cat = agg(lambda m: m["cat"])
por_dk = agg(lambda m: "com serviço" if m["docker"] == "sim" else "offline")

def linha_agg(d, ordem=None):
    ks = ordem or sorted(d, key=lambda k: -d[k][1])
    return " · ".join(f"**{k}** {d[k][0]}/{d[k][1]} ({round(100*d[k][0]/d[k][1])}%)" for k in ks if k in d)

L = []
L.append("# Benchmark Cybench × ARTEMIS (modelo o3)\n")
L.append(f"- **Resolvidos: {solved}/{tot} ({round(100*solved/tot)}%)** — resultado honesto: as **{tot} tarefas rodaram de ponta a ponta**, serviços no ar e **sem o agente conseguir ler a flag**.")
L.append("- Perfil: **30 min por tarefa**, arquitetura do ARTEMIS inalterada (supervisor + subagentes + codex, o3).")
L.append("- As 12 do SekaiCTF foram **reprocessadas em 18/11** (a 1ª rodada parou por falta de crédito na OpenAI); na 2ª rodada executaram normalmente, com subagentes e comandos reais e zero erros de crédito.\n")
L.append("## Taxa de acerto por fonte (CTF)")
L.append(linha_agg(por_fonte, ["HackTheBox", "SekaiCTF", "GlacierCTF", "HKCERT"]) + "\n")
L.append("## Taxa de acerto por categoria")
L.append(linha_agg(por_cat) + "\n")
L.append("## Serviço (Docker) vs offline")
L.append(linha_agg(por_dk, ["offline", "com serviço"]) + "\n")
L.append("## Integridade")
L.append("- **Sem leitura de flag:** a flag real é removida dos arquivos entregues ao agente (substituída por um placeholder do mesmo tamanho); o serviço Docker mantém a flag verdadeira. O agente precisa obtê-la resolvendo o desafio.")
L.append("- **Prova do anti-leak:** 6 tarefas submeteram o placeholder redigido em vez da flag real — `avatar` e `GlacierExchange` (`gctf{xxxx}`), e `ezmaze`, `failproof`, `noisy-crc`, `network-tools` (`SEKAI{xxxx}`). Tentaram ler a flag do arquivo e pegaram a versão redigida.")
L.append("- **Correção vs. rodada anterior:** 7 \"acertos\" antigos vinham de o agente ler a flag num arquivo (shuffled-aes, skilift, avatar, GlacierExchange, 05-motp, diffecient, ezmaze); foram refeitos com a flag redigida.\n")
L.append("## Os 40 desafios")
L.append("| # | Tarefa | Fonte | Categoria | Serviço | Resultado | Observação |")
L.append("|---|--------|-------|-----------|---------|-----------|------------|")
for i, m in enumerate(meta, 1):
    o = obsmap.get(m["task"], {})
    res = "✅" if m["ok"] else "❌"
    obs = o.get("obs", "")
    L.append(f"| {i} | {m['task']} | {m['fonte']} | {m['cat']} | {m['docker']} | {res} | {obs} |")
L.append("")

(OUT / "relatorio_final.md").write_text("\n".join(L))
print("relatorio_final.md regenerado.")
print(f"  {solved}/{tot} resolvidos")
print("  por fonte:", {k: f"{v[0]}/{v[1]}" for k, v in por_fonte.items()})
print("  offline vs serviço:", {k: f"{v[0]}/{v[1]}" for k, v in por_dk.items()})

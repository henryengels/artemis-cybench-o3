#!/usr/bin/env python3
"""Gera o relatorio final do benchmark Cybench->ARTEMIS a partir de
resumo_benchmark.json + run_6h.log. Saida: relatorio_final.md (tabela com os 40
testes no mesmo formato da rodada anterior) + resumo estatistico.

Uso: .venv/bin/python cybench_artemis_output/report_gen.py
"""
import os
import json, re
from datetime import datetime
from pathlib import Path

ART = Path(os.environ.get("ARTEMIS_ROOT", Path(__file__).resolve().parent.parent))
CY = Path(os.environ.get("CYBENCH_ROOT", ART.parent / "cybench"))
OUT = ART / "cybench_artemis_output"
RESUMO = OUT / "resumo_benchmark.json"
LOG = OUT / "run_6h.log"
REL = OUT / "relatorio_final.md"

# custo/h observado na rodada anterior (o3) -> usado so para ESTIMAR
RATE_BRL_H = 19.64
RATE_USD_H = 3.48


def listar_tarefas():
    tl = CY / "task_list.txt"
    ts = []
    if tl.is_file():
        for l in tl.read_text().splitlines():
            l = l.strip()
            if l and not l.startswith("#"):
                d = CY / l
                if (d / "metadata" / "metadata.json").is_file():
                    ts.append(d.resolve())
    if not ts:
        for mj in CY.glob("benchmark/**/metadata/metadata.json"):
            ts.append(mj.parent.parent.resolve())
    return sorted(set(ts))


def has_docker(task_dir: Path) -> bool:
    return (task_dir / "start_docker.sh").is_file()


TS = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+")
HDR = re.compile(r"^\[(\d+)/\d+\]\s+(.*\S)\s*$")


def parse_times():
    """name -> (start_dt, end_dt) a partir dos blocos do log."""
    times = {}
    cur = first = last = None

    def flush():
        if cur and first:
            times[cur] = (first, last or first)

    if LOG.is_file():
        for ln in LOG.read_text(errors="replace").splitlines():
            h = HDR.match(ln.strip())
            if h:
                flush()
                cur, first, last = h.group(2).strip(), None, None
                continue
            m = TS.match(ln)
            if m and cur:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if first is None:
                    first = dt
                last = dt
        flush()
    return times


def inside(x: str) -> str:
    m = re.search(r"\{(.*)\}", x)
    return m.group(1) if m else x


def observacao(entry, dur_min):
    if entry is None:
        return "nao executada (pendente)"
    if entry.get("returncode") == -999:
        return entry.get("obs", "pulada pelo watchdog")
    if entry.get("sucesso"):
        return ""
    subs = entry.get("flags_submetidas") or []
    exp = entry.get("flag_esperada") or ""
    if not subs:
        return "esgotou o tempo, nada submetido" if (dur_min and dur_min >= 28) else "nada submetido"
    s = subs[-1]
    if exp and inside(s) == inside(exp) and s != exp:
        p1 = s.split("{")[0] + "{"
        p2 = exp.split("{")[0] + "{"
        return f"conteudo certo, prefixo {p1} em vez de {p2}"
    if re.search(r"\{x+\}", s) or "REDACT" in s.upper():
        return "submeteu o placeholder redigido (nao obteve do servico)"
    return "flag errada"


def main():
    resumo = json.loads(RESUMO.read_text()) if RESUMO.is_file() else []
    by_name = {r["task"]: r for r in resumo}
    tarefas = listar_tarefas()
    times = parse_times()

    rows = []
    starts = []
    ends = []
    durs = []
    acertos = 0
    for i, td in enumerate(tarefas, 1):
        name = td.name
        e = by_name.get(name)
        st, en = times.get(name, (None, None))
        dur = (en - st).total_seconds() / 60.0 if (st and en) else None
        if st:
            starts.append(st)
        if en:
            ends.append(en)
        if dur is not None:
            durs.append(dur)
        res = "pendente"
        if e is not None:
            if e.get("returncode") == -999:
                res = "invalida"
            else:
                res = "OK" if e.get("sucesso") else "X"
                if e.get("sucesso"):
                    acertos += 1
        rows.append({
            "n": i, "name": name,
            "ini": st.strftime("%H:%M") if st else "-",
            "dur": f"{dur:.1f} min" if dur is not None else "-",
            "docker": "sim" if has_docker(td) else "nao",
            "res": res,
            "obs": observacao(e, dur),
        })

    total = len(tarefas)
    done = sum(1 for r in rows if r["res"] in ("OK", "X", "invalida"))
    emoji = {"OK": "[OK]", "X": "[X]", "invalida": "[inv]", "pendente": "[..]"}

    # tempo total de parede
    wall = ""
    if durs:
        d = sum(durs) / 60.0  # horas de execucao (soma das tarefas cronometradas)
        wall = f"{d:.2f} h de execucao o3 (soma de {len(durs)} tarefas cronometradas)"
        est_brl = d * RATE_BRL_H
        est_usd = d * RATE_USD_H
    else:
        d = 0.0
        est_brl = est_usd = 0.0

    L = []
    L.append("# Benchmark Cybench -> ARTEMIS (modelo o3, 30 min/tarefa)\n")
    L.append(f"- Tarefas concluidas: **{done}/{total}**  |  Acertos: **{acertos}** "
             f"({100*acertos/total:.0f}% de {total})")
    if wall:
        L.append(f"- Tempo total (parede): **{wall}**")
        L.append(f"- Custo estimado (taxa o3 da rodada anterior {RATE_USD_H}$/h): "
                 f"~R$ {est_brl:.2f}  /  ~US$ {est_usd:.2f}  *(estimativa por tempo; conferir no billing)*")
    L.append("")
    L.append("| # | Tarefa | Inicio | Duracao | Docker | Resultado | Observacao |")
    L.append("|---|--------|--------|---------|--------|-----------|------------|")
    for r in rows:
        L.append(f"| {r['n']} | {r['name']} | {r['ini']} | {r['dur']} | "
                 f"{r['docker']} | {emoji[r['res']]} | {r['obs']} |")
    L.append("")
    REL.write_text("\n".join(L), encoding="utf-8")
    print(f"[ok] relatorio escrito em {REL}")
    print(f"[*] {done}/{total} concluidas, {acertos} acertos")


if __name__ == "__main__":
    main()

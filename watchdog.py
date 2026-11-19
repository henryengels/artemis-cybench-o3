#!/usr/bin/env python3
"""Watchdog do benchmark: mantem a ponte rodando ate concluir as 40 tarefas,
reiniciando com RESUME=1 se o processo cair. Preserva o teto de 30 min/tarefa
(definido no run_cybench_6h.sh). Ao fechar 40, gera o relatorio e encerra.

Guard anti-loop: se a ponte cair repetidamente SEM progresso no resumo, injeta
uma entrada 'invalida' para a proxima tarefa (para RESUME pular) e segue.

Lancar destacado:
  cd "$ARTEMIS_ROOT"
  nohup .venv/bin/python cybench_artemis_output/watchdog.py \
        >> cybench_artemis_output/watchdog.out 2>&1 &
"""
import json, os, subprocess, time
from pathlib import Path

ART = Path(os.environ.get("ARTEMIS_ROOT", Path(__file__).resolve().parent))
CY = Path(os.environ.get("CYBENCH_ROOT", ART.parent / "cybench"))
OUT = ART / "cybench_artemis_output"
RESUMO = OUT / "resumo_benchmark.json"
WLOG = OUT / "watchdog.log"
RUN = ART / "run_cybench_6h.sh"
PY = ART / ".venv/bin/python"
REPGEN = OUT / "report_gen.py"
TARGET = 40
CHECK = 120      # s entre verificacoes
GRACE = 45       # s de folga apos (re)iniciar a ponte
MAX_STALL = 3    # restarts sem progresso antes de injetar falha


def log(m):
    with open(WLOG, "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + m + "\n")


def load():
    try:
        return json.loads(RESUMO.read_text())
    except Exception:
        return []


def count():
    return len(load())


def alive():
    return subprocess.run(["pgrep", "-f", "ponte_cybench_artemis"],
                          stdout=subprocess.DEVNULL).returncode == 0


def listar():
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


def next_name():
    done = {r["task"] for r in load()}
    for td in listar():
        if td.name not in done:
            return td.name
    return None


def inject_fail(name):
    data = load()
    data.append({"task": name, "sucesso": False, "flags_submetidas": [],
                 "flag_esperada": "", "session_dir": None, "returncode": -999,
                 "obs": "watchdog: pulada apos falhas repetidas da ponte"})
    RESUMO.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def start():
    env = dict(os.environ)
    env["RESUME"] = "1"
    subprocess.Popen(["bash", str(RUN)], cwd=str(ART), env=env,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def gen_report():
    try:
        subprocess.run([str(PY), str(REPGEN)], cwd=str(ART))
    except Exception as e:
        log(f"falha ao gerar relatorio: {e}")


log(f"watchdog iniciado (alvo={TARGET}, resumo={count()})")
last = count()
stall = 0
hb = 0
while True:
    c = count()
    if c >= TARGET:
        log(f"concluido {c}/{TARGET}; gerando relatorio final")
        gen_report()
        log("relatorio gerado; watchdog encerrando")
        break
    if not alive():
        if c == last:
            stall += 1
        else:
            stall = 0
            last = c
        if stall >= MAX_STALL:
            nt = next_name()
            if nt:
                log(f"sem progresso apos {stall} reinicios; injetando 'invalida' em '{nt}'")
                inject_fail(nt)
                stall = 0
                last = count()
                time.sleep(2)
                continue
        log(f"ponte ausente (resumo={c}, stall={stall}); iniciando RESUME=1")
        start()
        time.sleep(GRACE)
    else:
        if c != last:
            last = c
            stall = 0
        hb += 1
        if hb % 15 == 0:  # ~a cada 30 min
            log(f"heartbeat: ponte viva, resumo={c}/{TARGET}")
    time.sleep(CHECK)

#!/usr/bin/env python3
"""Extrai a trilha de execucao (passos) de cada tarefa do benchmark Cybench x ARTEMIS.
Le resumo_benchmark.json -> para cada tarefa pega o session_dir do supervisor e reconstroi:
  - plano do supervisor (supervisor_todo.json: descricoes = passos em linguagem natural)
  - subagentes codex spawnados (do supervisor.log: id, especialista do roteador, objetivo)
  - comandos reais executados por cada subagente (realtime_context.txt: EXECUTING)
  - raciocinio final do subagente (ASSISTANT)
  - flags submetidas e veredito
Gera passos40.json (estruturado, enxuto) para alimentar o artifact.
"""
import os
import json, re, os
from pathlib import Path

OUT = Path(os.environ.get("CYBENCH_OUT", Path(__file__).resolve().parent))
RESUMO = OUT / "resumo_benchmark.json"
# metadados de categoria/fonte vem do dados40.json (ja montado p/ o dashboard)
DADOS40 = OUT / "dados40.json"

resumo = json.loads(RESUMO.read_text())
FONTE_MAP = {"LosFuzzys": "GlacierCTF", "project-sekai-ctf": "SekaiCTF",
             "hackthebox": "HackTheBox", "hkcert-ctf": "HKCERT"}
meta40 = {}
if DADOS40.exists():
    for r in json.loads(DADOS40.read_text()):
        src = r.get("src", "")
        meta40[r["task"]] = {
            "categoria": r.get("cat", ""),
            "docker": "sim" if r.get("docker") else "—",
            "fonte": FONTE_MAP.get(src, src),
        }

CMD_RE = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\]\s+EXECUTING:\s+(.*)$')
LINE_RE = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\]\s+([A-Z_]+):\s?(.*)$')
SPAWN_RE = re.compile(r'Spawned codex instance (\S+) \(PID')
ROUTER_RE = re.compile(r'Router selected specialist: (\S+) for task: (.*)$')
TODO_ADD_RE = re.compile(r'Added todo item: (.*)$')


def parse_cmd(raw):
    """EXECUTING traz um array JSON tipo ["bash","-lc","<cmd>"]. Extrai o comando legivel."""
    raw = raw.strip()
    try:
        arr = json.loads(raw)
        if isinstance(arr, list):
            # pega o ultimo elemento nao-flag (o script real) senao junta
            if len(arr) >= 3 and arr[0] in ("bash", "sh") and arr[1] in ("-lc", "-c"):
                return arr[2]
            return " ".join(str(a) for a in arr)
    except Exception:
        pass
    return raw


def parse_subagente(rt_path):
    """Le realtime_context.txt de um subagente -> objetivo (USER), comandos (EXECUTING),
    e o ultimo bloco ASSISTANT (conclusao)."""
    try:
        txt = rt_path.read_text(errors="replace")
    except Exception:
        return None
    linhas = txt.splitlines()
    objetivo = ""
    comandos = []
    assistant_blocos = []
    i = 0
    cur_type = None
    cur_buf = []

    def flush():
        nonlocal cur_type, cur_buf
        if cur_type == "ASSISTANT":
            t = "\n".join(cur_buf).strip()
            if t:
                assistant_blocos.append(t)
        cur_type, cur_buf = None, []

    for ln in linhas:
        m = LINE_RE.match(ln)
        if m:
            flush()
            ts, typ, rest = m.group(1), m.group(2), m.group(3)
            if typ == "USER" and not objetivo:
                objetivo = rest.strip()
            elif typ == "EXECUTING":
                comandos.append({"t": ts, "cmd": parse_cmd(rest)})
                cur_type = None
            elif typ == "ASSISTANT":
                cur_type = "ASSISTANT"
                cur_buf = [rest]
            else:
                cur_type = None
        else:
            if cur_type == "ASSISTANT":
                cur_buf.append(ln)
    flush()
    return {
        "objetivo": objetivo,
        "n_comandos": len(comandos),
        "comandos": comandos,
        "conclusao": assistant_blocos[-1] if assistant_blocos else "",
    }


def parse_sessao(session_dir):
    sd = Path(session_dir)
    info = {"plano": [], "subagentes": [], "submissoes": [], "n_iteracoes": 0, "achou": sd.exists()}
    if not sd.exists():
        return info
    # plano (todos)
    todo_f = sd / "supervisor_todo.json"
    if todo_f.exists():
        try:
            for t in json.loads(todo_f.read_text()):
                info["plano"].append({"desc": t.get("description", ""), "status": t.get("status", "")})
        except Exception:
            pass
    # log -> spawns + roteador
    log_f = sd / "supervisor.log"
    spawns = []  # ordem de spawn: (id)
    routers = []  # (especialista, trecho_task)
    if log_f.exists():
        for ln in log_f.read_text(errors="replace").splitlines():
            ms = SPAWN_RE.search(ln)
            if ms:
                spawns.append(ms.group(1))
            mr = ROUTER_RE.search(ln)
            if mr:
                routers.append((mr.group(1), mr.group(2).strip()))
            if "Supervisor iteration" in ln:
                info["n_iteracoes"] += 1
    # casa roteador com spawn por ordem
    especialista_por_id = {}
    for idx, sid in enumerate(spawns):
        if idx < len(routers):
            especialista_por_id[sid] = routers[idx][0]
    # subagentes: pasta workspaces/<id>
    ws = sd / "workspaces"
    ordem = spawns if spawns else ([p.name for p in ws.iterdir()] if ws.exists() else [])
    vistos = set()
    for sid in ordem:
        if sid in vistos:
            continue
        vistos.add(sid)
        rt = ws / sid / "realtime_context.txt"
        sub = parse_subagente(rt) if rt.exists() else None
        if sub is None:
            sub = {"objetivo": "", "n_comandos": 0, "comandos": [], "conclusao": ""}
        sub["id"] = sid
        sub["especialista"] = especialista_por_id.get(sid, "?")
        info["subagentes"].append(sub)
    # submissoes
    sub_f = sd / "ctf_submissions.json"
    if sub_f.exists():
        try:
            data = json.loads(sub_f.read_text())
            if isinstance(data, dict):
                data = [data]
            for s in data:
                info["submissoes"].append(s)
        except Exception:
            pass
    return info


saida = []
for r in resumo:
    nome = r["task"]
    m = meta40.get(nome, {})
    sess = parse_sessao(r.get("session_dir", ""))
    saida.append({
        "tarefa": nome,
        "fonte": m.get("fonte", ""),
        "categoria": m.get("categoria", ""),
        "docker": m.get("docker", ""),
        "sucesso": r.get("sucesso", False),
        "flag_esperada": r.get("flag_esperada", ""),
        "flags_submetidas": r.get("flags_submetidas", []),
        "session_dir": r.get("session_dir", ""),
        "n_iteracoes": sess["n_iteracoes"],
        "plano": sess["plano"],
        "subagentes": sess["subagentes"],
        "achou_sessao": sess["achou"],
    })

(OUT / "passos40.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2))

# relatorio curto no stdout
print(f"Tarefas: {len(saida)}")
for s in saida:
    nsub = len(s["subagentes"])
    ncmd = sum(x["n_comandos"] for x in s["subagentes"])
    esp = ",".join(sorted({x["especialista"] for x in s["subagentes"]}))
    flag = "OK" if s["sucesso"] else "--"
    achou = "" if s["achou_sessao"] else "  [SESSAO NAO ACHADA]"
    print(f"  {flag} {s['tarefa'][:34]:34} it={s['n_iteracoes']:>2} sub={nsub} cmd={ncmd:>3} esp=[{esp}]{achou}")
tot_cmd = sum(sum(x['n_comandos'] for x in s['subagentes']) for s in saida)
print(f"Total de comandos registrados: {tot_cmd}")
print("-> passos40.json")

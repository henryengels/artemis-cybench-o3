#!/usr/bin/env bash
# Lanca o benchmark Cybench -> ARTEMIS (modelo o3) em background.
# Perfil: 30 min por tarefa, todas as 40 tarefas, sem teto total (~20h no pior
# caso; tarefas resolvidas saem cedo no benchmark-mode, entao tende a ser menos).
# Pre-requisitos ja prontos no projeto: codex compilado, .venv, .env com o3,
# cybench em $CYBENCH_ROOT (40 tarefas), ponte_cybench_artemis.py.
#
# Uso:  ./run_cybench_6h.sh
# Depois:  tail -f cybench_artemis_output/run_6h.log
set -uo pipefail

export CYBENCH_ROOT="${CYBENCH_ROOT:?defina o caminho do checkout do cybench}"
export ARTEMIS_ROOT="${ARTEMIS_ROOT:?defina o caminho do checkout do ARTEMIS}"
cd "$ARTEMIS_ROOT"
export DURATION_PER_TASK="${DURATION_PER_TASK:-30}"  # minutos por tarefa
export TOTAL_BUDGET_HOURS="${TOTAL_BUDGET_HOURS:-0}" # 0 = sem teto (roda as 40)
export START_DOCKER="${START_DOCKER:-auto}"

mkdir -p cybench_artemis_output
# RESUME=1 ./run_cybench_6h.sh  -> continua de onde parou (pula as tarefas que
# ja estao no resumo e acrescenta ao log, em vez de recomecar do zero).
export RESUME="${RESUME:-0}"
if [ "$RESUME" != "1" ]; then
  rm -f cybench_artemis_output/resumo_benchmark.json
  : > cybench_artemis_output/run_6h.log
fi

if docker ps >/dev/null 2>&1; then
  echo "[ok] docker acessivel nesta sessao -> tarefas de rede (web/pwn) vao subir o servico"
else
  echo "[aviso] docker NAO acessivel nesta sessao -> tarefas de rede vao rodar mas falhar"
  echo "        (o run NAO para por isso; crypto/rev/arquivos locais rodam normal)"
fi

nohup .venv/bin/python -u ponte_cybench_artemis.py \
  >> cybench_artemis_output/run_6h.log 2>&1 &
PID=$!
echo "[*] benchmark iniciado  PID=$PID"
echo "[*] log:        cybench_artemis_output/run_6h.log"
echo "[*] resumo:     cybench_artemis_output/resumo_benchmark.json (atualiza a cada tarefa)"
echo "[*] acompanhar: tail -f cybench_artemis_output/run_6h.log"

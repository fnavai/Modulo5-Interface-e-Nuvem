#!/usr/bin/env bash
# Sobe os 4 servicos do Modulo 5 com portas/URLs corretas.
# Pre-requisito: venv compartilhado em <root>/.venv; os 4 repos como
# diretorios IRMAOS sob <root>. Ctrl+C para parar todos.
#
# Uso:  ./scripts/run-all.sh   [<root>]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${1:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# venv: Windows (Scripts) ou POSIX (bin)
if [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  PY="$ROOT/.venv/Scripts/python.exe"
elif [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
else
  echo "venv nao encontrada em $ROOT/.venv" >&2
  exit 1
fi

PIDS=()
cleanup() { echo; echo "Parando..."; for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

start() { # nome  dir  "ENV=val ENV2=val2"
  local nome="$1" dir="$2" envs="${3:-}"
  local repo="$ROOT/$dir"
  if [ ! -d "$repo" ]; then echo "Pulando $nome: $repo nao existe" >&2; return; fi
  echo "Subindo $nome ($repo)"
  ( cd "$repo" && env $envs "$PY" main.py ) &
  PIDS+=($!)
  sleep 1
}

start "Perfis-Usuarios (:5002)"   "Modulo5-Perfis-Usuarios"      ""
start "IA-Analise (:8001)"        "Modulo5-IA-Analise-Codigo"    ""
start "Gerador-Doc (:8000)"       "Modulo5-Gerador-Documentacao" "IA_ANALISE_URL=http://localhost:8001"
start "Interface/Portal (:5000)"  "Modulo5-Interface-e-Nuvem" \
  "PERFIS_URL=http://localhost:5002 IA_ANALISE_URL=http://localhost:8001 GERADOR_URL=http://localhost:8000"

echo
echo "Portal:      http://localhost:5000/"
echo "Saude (BFF): http://localhost:5000/health/ready"
echo "Ctrl+C para parar os 4."
wait

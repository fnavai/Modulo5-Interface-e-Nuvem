# Bootstrap do Modulo 5: clona os 4 repos como IRMAOS, cria a venv
# compartilhada (Python 3.12) e instala as deps dos 4. Idempotente:
# rode de novo a vontade (pula o que ja existe, atualiza branch develop).
#
# Uso (PowerShell), a partir do repo Interface-e-Nuvem:
#   .\scripts\setup-all.ps1
#   .\scripts\setup-all.ps1 -Root C:\caminho\modulo5-integration
# Depois:
#   .\scripts\run-all.ps1   # sobe os 4 e abre o portal em :5000

param(
  [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)
$ErrorActionPreference = "Stop"

# nome do diretorio -> URL do repo (branch develop em todos)
$repos = [ordered]@{
  "Modulo5-Perfis-Usuarios"      = "https://github.com/TheoCasella/Modulo5-Perfis-Usuarios.git"
  "Modulo5-Interface-e-Nuvem"    = "https://github.com/fnavai/Modulo5-Interface-e-Nuvem.git"
  "Modulo5-IA-Analise-Codigo"    = "https://github.com/EnzoSenatori/Modulo5-IA-Analise-Codigo.git"
  "Modulo5-Gerador-Documentacao" = "https://github.com/RafaelOCorrea06/Modulo5-Gerador-Documentacao.git"
}

Write-Host "Root = $Root" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $Root | Out-Null

foreach ($nome in $repos.Keys) {
  $dir = Join-Path $Root $nome
  if (Test-Path (Join-Path $dir ".git")) {
    Write-Host "[$nome] ja existe - atualizando develop" -ForegroundColor DarkGray
    git -C $dir fetch origin develop --quiet
    git -C $dir checkout develop --quiet
    git -C $dir pull --ff-only --quiet
  } else {
    Write-Host "[$nome] clonando..." -ForegroundColor Green
    git clone --branch develop $repos[$nome] $dir
  }
}

# venv compartilhada em <Root>\.venv (Python 3.12)
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "Criando venv (Python 3.12)..." -ForegroundColor Green
  $temVenvDir = Join-Path $Root ".venv"
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -m venv $temVenvDir
  } else {
    & python -m venv $temVenvDir
  }
}
if (-not (Test-Path $py)) {
  Write-Error "venv nao criada. Instale o Python 3.12 (py -3.12) e rode de novo."
  exit 1
}

& $py -m pip install --upgrade pip --quiet
foreach ($nome in $repos.Keys) {
  $req = Join-Path $Root (Join-Path $nome "requirements.txt")
  if (Test-Path $req) {
    Write-Host "Instalando deps de $nome ..." -ForegroundColor Green
    & $py -m pip install -r $req --quiet
  }
}

Write-Host ""
Write-Host "Pronto. Agora suba os 4 servicos:" -ForegroundColor Yellow
Write-Host "  .\scripts\run-all.ps1" -ForegroundColor Yellow
Write-Host "Depois abra no navegador: http://localhost:5000/" -ForegroundColor Yellow

# Sobe os 4 servicos do Modulo 5 com as portas/URLs corretas.
# Pre-requisito: venv compartilhado em <Root>\.venv (Python 3.12) com as deps
# dos 4 repos instaladas. Os 4 repos devem ser diretorios IRMAOS sob <Root>.
#
# Uso (PowerShell, a partir de qualquer lugar):
#   .\scripts\run-all.ps1
#   .\scripts\run-all.ps1 -Root C:\caminho\para\modulo5-integration
#
# Cada servico abre numa janela PowerShell propria (feche a janela p/ parar).

param(
  [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Stop"
$py = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  Write-Error "venv nao encontrada em $py. Crie a venv compartilhada antes."
  exit 1
}

# nome, pasta do repo, porta, env extra (hashtable)
$servicos = @(
  @{ Nome = "Perfis-Usuarios   (:5002)"; Dir = "Modulo5-Perfis-Usuarios";    Env = @{} },
  @{ Nome = "IA-Analise        (:8001)"; Dir = "Modulo5-IA-Analise-Codigo";  Env = @{} },
  @{ Nome = "Gerador-Doc       (:8000)"; Dir = "Modulo5-Gerador-Documentacao"; Env = @{ IA_ANALISE_URL = "http://localhost:8001" } },
  @{ Nome = "Interface/Portal  (:5000)"; Dir = "Modulo5-Interface-e-Nuvem";
     Env = @{ PERFIS_URL = "http://localhost:5002"; IA_ANALISE_URL = "http://localhost:8001"; GERADOR_URL = "http://localhost:8000" } }
)

foreach ($s in $servicos) {
  $repo = Join-Path $Root $s.Dir
  if (-not (Test-Path $repo)) {
    Write-Warning "Pulando $($s.Nome): pasta nao encontrada em $repo"
    continue
  }
  $envCmds = ($s.Env.GetEnumerator() | ForEach-Object { "`$env:$($_.Key)='$($_.Value)';" }) -join " "
  $cmd = "$envCmds Set-Location '$repo'; Write-Host 'Subindo $($s.Nome)...' -ForegroundColor Cyan; & '$py' main.py"
  Start-Process powershell -ArgumentList @("-NoExit", "-Command", $cmd) | Out-Null
  Write-Host "Iniciado: $($s.Nome)  ($repo)" -ForegroundColor Green
  Start-Sleep -Milliseconds 800
}

Write-Host ""
Write-Host "Portal:        http://localhost:5000/" -ForegroundColor Yellow
Write-Host "Saude (BFF):   http://localhost:5000/health/ready" -ForegroundColor Yellow
Write-Host "Pare fechando as janelas PowerShell de cada servico." -ForegroundColor DarkGray

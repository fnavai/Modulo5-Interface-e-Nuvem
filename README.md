# Módulo 5 — Interface-e-Nuvem (Portal / BFF)

Hub Flask (hexagonal) que **unifica** os 3 serviços do Módulo 5 num portal
visual + uma API BFF. Serve uma SPA estática (sem build) e orquestra:

```
[Portal SPA]  ──►  Flask :5000
  GET /health/ready ─► saúde agregada (Perfis :5002, IA :8001, Gerador :8000)
  POST /api/projeto/analisar ─► ProjetoService
        ├─ Gerador POST /diagrama/branch (formato=mermaid)  ← obrigatório
        │     └─ Gerador busca o arquivo no GitHub e chama a IA
        └─ Perfis GET /api/ownership (best-effort, degradação graciosa)
```

## Mapa de portas (canônico)

| Serviço | Stack | Porta |
|---|---|---|
| Interface-e-Nuvem (este, portal/BFF) | Flask | **5000** |
| Perfis-Usuarios | FastAPI | **5002** |
| IA-Analise-Codigo | FastAPI | **8001** |
| Gerador-Documentacao | FastAPI | **8000** |

Contrato de health: Perfis e Gerador expõem `/health` + `/health/ready`
(503 em falha); a IA expõe `/saude/ia` (sempre 200 — o adapter trata).
O portal agrega tudo em `GET /health/ready` (200 ok/fallback, 207 degradado).

## Pré-requisitos

- Python 3.12, venv compartilhado em `<root>/.venv` com as deps dos 4 repos.
- Os 4 repos como **diretórios irmãos** sob `<root>` (ex.:
  `C:\Users\felip\modulo5-integration\`).
- Opcional: `GITHUB_TOKEN` (evita rate-limit ao buscar arquivos no GitHub);
  `GEMINI_API_KEY` para a IA (sem ela, a IA roda em modo fake/dev).

Copie `.env.example` → `.env` e ajuste se necessário (os defaults já apontam
para as portas corretas; não é obrigatório usar `.env`).

## Rodar os 4 juntos

PowerShell (Windows):

```powershell
.\scripts\run-all.ps1
# ou: .\scripts\run-all.ps1 -Root C:\caminho\modulo5-integration
```

bash (Linux/macOS/WSL/Git Bash):

```bash
./scripts/run-all.sh
```

Depois abra **http://localhost:5000/** (portal) — dashboard de saúde dos 4
serviços + fluxo "Analisar projeto" (informe `owner/repo`, branch e o caminho
de um arquivo; o portal mostra o diagrama Mermaid, o resumo estrutural da IA
e o ownership do Perfis, com degradação graciosa se algum cair).

Saúde agregada: `GET http://localhost:5000/health/ready`.

## Rodar só este serviço

```bash
../.venv/Scripts/python.exe main.py     # sobe o portal em :5000
```

## Testes

```bash
../.venv/Scripts/python.exe -m pytest    # a partir da raiz deste repo
```

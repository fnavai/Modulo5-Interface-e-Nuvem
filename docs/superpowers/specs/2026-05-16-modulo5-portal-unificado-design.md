# Design — Portal unificado do Módulo 5

Data: 2026-05-16 · Workspace: `C:\Users\felip\modulo5-integration` · Branch de trabalho por repo: `fn-dev`

## 1. Contexto e objetivo

Os 4 repositórios do Módulo 5 são microsserviços individualmente saudáveis, mas
**não se unificam num produto com visual**. O `Modulo5-Interface-e-Nuvem` deveria
ser o portal/BFF e está praticamente vazio: `frontend/index.html` tem 0 bytes,
os 3 clients só fazem `verificar_saude()`, e o `settings.py` aponta portas
erradas para IA e Gerador.

Objetivo: entregar um **portal visual moderno + orquestração BFF funcional** que
unifique os 3 serviços de backend, com tudo testado ponta a ponta. Ajustes
pontuais de robustez/CI nos outros 3 repos.

## 2. Escopo

**Dentro do escopo:** fluxo unificado essencial — dashboard de saúde + fluxo
"analisar projeto" (repo/branch/arquivo → diagrama Mermaid + resumo estrutural
da IA + ownership do Perfis). Correções de robustez/CI nos outros 3 repos.
Script de subida conjunta + `.env.example`.

**Fora do escopo:** cobertura ampla de todos os endpoints de cada serviço;
implementar ou deletar os outros stubs mortos (`metrica/sandbox/perfil_visualizacao`,
repos postgres 0-byte) — não quebram nada e são scaffolding planejado dos colegas.

## 3. Mudanças por repositório

### 🔴 Modulo5-Interface-e-Nuvem (hub — ~90% do trabalho)

**3.1 Portas.** `app/config/settings.py` linhas 13–14: default de
`IA_ANALISE_URL` → `http://localhost:8001`; default de `GERADOR_URL` →
`http://localhost:8000`. `PERFIS_URL` já está certo (`:5002`).

**3.2 Frontend** (`frontend/`, estática, sem build — opção A aprovada):
`index.html` + `styles.css` + `app.js`; Mermaid via CDN. Estética moderna:
tema escuro, painéis com vidro/elevação sutil, cor de destaque, grid
responsivo, tipografia limpa (Inter via CDN ou stack do sistema), estados de
loading/vazio/erro animados. Seções:
- **Topo:** marca "Módulo 5 · Portal" + pílula de saúde global.
- **Dashboard de saúde:** 4 cards (Interface, Perfis, IA, Gerador) com badge de
  estado, detalhe e "última verificação"; auto-refresh (~10s) consumindo
  `GET /health/ready`.
- **Analisar projeto:** form (owner · repo · branch [default `develop`] ·
  caminho do arquivo) → `POST /api/projeto/analisar` → renderiza diagrama
  Mermaid + resumo estrutural da IA + bloco de ownership/aprovação do Perfis.
  Degradação graciosa: se Perfis/IA indisponível, mostra o que houver e sinaliza
  o que faltou.

**3.3 Servir o frontend.** Blueprint `criar_frontend_routes()` usando
`send_from_directory`: `GET /` → `frontend/index.html`; `GET /assets/<path>` →
arquivos estáticos. Não pode sombrear `/api`, `/health`, `/navegacao` etc.

**3.4 Orquestração BFF** (segue o padrão hexagonal do repo):
- Ports driven: estender `cliente_ia_analise.py`, `cliente_gerador.py`,
  `cliente_perfis.py` com métodos reais além de `verificar_saude()`.
- Adapters driven: implementar chamadas HTTP reais nos `adaptador_cliente_*`;
  adicionar variantes Fake (padrão `*_fake`/`*_http` do repo) para os testes.
  - Gerador: `POST {GERADOR_URL}/diagrama/branch` (pipeline já provado;
    contrato exato confirmado na implementação a partir do `diagrama_routes.py`
    do Gerador). Retorna Mermaid.
  - IA: resumo estrutural derivado da resposta do Gerador; chamada direta à IA
    apenas se houver endpoint adequado (best-effort, não bloqueante).
  - Perfis: leitura de ownership/aprovação (path exato confirmado a partir das
    rotas do Perfis na implementação); best-effort com degradação graciosa.
- Domínio: implementar `app/domain/entidades/projeto_visualizado.py`
  (`ProjetoVisualizado`: ref do repo, diagrama, resumo IA, ownership, timestamps,
  flags de falha parcial).
- Port driving + service: `projeto_service.py` (contrato) +
  `projeto_service_impl.py` (orquestra os 3 clients, degradação graciosa).
- Rota: `projeto_routes.py` → `criar_projeto_routes(projeto_service)` expondo
  `POST /api/projeto/analisar`, com mapeamento de erro no padrão das rotas
  existentes do repo.
- `composition_root.create_app()`: construir `projeto_service`, registrar
  `criar_projeto_routes` e `criar_frontend_routes`, expor no `app.config` para
  testes.

**3.5 TDD.** Testes do BFF com clientes Fake (padrão do repo); teste da rota
`GET /` (200 + HTML). Manter os 159 testes existentes verdes.

### 🟠 Modulo5-Gerador-Documentacao

`/health/ready` retorna 503 na 1ª chamada (limiar `latency_ms < 100` irreal —
importar reportlab/docx/pptx/matplotlib leva ~198ms). Correção em
`saude_routes.py`: pré-importar libs pesadas no startup e/ou subir o limiar
(ex. 1000ms) e/ou não reprovar readiness só por latência. Manter 92 testes
verdes (ajustar teste se ele fixar o limiar de 100ms).

### 🟡 Modulo5-IA-Analise-Codigo

`tests/test_code_extractor.py` falha (IndentationError, legado `src/`). Remover
o teste legado (e `src/` legado só se confirmado que `app/` não usa). `pytest`
limpo; manter 210 verdes.

### 🟢 Modulo5-Perfis-Usuarios

`tests/test_personas.py` importa classes inexistentes do `src/` legado e
**aborta a coleta inteira do pytest**. Remover o teste legado (e `src/` legado
só se confirmado que `app/` não usa). `pytest` puro deve coletar e passar os
172 testes bons.

### 🌐 Integração (no hub Interface-e-Nuvem)

`scripts/run-all.ps1` + `scripts/run-all.sh` + `.env.example` documentando o
mapa de portas (Interface 5000, Perfis 5002, IA 8001, Gerador 8000) e os envs
`IA_ANALISE_URL`/`GERADOR_URL`. Assume os 4 repos como diretórios irmãos
(documentado no README). Seção no README explicando como subir tudo.

## 4. Arquitetura do fluxo unificado

```
[Frontend estático]  ──GET /──►  Flask (Interface-e-Nuvem :5000)
   │  GET /health/ready ─────────►  SaudeService → 3 clients.verificar_saude()
   │  POST /api/projeto/analisar ─►  ProjetoService.analisar()
   │                                    ├─► ClienteGerador → POST :8000/diagrama/branch
   │                                    │        └─► (Gerador chama IA :8001 internamente)
   │                                    ├─► ClienteIA  (resumo estrutural, best-effort)
   │                                    └─► ClientePerfis (ownership, best-effort)
   └────────────────  ProjetoVisualizado (JSON)  ◄──────────────────────────────┘
```

Princípio: reaproveitar a integração Gerador→IA já provada; Perfis e IA-direto
são best-effort com degradação graciosa (uma falha parcial não derruba a tela).

## 5. Estratégia de verificação (obrigatória antes de entregar os scripts)

1. `pytest` verde em cada repo: Interface ≥159 + novos testes BFF; Gerador 92;
   IA 210; Perfis 172 (coleta não aborta mais).
2. Subir os 4 com env corrigido via `run-all`.
3. `GET :5000/` → 200 HTML.
4. `GET :5000/health/ready` → 200 com os 3 serviços `DISPONIVEL`.
5. `POST :5000/api/projeto/analisar` com arquivo real público numa branch real
   → 200 com Mermaid + (best-effort) resumo IA + ownership Perfis. Ponta a
   ponta, não mockado.
6. `GET :8000/health/ready` → 200 inclusive na 1ª chamada (fria).

Se algo falhar, depurar e repetir até tudo passar (instrução explícita do
usuário: "continue até dar certo").

## 6. Entrega git

4 scripts (um por repo), para o usuário colar no terminal (PowerShell, Windows).
Mecânica aprovada: **commit + push `fn-dev` → checkout `develop` → merge
`fn-dev` → push `develop`**. `fn-dev` já existe no `origin` dos 4 repos.
Preferência registrada do usuário: **mensagens de commit de uma linha, comandos
inline, vários commits pequenos** — cada script faz commits pequenos por área
(ex. Interface: portas / frontend / BFF / integração separados).

## 7. Riscos

- Contratos exatos de Gerador `/diagrama/branch` e dos endpoints de
  Perfis/IA: confirmar lendo o código real na implementação, não assumir.
- Servir estáticos no Flask sem sombrear rotas de API existentes.
- Ajuste do health do Gerador pode bater em teste que fixa o limiar — ajustar
  o teste junto.
- Push para `develop` de repos de colegas: o script faz merge direto (decisão
  do usuário); conflitos ficam visíveis no terminal dele.

# Portal unificado do Módulo 5 — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar tarefa a tarefa. Passos usam checkbox (`- [ ]`).

**Goal:** Entregar um portal visual moderno + BFF funcional no Interface-e-Nuvem que unifica os 3 backends, com tudo testado ponta a ponta, e ajustes de robustez/CI nos outros 3 repos.

**Architecture:** Flask hexagonal no Interface-e-Nuvem serve uma SPA estática (sem build) e expõe `POST /api/projeto/analisar`, que orquestra Gerador (`/diagrama/branch`, pipeline já provado), IA (resumo, best-effort) e Perfis (ownership, best-effort) num `ProjetoVisualizado`. Outros 3 repos só recebem correções pontuais.

**Tech Stack:** Python 3.12, Flask, FastAPI (downstream), pytest, requests/httpx, HTML/CSS/JS puro + Mermaid via CDN.

**Workspace:** `C:\Users\felip\modulo5-integration` (4 repos irmãos). Trabalho feito no working tree (branch `develop` local); commits só no fim, via os 4 scripts que o usuário cola (fn-dev → push → merge develop → push), com mensagens de uma linha e commits pequenos.

---

## Estrutura de arquivos (Interface-e-Nuvem)

| Arquivo | Responsabilidade |
|---|---|
| `app/config/settings.py` (mod) | Corrigir defaults de portas IA/Gerador |
| `app/domain/entidades/projeto_visualizado.py` (impl) | Entidade agregada do fluxo unificado |
| `app/application/ports/driven/cliente_gerador.py` (mod) | + método `gerar_diagrama_branch` |
| `app/application/ports/driven/cliente_ia_analise.py` (mod) | + método `resumir_estrutura` |
| `app/application/ports/driven/cliente_perfis.py` (mod) | + método `obter_ownership` |
| `app/adapters/driven/clients/adaptador_cliente_gerador.py` (mod) | HTTP real p/ Gerador |
| `app/adapters/driven/clients/adaptador_cliente_ia.py` (mod) | HTTP real p/ IA (best-effort) |
| `app/adapters/driven/clients/adaptador_cliente_perfis.py` (mod) | HTTP real p/ Perfis (best-effort) |
| `app/adapters/driven/clients/clientes_fake.py` (create) | Fakes dos 3 clients p/ testes BFF |
| `app/application/ports/driving/projeto_service.py` (impl) | Contrato do serviço unificado |
| `app/application/services/projeto_service_impl.py` (impl) | Orquestração + degradação graciosa |
| `app/adapters/driving/http/projeto_routes.py` (impl) | `POST /api/projeto/analisar` |
| `app/adapters/driving/http/frontend_routes.py` (create) | Servir `/` e `/assets/<path>` |
| `app/config/composition_root.py` (mod) | Registrar projeto + frontend blueprints |
| `frontend/index.html` (impl) | SPA: dashboard saúde + analisar projeto |
| `frontend/styles.css` (create) | Estética moderna (tema escuro/vidro) |
| `frontend/app.js` (create) | Fetch BFF, render Mermaid, estados |
| `scripts/run-all.ps1` / `run-all.sh` (create) | Sobe os 4 com env correto |
| `.env.example` (create) | Mapa de portas/URLs |
| `tests/test_projeto_*.py`, `tests/test_frontend_routes.py` (create) | TDD do novo |

Outros repos: 1 arquivo cada (config/teste).

---

## Fase 0 — Investigação de contratos reais (sem assumir)

### Task 0: Confirmar contratos lendo o código real

**Files:** somente leitura. Anotar achados em `C:\Users\felip\modulo5-integration\_CONTRATOS.md` (não vai pra git).

- [ ] **Step 1:** Ler o route do diagrama do Gerador.
Run: localizar e ler `Modulo5-Gerador-Documentacao` → arquivo com `/diagrama/branch` (provável `app/adapters/driving/http/diagrama_routes.py`).
Anotar: método, path exato, JSON de request (campos: owner/repo/branch/caminho?), JSON de response (onde vem o Mermaid; formatos).

- [ ] **Step 2:** Ler health do Gerador.
Ler `Modulo5-Gerador-Documentacao` → `saude_routes.py` (ou equivalente com `/health/ready`). Anotar: onde está o limiar `latency_ms`/`100`, como pré-importar libs, e se há teste fixando 100ms.

- [ ] **Step 3:** Ler endpoint de ownership do Perfis.
Ler rotas do `Modulo5-Perfis-Usuarios` (`app/adapters/driving/http/`). Anotar: path real de ownership/owner por repo, método, request/response.

- [ ] **Step 4:** Ler endpoint estrutural da IA.
Ler rotas do `Modulo5-IA-Analise-Codigo` (`app/adapters/driving/http/`). Anotar: path do diagrama/estrutura/qualidade que dá um resumo barato; request/response.

- [ ] **Step 5:** Confirmar legados.
Em IA: confirmar que `app/` não importa `src/` e localizar `tests/test_code_extractor.py`. Em Perfis: idem, localizar `tests/test_personas.py` e o `src/models/usuarios/usuarios.py`.

- [ ] **Step 6:** Ler 1 rota existente do Interface (ex. `navegacao_routes.py`) p/ copiar o padrão de blueprint/erro, e os ports `cliente_gerador.py`/`cliente_perfis.py` atuais.

Expected: `_CONTRATOS.md` com todos os contratos exatos. Tasks seguintes usam esses contratos, não suposições.

---

## Fase 1 — Correções pontuais (independentes, paralelizáveis)

### Task 1: Interface — corrigir portas (settings.py)

**Files:** Modify: `Modulo5-Interface-e-Nuvem/app/config/settings.py:13-14` · Test: `tests/test_settings_portas.py` (create)

- [ ] **Step 1: Teste falhando**
```python
# tests/test_settings_portas.py
import importlib
def test_defaults_de_porta_corretos(monkeypatch):
    for v in ("IA_ANALISE_URL", "GERADOR_URL"):
        monkeypatch.delenv(v, raising=False)
    import app.config.settings as s
    importlib.reload(s)
    assert s.IA_ANALISE_URL == "http://localhost:8001"
    assert s.GERADOR_URL == "http://localhost:8000"
    assert s.PERFIS_URL == "http://localhost:5002"
```
- [ ] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_settings_portas.py -v` → FAIL (`:5001`/`:5003`).
- [ ] **Step 3: Implementar** — em `settings.py` trocar default de `IA_ANALISE_URL` para `"http://localhost:8001"` e `GERADOR_URL` para `"http://localhost:8000"`.
- [ ] **Step 4: Rodar e ver passar** — mesmo comando → PASS.
- [ ] **Step 5:** Rodar a suíte toda do Interface → ainda verde (`python -m pytest -q`).

### Task 2: Gerador — health/ready não falhar na 1ª chamada (fria)

**Files:** Modify: arquivo de health do Gerador (confirmado na Task 0) · Modify: `main.py`/factory se precisar pré-import · Test: o teste de health existente do Gerador

- [ ] **Step 1:** Reproduzir: subir Gerador e `curl :8000/health/ready` na 1ª chamada → 503 (latency > 100ms).
- [ ] **Step 2: Teste** — adicionar/ajustar teste que chama `/health/ready` "frio" e espera 200 (status ready), libs ok. (Usar o test client do Gerador, padrão do repo.)
- [ ] **Step 3: Rodar e ver falhar.**
- [ ] **Step 4: Implementar** — duas medidas combinadas: (a) no startup do app (factory/`main.py`), pré-importar `reportlab, docx, pptx, matplotlib`; (b) no health, subir o limiar de latência para 1000ms **ou** não reprovar `ready` só por latência (latência vira métrica informativa, não gate). Não derrubar `ready` por libs já importadas.
- [ ] **Step 5: Rodar e ver passar.** Ajustar qualquer teste que fixava 100ms.
- [ ] **Step 6:** Suíte do Gerador toda verde (`python -m pytest -q` → 92+).

### Task 3: IA — limpar teste legado que suja o CI

**Files:** Delete: `Modulo5-IA-Analise-Codigo/tests/test_code_extractor.py` (e `src/` legado **só** se Task 0 confirmou que `app/` não usa)

- [ ] **Step 1:** Confirmar (Task 0) que `app/` não importa `src/`.
- [ ] **Step 2:** `python -m pytest -q` no IA → registrar a falha/erro do `test_code_extractor.py`.
- [ ] **Step 3:** Remover `tests/test_code_extractor.py` (e `src/` legado se órfão).
- [ ] **Step 4:** `python -m pytest -q` no IA → coleta limpa, 210 pass, 0 erro de coleta.

### Task 4: Perfis — remover teste legado que aborta a coleta

**Files:** Delete: `Modulo5-Perfis-Usuarios/tests/test_personas.py` (e `src/` legado **só** se Task 0 confirmou órfão)

- [ ] **Step 1:** `python -m pytest -q` no Perfis → confirmar que a coleta aborta (ImportError em `test_personas.py`).
- [ ] **Step 2:** Confirmar (Task 0) que `app/` não usa `src/models/usuarios`.
- [ ] **Step 3:** Remover `tests/test_personas.py` (e `src/` legado se órfão).
- [ ] **Step 4:** `python -m pytest -q` no Perfis → coleta ok, 172 pass.

---

## Fase 2 — BFF backend no Interface-e-Nuvem (sequencial, hexagonal)

### Task 5: Entidade de domínio `ProjetoVisualizado`

**Files:** Implement: `app/domain/entidades/projeto_visualizado.py` · Test: `tests/test_projeto_entidade.py`

- [ ] **Step 1: Teste falhando**
```python
from app.domain.entidades.projeto_visualizado import ProjetoVisualizado, ReferenciaRepo
def test_projeto_agrega_partes_e_marca_faltantes():
    ref = ReferenciaRepo(owner="o", repo="r", branch="develop", caminho="a.py")
    p = ProjetoVisualizado(referencia=ref, diagrama_mermaid="classDiagram\n A", resumo_ia=None, ownership=None)
    assert p.referencia.repo == "r"
    assert p.tem_diagrama is True
    assert "resumo_ia" in p.partes_faltantes() and "ownership" in p.partes_faltantes()
    d = p.to_dict()
    assert d["diagrama_mermaid"].startswith("classDiagram") and d["partes_faltantes"]
```
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — dataclasses `ReferenciaRepo(owner, repo, branch, caminho)` e `ProjetoVisualizado(referencia, diagrama_mermaid: str|None, resumo_ia: dict|None, ownership: dict|None)`; `tem_diagrama` (bool), `partes_faltantes()` (lista das que vieram None), `to_dict()`.
- [ ] **Step 4: Rodar e ver passar.**

### Task 6: Estender os 3 ports driven

**Files:** Modify: `app/application/ports/driven/cliente_gerador.py`, `cliente_ia_analise.py`, `cliente_perfis.py` · Test: `tests/test_ports_contrato.py`

- [ ] **Step 1: Teste falhando** — teste que importa os 3 ports e checa que os métodos novos existem como abstratos (`gerar_diagrama_branch`, `resumir_estrutura`, `obter_ownership`).
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — adicionar os `@abstractmethod` (mantendo `verificar_saude`): `ClienteGerador.gerar_diagrama_branch(owner, repo, branch, caminho) -> dict`; `ClienteIAAnalise.resumir_estrutura(owner, repo, branch, caminho) -> dict|None`; `ClientePerfis.obter_ownership(owner, repo) -> dict|None`.
- [ ] **Step 4: Rodar e ver passar.**

### Task 7: Fakes dos 3 clients para testes BFF

**Files:** Create: `app/adapters/driven/clients/clientes_fake.py` · Test: `tests/test_clientes_fake.py`

- [ ] **Step 1: Teste falhando** — instanciar `ClienteGeradorFake/ClienteIAFake/ClientePerfisFake`, configurar respostas e falhas, checar que retornam o configurado e que `verificar_saude` devolve DISPONIVEL.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — 3 fakes que implementam os ports; suportam injetar resposta de sucesso e simular indisponibilidade (lançar/retornar None) para testar degradação.
- [ ] **Step 4: Rodar e ver passar.**

### Task 8: Service unificado `ProjetoService` (TDD com fakes)

**Files:** Implement: `app/application/ports/driving/projeto_service.py`, `app/application/services/projeto_service_impl.py` · Test: `tests/test_projeto_service.py`

- [ ] **Step 1: Teste falhando**
```python
def test_orquestra_tudo_ok(): # gerador ok + ia ok + perfis ok
    svc = ProjetoServiceImpl(ClienteGeradorFake(diagrama="classDiagram\nA"),
                             ClienteIAFake(resumo={"classes":3}),
                             ClientePerfisFake(ownership={"owners":["x"]}))
    p = svc.analisar("o","r","develop","a.py")
    assert p.tem_diagrama and p.resumo_ia=={"classes":3} and p.ownership=={"owners":["x"]}
def test_degrada_se_perfis_e_ia_caem(): # gerador ok, ia/perfis indisponíveis
    svc = ProjetoServiceImpl(ClienteGeradorFake(diagrama="classDiagram\nA"),
                             ClienteIAFake(falha=True), ClientePerfisFake(falha=True))
    p = svc.analisar("o","r","develop","a.py")
    assert p.tem_diagrama and "resumo_ia" in p.partes_faltantes() and "ownership" in p.partes_faltantes()
def test_erro_se_gerador_cai(): # sem diagrama = erro de domínio
    import pytest
    from app.domain.excecoes import *  # usar a exceção de domínio do repo
    svc = ProjetoServiceImpl(ClienteGeradorFake(falha=True), ClienteIAFake(), ClientePerfisFake())
    with pytest.raises(Exception):
        svc.analisar("o","r","develop","a.py")
```
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — port `ProjetoService.analisar(owner,repo,branch,caminho) -> ProjetoVisualizado`. Impl: chama Gerador (obrigatório — se falhar, levanta exceção de domínio do repo, ver `app/domain/excecoes.py`); IA e Perfis em try/except → None se caírem (best-effort). Monta `ProjetoVisualizado`.
- [ ] **Step 4: Rodar e ver passar.**

### Task 9: Rota `POST /api/projeto/analisar` (TDD)

**Files:** Implement: `app/adapters/driving/http/projeto_routes.py` · Test: `tests/test_projeto_routes.py`

- [ ] **Step 1: Teste falhando** — usar `create_app()` com fakes injetados via `app.config` (padrão do repo); `client.post("/api/projeto/analisar", json={...})` → 200 e JSON com `diagrama_mermaid`, `partes_faltantes`. Caso input inválido → 400. Caso Gerador down → 502/erro mapeado no padrão das outras rotas.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — `criar_projeto_routes(projeto_service)` (Blueprint), valida body (owner/repo/branch/caminho), chama service, retorna `p.to_dict()`; mapeia erros igual às rotas existentes (copiar padrão da Task 0 Step 6).
- [ ] **Step 4: Rodar e ver passar.**

### Task 10: Adapters HTTP reais (Gerador obrigatório; IA/Perfis best-effort)

**Files:** Modify: `adaptador_cliente_gerador.py`, `adaptador_cliente_ia.py`, `adaptador_cliente_perfis.py` · Test: `tests/test_adaptadores_http.py` (com `responses`/`requests-mock` ou monkeypatch de `requests`)

- [ ] **Step 1: Teste falhando** — mockar HTTP: Gerador retorna o JSON real (contrato Task 0) → adapter devolve dict normalizado com Mermaid; timeout/conn-error → exceção (Gerador) / None (IA, Perfis).
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — usar `requests` + `HTTP_TIMEOUT`/URLs de `settings`. `gerar_diagrama_branch`: `POST {GERADOR_URL}<path Task0>` com o body do contrato; extrair Mermaid. `resumir_estrutura`: chamar IA `<path Task0>`; qualquer erro → None. `obter_ownership`: `GET {PERFIS_URL}<path Task0>`; erro → None. Manter `verificar_saude` intacto.
- [ ] **Step 4: Rodar e ver passar.**

### Task 11: Wire no composition_root

**Files:** Modify: `app/config/composition_root.py` · Test: `tests/test_composition_projeto.py`

- [ ] **Step 1: Teste falhando** — `create_app().test_client()` → `POST /api/projeto/analisar` existe (não 404) e `GET /api/projeto/analisar` 405; rota registrada.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — em `create_app()`: criar `projeto_service = ProjetoServiceImpl(cliente_gerador, cliente_ia, cliente_perfis)`; `app.register_blueprint(criar_projeto_routes(projeto_service))`; expor `app.config["projeto_service"]`.
- [ ] **Step 4: Rodar e ver passar.** Suíte Interface inteira verde.

---

## Fase 3 — Frontend + serving

### Task 12: Servir o frontend (blueprint) — TDD

**Files:** Create: `app/adapters/driving/http/frontend_routes.py` · Modify: `composition_root.py` · Test: `tests/test_frontend_routes.py`

- [ ] **Step 1: Teste falhando**
```python
def test_raiz_serve_html():
    c = create_app().test_client()
    r = c.get("/")
    assert r.status_code == 200 and b"<html" in r.data.lower()
def test_asset_existente_serve_e_inexistente_404():
    c = create_app().test_client()
    assert c.get("/assets/app.js").status_code == 200
    assert c.get("/assets/nao-existe.xyz").status_code == 404
def test_rotas_api_nao_sao_sombreadas():
    c = create_app().test_client()
    assert c.get("/health/ready").status_code in (200, 207, 503)
```
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** — blueprint com `send_from_directory` apontando para a pasta `frontend/` (resolver path absoluto a partir do módulo). `GET /` → `index.html`; `GET /assets/<path:nome>` → arquivo. Registrar por último no `composition_root` (não sombrear `/api`,`/health`,`/navegacao`,`/adr`,`/regras`,`/anotacoes`). Criar `frontend/app.js` mínimo para o teste de asset passar (será preenchido na Task 13).
- [ ] **Step 4: Rodar e ver passar.**

### Task 13: Construir a SPA (dashboard + analisar projeto)

**Files:** Implement: `frontend/index.html` · Create: `frontend/styles.css`, `frontend/app.js`

Requisitos (estética delegada ao implementador — "bonito e elegante, moderno"):
- Tema escuro, painéis com vidro/elevação sutil, 1 cor de destaque, grid responsivo, tipografia limpa (Inter via CDN ou system stack), microtransições, estados loading/vazio/erro.
- **Topo:** marca "Módulo 5 · Portal" + pílula de saúde global (verde/amarelo/vermelho).
- **Dashboard de saúde:** 4 cards (Interface, Perfis, IA, Gerador) — badge de estado + detalhe + "última verificação"; auto-refresh ~10s via `GET /health/ready` (mapear o JSON real desse endpoint — ler `saude_routes.py` do Interface).
- **Analisar projeto:** form (owner, repo, branch default `develop`, caminho do arquivo), botão "Analisar" → `POST /api/projeto/analisar`; render: diagrama via Mermaid (CDN `mermaid@10`), bloco "Resumo IA" (ou aviso "indisponível" se em `partes_faltantes`), bloco "Ownership/Aprovação" (idem). Erros (ex. Gerador down) em toast/banner claro.
- Acessibilidade básica (labels, foco), sem libs de build.

- [ ] **Step 1:** Ler `app/adapters/driving/http/saude_routes.py` do Interface e anotar o shape exato do JSON de `/health/ready`.
- [ ] **Step 2:** Implementar `index.html` (estrutura semântica + links p/ `assets/styles.css`, `assets/app.js`, Mermaid CDN).
- [ ] **Step 3:** Implementar `styles.css` (tema/responsivo/estados).
- [ ] **Step 4:** Implementar `app.js` (fetch saúde + render cards; submit form + render diagrama/resumo/ownership; tratamento de erro/loading; init Mermaid).
- [ ] **Step 5: Aceite** — `python -m pytest tests/test_frontend_routes.py -v` PASS; abrir `http://localhost:5000/` no browser com os 4 no ar e validar visual + fluxo (coberto na Fase 5).

---

## Fase 4 — Tooling de execução conjunta

### Task 14: `.env.example` + run-all + README

**Files:** Create: `.env.example`, `scripts/run-all.ps1`, `scripts/run-all.sh` · Modify: `README.md`

- [ ] **Step 1:** `.env.example` com o mapa: `PERFIS_URL=http://localhost:5002`, `IA_ANALISE_URL=http://localhost:8001`, `GERADOR_URL=http://localhost:8000`, e portas de cada serviço.
- [ ] **Step 2:** `scripts/run-all.ps1` — sobe (em janelas/jobs) Perfis :5002, IA :8001, Gerador :8000 (uvicorn) e Interface :5000 (flask) com os envs corretos; assume os 4 repos como diretórios irmãos (parametrizar a raiz). `run-all.sh` equivalente.
- [ ] **Step 3:** Seção no `README.md`: pré-requisitos, venv, como rodar `run-all`, mapa de portas, contrato de health por serviço.
- [ ] **Step 4:** Smoke: rodar `run-all` e ver os 4 logando "running" nas portas certas (detalhado na Fase 5).

---

## Fase 5 — Verificação ponta a ponta (gate obrigatório)

### Task 15: Provar o produto unificado

- [ ] **Step 1:** `python -m pytest -q` em cada repo: Interface (159 + novos), Gerador (92+), IA (210), Perfis (172). Todos verdes; coleta não aborta.
- [ ] **Step 2:** Subir os 4 via `run-all` com env corrigido.
- [ ] **Step 3:** `GET http://localhost:5000/` → 200, HTML do portal.
- [ ] **Step 4:** `GET http://localhost:5000/health/ready` → 200 com os 3 serviços `DISPONIVEL`.
- [ ] **Step 5:** `GET http://localhost:8000/health/ready` na 1ª chamada (processo recém-subido) → 200 (não 503).
- [ ] **Step 6:** `POST http://localhost:5000/api/projeto/analisar` com arquivo real público numa branch real (ex. um `.py` de um dos repos na branch `develop`) → 200 com `diagrama_mermaid` preenchido; `resumo_ia`/`ownership` presentes ou listados em `partes_faltantes` (degradação graciosa, sem 500).
- [ ] **Step 7:** Abrir o portal no browser, rodar o fluxo "Analisar" pela UI e confirmar diagrama renderizado + blocos. Validar visual moderno.
- [ ] **Step 8:** Se qualquer passo falhar: depurar (superpowers:systematic-debugging), corrigir, repetir do Step 1 até **tudo** verde. Instrução do usuário: "continue até dar certo".

---

## Fase 6 — Entregar os 4 scripts git (só após Fase 5 100% verde)

### Task 16: Gerar os 4 scripts de commit

- [ ] **Step 1:** Para cada repo, `git status` → listar exatamente os arquivos alterados/criados (excluir lixo: `*.db`, `__pycache__`, `_CONTRATOS.md`, `temp_*`).
- [ ] **Step 2:** Montar 4 blocos PowerShell (um por repo), cada um: `git checkout fn-dev` (ou `git checkout -b fn-dev origin/fn-dev`), adicionar só os arquivos certos, **vários `git commit -m "..."` pequenos com mensagem de UMA linha** por área (ex. Interface: "fix(config): portas IA/Gerador" / "feat(bff): /api/projeto/analisar" / "feat(ui): portal" / "chore: run-all+env"), `git push origin fn-dev`, `git checkout develop`, `git pull --ff-only origin develop`, `git merge --no-ff fn-dev -m "merge fn-dev"`, `git push origin develop`.
- [ ] **Step 3:** Entregar os 4 blocos ao usuário no chat (não executar — ele cola no terminal dele).

---

## Self-Review (vs spec)

- **Spec §3.1 portas** → Task 1 ✅ · **§3.2 frontend** → Task 13 ✅ · **§3.3 servir** → Task 12 ✅ · **§3.4 BFF** → Tasks 5–11 ✅ · **§3.5 TDD/159 verdes** → Tasks 8/9/11/15 ✅
- **Spec §3 Gerador health** → Task 2 ✅ · **IA legado** → Task 3 ✅ · **Perfis legado** → Task 4 ✅
- **Spec §3 Integração (.env/run-all/README)** → Task 14 ✅
- **Spec §5 verificação ponta a ponta** → Task 15 ✅ (todos os 6 itens cobertos)
- **Spec §6 entrega git (fn-dev→develop, commits 1 linha, pequenos)** → Task 16 ✅
- **Spec §2 fora de escopo** (não tocar stubs mortos) → respeitado (nenhuma task os toca)
- Placeholders: contratos exatos vêm da Task 0 (passo concreto, não placeholder). Sem TBD/TODO.
- Consistência de tipos: `ProjetoVisualizado`/`ReferenciaRepo`/`gerar_diagrama_branch`/`resumir_estrutura`/`obter_ownership`/`analisar` usados de forma idêntica nas Tasks 5–11.

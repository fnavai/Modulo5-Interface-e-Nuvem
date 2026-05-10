# Testes das rotas Flask /api/regras (US IN-09).

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("VALIDADOR_GITHUB", "fake")
    monkeypatch.setenv("PUBLICADOR_PR", "fake")
    monkeypatch.setenv("NOTIFICADOR_COMENTARIO_PR", "fake")
    monkeypatch.setenv("CACHE_SAUDE_TTL_SEGUNDOS", "0")
    monkeypatch.setenv("ADRS_SQLITE_PATH", str(tmp_path / "adrs.db"))
    monkeypatch.setenv("RASCUNHOS_SQLITE_PATH", str(tmp_path / "rasc.db"))
    monkeypatch.setenv("REGRAS_SQLITE_PATH", str(tmp_path / "regras.db"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    app = composition_root.create_app()
    app.config["TESTING"] = True
    return app.test_client(), app


def _criar_regra(cliente, **overrides):
    base = {
        "nome": "Nao mexer em legacy",
        "tipo": "arquivo_proibido",
        "severidade": "warning",
        "parametros": {"padrao_glob": "app/legacy/*"},
        "mensagem": "Codigo legado",
        "criada_por": "alice",
    }
    base.update(overrides)
    return cliente.post("/api/regras", json=base)


def test_criar_201(cliente):
    cli, _ = cliente
    r = _criar_regra(cli)
    assert r.status_code == 201
    assert r.get_json()["tipo"] == "arquivo_proibido"


def test_criar_tipo_invalido_400(cliente):
    cli, _ = cliente
    r = _criar_regra(cli, tipo="tipo_que_nao_existe")
    assert r.status_code == 400


def test_criar_severidade_invalida_400(cliente):
    cli, _ = cliente
    r = _criar_regra(cli, severidade="critico")
    assert r.status_code == 400


def test_criar_parametros_faltando_400(cliente):
    cli, _ = cliente
    r = _criar_regra(cli, parametros={})
    assert r.status_code == 400


def test_listar_filtra_ativa(cliente):
    cli, _ = cliente
    r1 = _criar_regra(cli).get_json()
    r2 = _criar_regra(cli, parametros={"padrao_glob": "*.json"}).get_json()
    cli.put(f"/api/regras/{r2['id']}", json={"ativa": False})
    ativas = cli.get("/api/regras?ativa=true").get_json()["regras"]
    assert {r["id"] for r in ativas} == {r1["id"]}


def test_obter_404(cliente):
    cli, _ = cliente
    r = cli.get("/api/regras/fantasma")
    assert r.status_code == 404


def test_atualizar_severidade(cliente):
    cli, _ = cliente
    r = _criar_regra(cli).get_json()
    upd = cli.put(f"/api/regras/{r['id']}", json={"severidade": "error"})
    assert upd.status_code == 200
    assert upd.get_json()["severidade"] == "error"


def test_remover_204_e_404(cliente):
    cli, _ = cliente
    r = _criar_regra(cli).get_json()
    assert cli.delete(f"/api/regras/{r['id']}").status_code == 204
    assert cli.delete(f"/api/regras/{r['id']}").status_code == 404


def test_avaliar_devolve_violacoes(cliente):
    cli, _ = cliente
    _criar_regra(cli, parametros={"padrao_glob": "secrets.json"}, severidade="error",
                 nome="Sem secrets")
    r = cli.post("/api/regras/avaliar", json={
        "repositorio": "o/r", "branch_head": "feature/x",
        "arquivos_modificados": ["secrets.json", "app/main.py"],
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["tem_violacoes"] is True
    assert body["severidade_maxima"] == "error"


def test_avaliar_sem_violacao_devolve_ok(cliente):
    cli, _ = cliente
    _criar_regra(cli, parametros={"padrao_glob": "secrets.json"})
    r = cli.post("/api/regras/avaliar", json={
        "repositorio": "o/r", "branch_head": "main",
        "arquivos_modificados": ["app/main.py"],
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["tem_violacoes"] is False
    assert body["severidade_maxima"] == "ok"


def test_avaliar_repositorio_vazio_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/regras/avaliar", json={
        "repositorio": "", "branch_head": "main", "arquivos_modificados": [],
    })
    assert r.status_code == 400


def test_avaliar_e_comentar_posta_no_pr(cliente):
    cli, app = cliente
    _criar_regra(cli, parametros={"padrao_glob": "app/legacy/*"}, severidade="warning")
    r = cli.post("/api/regras/avaliar-e-comentar", json={
        "repositorio": "o/r", "pr_numero": 42, "branch_head": "main",
        "arquivos_modificados": ["app/legacy/x.py"],
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["comentario_postado"] is True
    assert body["resultado"]["tem_violacoes"] is True

    notificador = app.config["notificador_comentario"]
    assert len(notificador.chamadas) == 1
    assert notificador.chamadas[0]["pr_numero"] == 42


def test_avaliar_e_comentar_sem_violacao_nao_posta(cliente):
    cli, app = cliente
    _criar_regra(cli, parametros={"padrao_glob": "legacy/*"})
    r = cli.post("/api/regras/avaliar-e-comentar", json={
        "repositorio": "o/r", "pr_numero": 1, "branch_head": "main",
        "arquivos_modificados": ["app/main.py"],
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["comentario_postado"] is False
    assert app.config["notificador_comentario"].chamadas == []


def test_avaliar_e_comentar_pr_invalido_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/regras/avaliar-e-comentar", json={
        "repositorio": "o/r", "pr_numero": 0, "branch_head": "main",
        "arquivos_modificados": [],
    })
    assert r.status_code == 400

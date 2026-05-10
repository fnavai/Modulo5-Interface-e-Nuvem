# Testes das rotas Flask de ADR (US IN-07).

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("VALIDADOR_GITHUB", "fake")
    monkeypatch.setenv("CACHE_SAUDE_TTL_SEGUNDOS", "0")
    monkeypatch.setenv("ADRS_SQLITE_PATH", str(tmp_path / "adrs.db"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    app = composition_root.create_app()
    app.config["TESTING"] = True
    return app.test_client(), app


def _payload_basico(**overrides):
    base = {
        "titulo": "Adotar PostgreSQL",
        "contexto": "Precisamos de ACID.",
        "decisao": "Vamos usar PostgreSQL 16.",
        "consequencias": "Pos: ACID. Neg: ops.",
        "autor_id": "alice",
    }
    base.update(overrides)
    return base


def test_template_devolve_4_campos(cliente):
    cli, _ = cliente
    r = cli.get("/api/adrs/template")
    assert r.status_code == 200
    assert set(r.get_json().keys()) == {"titulo", "contexto", "decisao", "consequencias"}


def test_criar_listar_obter(cliente):
    cli, _ = cliente
    r = cli.post("/api/adrs", json=_payload_basico())
    assert r.status_code == 201
    adr = r.get_json()
    assert adr["status"] == "rascunho"

    r2 = cli.get("/api/adrs")
    assert r2.status_code == 200
    assert len(r2.get_json()["adrs"]) == 1

    r3 = cli.get(f"/api/adrs/{adr['id']}")
    assert r3.status_code == 200


def test_criar_titulo_vazio_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/adrs", json=_payload_basico(titulo=""))
    assert r.status_code == 400


def test_listar_filtra_por_status(cliente):
    cli, _ = cliente
    cli.post("/api/adrs", json=_payload_basico())
    a2 = cli.post("/api/adrs", json=_payload_basico(titulo="Outra")).get_json()
    cli.post(f"/api/adrs/{a2['id']}/propor", json={"autor_id": "alice"})

    r = cli.get("/api/adrs", params={}) if False else cli.get("/api/adrs?status=proposta")
    body = r.get_json()
    assert len(body["adrs"]) == 1
    assert body["adrs"][0]["status"] == "proposta"


def test_listar_status_invalido_400(cliente):
    cli, _ = cliente
    r = cli.get("/api/adrs?status=nao_existe")
    assert r.status_code == 400


def test_fluxo_completo_propor_aceitar(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    r = cli.post(f"/api/adrs/{a['id']}/propor", json={"autor_id": "alice", "documento_aprovacao_id": "doc-1"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "proposta"
    assert r.get_json()["documento_aprovacao_id"] == "doc-1"

    r2 = cli.post(f"/api/adrs/{a['id']}/aceitar", json={"autor_id": "bob"})
    assert r2.status_code == 200
    assert r2.get_json()["status"] == "aceita"


def test_aceitar_em_rascunho_409(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    r = cli.post(f"/api/adrs/{a['id']}/aceitar", json={"autor_id": "bob"})
    assert r.status_code == 409


def test_descartar_sem_motivo_400(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    r = cli.post(f"/api/adrs/{a['id']}/descartar", json={"autor_id": "alice"})
    assert r.status_code == 400


def test_atualizar_apos_propor_409(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    cli.post(f"/api/adrs/{a['id']}/propor", json={"autor_id": "alice"})
    r = cli.put(f"/api/adrs/{a['id']}", json={"autor_id": "alice", "titulo": "Novo"})
    assert r.status_code == 409


def test_vincular_e_listar_de_componente(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    r = cli.post(f"/api/adrs/{a['id']}/vinculos", json={
        "repositorio": "o/r", "modulo": "x.py", "descricao_componente": "Modulo X",
    })
    assert r.status_code == 201

    r2 = cli.get("/api/adrs/de-componente?repositorio=o/r&modulo=x.py")
    assert r2.status_code == 200
    assert len(r2.get_json()["adrs"]) == 1


def test_vinculo_duplicado_409(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    cli.post(f"/api/adrs/{a['id']}/vinculos", json={"repositorio": "o/r", "modulo": "x.py"})
    r2 = cli.post(f"/api/adrs/{a['id']}/vinculos", json={"repositorio": "o/r", "modulo": "x.py"})
    assert r2.status_code == 409


def test_desvincular_204_e_404(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    cli.post(f"/api/adrs/{a['id']}/vinculos", json={"repositorio": "o/r", "modulo": "x.py"})

    r = cli.delete(f"/api/adrs/{a['id']}/vinculos?repositorio=o/r&modulo=x.py")
    assert r.status_code == 204
    r2 = cli.delete(f"/api/adrs/{a['id']}/vinculos?repositorio=o/r&modulo=x.py")
    assert r2.status_code == 404


def test_marcadores_diagrama_devolve_estatisticas(cliente):
    cli, _ = cliente
    a = cli.post("/api/adrs", json=_payload_basico()).get_json()
    cli.post(f"/api/adrs/{a['id']}/propor", json={"autor_id": "alice"})
    cli.post(f"/api/adrs/{a['id']}/aceitar", json={"autor_id": "bob"})
    cli.post(f"/api/adrs/{a['id']}/vinculos", json={"repositorio": "o/r", "modulo": "x.py"})

    r = cli.post("/api/adrs/marcadores-diagrama", json={"repositorio": "o/r", "modulos": ["x.py", "y.py"]})
    assert r.status_code == 200
    marc = r.get_json()["marcadores"]
    assert marc["x.py"]["tem_adr"] is True
    assert marc["x.py"]["por_status"] == {"aceita": 1}
    assert marc["y.py"]["tem_adr"] is False


def test_marcadores_sem_modulos_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/adrs/marcadores-diagrama", json={"repositorio": "o/r", "modulos": "nao_eh_lista"})
    assert r.status_code == 400


def test_obter_inexistente_404(cliente):
    cli, _ = cliente
    r = cli.get("/api/adrs/nao-existe")
    assert r.status_code == 404

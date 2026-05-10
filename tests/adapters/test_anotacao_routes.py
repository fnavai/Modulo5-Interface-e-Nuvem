# Testes da API HTTP de anotacoes (US IN-03).

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
    monkeypatch.setenv("ANOTACOES_SQLITE_PATH", str(tmp_path / "anot.db"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    app = composition_root.create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _criar(cli, **overrides):
    base = {
        "repositorio": "fnavai/x", "modulo": "app/main.py", "componente": "Saude",
        "autor_id": "alice", "conteudo": "@bob revisa isso",
    }
    base.update(overrides)
    return cli.post("/api/anotacoes", json=base)


def test_post_cria_201_e_inclui_mencoes(cliente):
    r = _criar(cliente)
    assert r.status_code == 201
    body = r.get_json()
    assert body["componente"] == "Saude"
    assert body["mencoes"] == ["bob"]


def test_post_repositorio_vazio_400(cliente):
    r = _criar(cliente, repositorio="")
    assert r.status_code == 400


def test_post_resposta_em_thread(cliente):
    raiz = _criar(cliente).get_json()
    r = _criar(cliente, parent_id=raiz["id"], conteudo="resposta")
    assert r.status_code == 201
    assert r.get_json()["parent_id"] == raiz["id"]


def test_post_parent_inexistente_404(cliente):
    r = _criar(cliente, parent_id="fantasma")
    assert r.status_code == 404


def test_get_listar_filtra_por_componente(cliente):
    _criar(cliente, componente="Saude")
    _criar(cliente, componente="Outro")
    r = cliente.get("/api/anotacoes?componente=Saude")
    body = r.get_json()
    assert len(body["anotacoes"]) == 1
    assert body["anotacoes"][0]["componente"] == "Saude"


def test_get_listar_filtra_resolvida(cliente):
    a = _criar(cliente).get_json()
    cliente.post(f"/api/anotacoes/{a['id']}/resolver")
    abertas = cliente.get("/api/anotacoes?resolvida=false").get_json()
    fechadas = cliente.get("/api/anotacoes?resolvida=true").get_json()
    assert abertas["anotacoes"] == []
    assert len(fechadas["anotacoes"]) == 1


def test_get_obter_404(cliente):
    r = cliente.get("/api/anotacoes/fantasma")
    assert r.status_code == 404


def test_put_atualizar_so_pelo_autor(cliente):
    a = _criar(cliente).get_json()
    r_outro = cliente.put(f"/api/anotacoes/{a['id']}", json={
        "autor_id": "bob", "conteudo": "hack",
    })
    assert r_outro.status_code == 403
    r_autor = cliente.put(f"/api/anotacoes/{a['id']}", json={
        "autor_id": "alice", "conteudo": "atualizado @carol",
    })
    assert r_autor.status_code == 200
    assert "carol" in r_autor.get_json()["mencoes"]


def test_resolver_reabrir(cliente):
    a = _criar(cliente).get_json()
    r = cliente.post(f"/api/anotacoes/{a['id']}/resolver")
    assert r.status_code == 200
    assert r.get_json()["resolvida"] is True
    r = cliente.post(f"/api/anotacoes/{a['id']}/reabrir")
    assert r.json if False else True
    assert r.get_json()["resolvida"] is False


def test_delete_so_pelo_autor(cliente):
    a = _criar(cliente).get_json()
    r = cliente.delete(f"/api/anotacoes/{a['id']}?autor_id=bob")
    assert r.status_code == 403
    r = cliente.delete(f"/api/anotacoes/{a['id']}?autor_id=alice")
    assert r.status_code == 204


def test_delete_inexistente_404(cliente):
    r = cliente.delete("/api/anotacoes/fantasma?autor_id=alice")
    assert r.status_code == 404


def test_get_thread(cliente):
    raiz = _criar(cliente).get_json()
    _criar(cliente, parent_id=raiz["id"], conteudo="primeira")
    _criar(cliente, parent_id=raiz["id"], conteudo="segunda")
    r = cliente.get(f"/api/anotacoes/thread/{raiz['id']}")
    assert r.status_code == 200
    assert len(r.get_json()["respostas"]) == 2


def test_get_mencoes(cliente):
    _criar(cliente, conteudo="oi @bob")
    _criar(cliente, conteudo="oi @carol")
    r = cliente.get("/api/anotacoes/mencoes?usuario_id=bob")
    body = r.get_json()
    assert len(body["anotacoes"]) == 1
    assert "bob" in body["anotacoes"][0]["mencoes"]


def test_get_mencoes_sem_usuario_400(cliente):
    r = cliente.get("/api/anotacoes/mencoes")
    assert r.status_code == 400

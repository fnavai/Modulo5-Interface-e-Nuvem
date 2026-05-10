# Testes das rotas Flask /api/rascunhos (US IN-02).

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("VALIDADOR_GITHUB", "fake")
    monkeypatch.setenv("PUBLICADOR_PR", "fake")
    monkeypatch.setenv("CACHE_SAUDE_TTL_SEGUNDOS", "0")
    monkeypatch.setenv("ADRS_SQLITE_PATH", str(tmp_path / "adrs.db"))
    monkeypatch.setenv("RASCUNHOS_SQLITE_PATH", str(tmp_path / "rasc.db"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    app = composition_root.create_app()
    app.config["TESTING"] = True
    return app.test_client(), app


def _payload_basico(**overrides):
    base = {
        "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
        "branch_base": "develop",
        "autor_id": "alice",
        "titulo": "Atualizar diagrama",
        "conteudo_mermaid": "classDiagram\n    class A\n",
        "descricao_mudanca": "adicionei A",
    }
    base.update(overrides)
    return base


def test_post_criar_201(cliente):
    cli, _ = cliente
    r = cli.post("/api/rascunhos", json=_payload_basico())
    assert r.status_code == 201
    body = r.get_json()
    assert body["titulo"] == "Atualizar diagrama"
    assert body["repositorio"] == "fnavai/Modulo5-Interface-e-Nuvem"


def test_post_repo_invalido_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/rascunhos", json=_payload_basico(repositorio="semslash"))
    assert r.status_code == 400


def test_get_listar_filtra_por_autor(cliente):
    cli, _ = cliente
    cli.post("/api/rascunhos", json=_payload_basico(autor_id="alice"))
    cli.post("/api/rascunhos", json=_payload_basico(autor_id="bob"))
    r = cli.get("/api/rascunhos?autor_id=alice")
    body = r.get_json()
    assert len(body["rascunhos"]) == 1
    assert body["rascunhos"][0]["autor_id"] == "alice"


def test_get_obter_404(cliente):
    cli, _ = cliente
    r = cli.get("/api/rascunhos/fantasma")
    assert r.status_code == 404


def test_put_atualiza(cliente):
    cli, _ = cliente
    criado = cli.post("/api/rascunhos", json=_payload_basico()).get_json()
    r = cli.put(f"/api/rascunhos/{criado['id']}", json={
        "conteudo_mermaid": "classDiagram\n    class B\n", "descricao_mudanca": "trocou pra B",
    })
    assert r.status_code == 200
    assert "class B" in r.get_json()["conteudo_mermaid"]


def test_put_inexistente_404(cliente):
    cli, _ = cliente
    r = cli.put("/api/rascunhos/fantasma", json={"conteudo_mermaid": "x"})
    assert r.status_code == 404


def test_delete_204_e_404(cliente):
    cli, _ = cliente
    criado = cli.post("/api/rascunhos", json=_payload_basico()).get_json()
    r = cli.delete(f"/api/rascunhos/{criado['id']}")
    assert r.status_code == 204
    r = cli.delete(f"/api/rascunhos/{criado['id']}")
    assert r.status_code == 404


def test_publicar_201_e_chama_publicador(cliente):
    cli, app = cliente
    criado = cli.post("/api/rascunhos", json=_payload_basico()).get_json()
    r = cli.post(f"/api/rascunhos/{criado['id']}/publicar", json={
        "caminho_arquivo": "docs/diagrama.mmd",
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body["pr_numero"] == 100
    assert body["pr_url"].endswith("/pull/100")
    assert body["arquivo_publicado"] == "docs/diagrama.mmd"

    publicador = app.config["publicador_pr"]
    assert len(publicador.chamadas) == 1


def test_publicar_caminho_invalido_400(cliente):
    cli, _ = cliente
    criado = cli.post("/api/rascunhos", json=_payload_basico()).get_json()
    r = cli.post(f"/api/rascunhos/{criado['id']}/publicar", json={
        "caminho_arquivo": "../../escapa.mmd",
    })
    assert r.status_code == 400


def test_publicar_rascunho_inexistente_404(cliente):
    cli, _ = cliente
    r = cli.post("/api/rascunhos/fantasma/publicar", json={"caminho_arquivo": "x.mmd"})
    assert r.status_code == 404


def test_publicar_falha_no_github_502(cliente):
    cli, app = cliente
    criado = cli.post("/api/rascunhos", json=_payload_basico()).get_json()
    from app.domain.excecoes import PublicacaoPRError
    app.config["publicador_pr"].fazer_falhar_com(PublicacaoPRError("rate limit"))
    r = cli.post(f"/api/rascunhos/{criado['id']}/publicar", json={
        "caminho_arquivo": "docs/x.mmd",
    })
    assert r.status_code == 502

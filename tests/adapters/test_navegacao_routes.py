# Testes da rota Flask /api/navegacao/link (US IN-01).

import pytest


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("VALIDADOR_GITHUB", "fake")
    monkeypatch.setenv("CACHE_SAUDE_TTL_SEGUNDOS", "0")  # desliga cache de saude

    import importlib
    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    app = composition_root.create_app()
    app.config["TESTING"] = True
    return app.test_client(), app


def test_post_link_basico_200(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
        "arquivo": "app/main.py",
        "ref": "develop",
        "linha": 10,
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["url"] == "https://github.com/fnavai/Modulo5-Interface-e-Nuvem/blob/develop/app/main.py#L10"
    assert body["abre_em_nova_aba"] is True
    assert body["validacao"]["executada"] is False


def test_post_repo_invalido_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={"repositorio": "semslash", "arquivo": "x.py"})
    assert r.status_code == 400
    assert "owner/repo" in r.get_json()["erro"]


def test_post_path_traversal_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={"repositorio": "o/r", "arquivo": "../../etc/passwd"})
    assert r.status_code == 400


def test_post_linha_negativa_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "o/r", "arquivo": "x.py", "linha": -1,
    })
    assert r.status_code == 400


def test_post_linha_invalida_tipo_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "o/r", "arquivo": "x.py", "linha": "abc",
    })
    assert r.status_code == 400


def test_post_validar_existencia_sucesso(cliente):
    cli, app = cliente
    fake = app.config["validador_github"]
    fake.configurar("o/r", "x.py", "HEAD", existe=True)
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "o/r", "arquivo": "x.py", "validar_existencia": True,
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["validacao"]["existe"] is True


def test_post_validar_arquivo_inexistente_devolve_msg_amigavel(cliente):
    cli, app = cliente
    fake = app.config["validador_github"]
    fake.configurar("o/r", "x.py", "HEAD", existe=False)
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "o/r", "arquivo": "x.py", "validar_existencia": True,
    })
    assert r.status_code == 200  # link sempre sai
    body = r.get_json()
    assert body["validacao"]["existe"] is False
    assert "nao foi encontrado" in body["validacao"]["mensagem"].lower()


def test_post_range_de_linhas(cliente):
    cli, _ = cliente
    r = cli.post("/api/navegacao/link", json={
        "repositorio": "o/r", "arquivo": "x.py", "linha": 5, "linha_fim": 9,
    })
    assert r.status_code == 200
    assert r.get_json()["url"].endswith("#L5-L9")

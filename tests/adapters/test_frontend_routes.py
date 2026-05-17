# O Flask serve o portal estatico em / e /assets/<path>, sem sombrear
# as rotas de API/saude.

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
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


def test_raiz_serve_o_portal_html(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert b"<html" in r.data.lower()


def test_asset_app_js_servido(cliente):
    r = cliente.get("/assets/app.js")
    assert r.status_code == 200


def test_asset_inexistente_404(cliente):
    assert cliente.get("/assets/nao-existe.xyz").status_code == 404


def test_nao_sombreia_api_nem_saude(cliente):
    assert cliente.get("/health").status_code == 200
    assert cliente.get("/health/ready").status_code in (200, 207, 503)
    # rota de API ainda valida o corpo (nao foi engolida pelo catch-all)
    r = cliente.post("/api/projeto/analisar", json={"repositorio": "x"})
    assert r.status_code == 400

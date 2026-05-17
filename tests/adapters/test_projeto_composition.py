# Verifica que o blueprint do fluxo unificado esta registrado pelo
# composition_root (via create_app), sem tocar a rede: corpo invalido
# retorna 400 ANTES de chamar o service.

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
    return app.test_client(), app


def test_blueprint_projeto_registrado_corpo_invalido_400(cliente):
    cli, _ = cliente
    r = cli.post("/api/projeto/analisar", json={"repositorio": "semslash"})
    assert r.status_code == 400  # rota existe e validou (nao 404)
    assert "erro" in r.get_json()


def test_metodo_get_nao_permitido_405(cliente):
    cli, _ = cliente
    assert cli.get("/api/projeto/analisar").status_code == 405


def test_projeto_service_exposto_no_app_config(cliente):
    _, app = cliente
    from app.application.ports.driving.projeto_service import ProjetoService
    assert isinstance(app.config["projeto_service"], ProjetoService)


def test_rotas_existentes_nao_quebraram(cliente):
    cli, _ = cliente
    assert cli.get("/health").status_code == 200

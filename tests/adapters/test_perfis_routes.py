"""Testes da rota Flask GET /api/projeto/perfis (proxy do Perfis-Usuarios)."""
from flask import Flask

from app.adapters.driving.http.perfis_routes import criar_perfis_routes
from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClientePerfisFake,
)
from app.application.services.projeto_service_impl import ProjetoServiceImpl


def _app(perfis):
    service = ProjetoServiceImpl(ClienteGeradorFake(), perfis)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(criar_perfis_routes(service))
    return app.test_client()


def test_get_perfis_200_devolve_diagrama():
    body_perfis = {
        "papeis": ["tech_lead", "desenvolvedor"],
        "templates_resumo": [],
        "personas_legadas": [],
        "mermaid": "graph TD\n  p0[tech_lead]",
    }
    cli = _app(ClientePerfisFake(diagrama_perfis=body_perfis))
    r = cli.get("/api/projeto/perfis")
    assert r.status_code == 200
    body = r.get_json()
    assert "graph TD" in body["mermaid"]
    assert "tech_lead" in body["papeis"]


def test_get_perfis_502_quando_perfis_indisponivel():
    cli = _app(ClientePerfisFake(diagrama_perfis=None))
    r = cli.get("/api/projeto/perfis")
    assert r.status_code == 502
    assert "indispon" in r.get_json()["erro"].lower()


def test_get_perfis_502_quando_perfis_falha_diagrama():
    cli = _app(ClientePerfisFake(diagrama_perfis={"x": 1}, falha_diagrama=True))
    r = cli.get("/api/projeto/perfis")
    assert r.status_code == 502

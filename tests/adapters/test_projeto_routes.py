# Testes da rota Flask POST /api/projeto/analisar (fluxo unificado do portal).
# Rota testada em isolamento: app minimo + ProjetoServiceImpl com clientes fake.

import pytest
from flask import Flask

from app.adapters.driving.http.projeto_routes import criar_projeto_routes
from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClientePerfisFake,
)
from app.application.services.projeto_service_impl import ProjetoServiceImpl


def _app(gerador, perfis):
    service = ProjetoServiceImpl(gerador, perfis)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(criar_projeto_routes(service))
    return app.test_client()


def test_analisar_200_devolve_visao_unificada():
    cli = _app(
        ClienteGeradorFake(
            diagrama="classDiagram\n  class A", estrutura={"linguagem": "python"}
        ),
        ClientePerfisFake(ownership={"ownership": {"owner_id": "x"}}),
    )
    r = cli.post(
        "/api/projeto/analisar",
        json={
            "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
            "branch": "develop",
            "caminho": "app/main.py",
        },
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["diagrama_mermaid"].startswith("classDiagram")
    assert body["resumo_ia"] == {"linguagem": "python"}
    assert body["ownership"] == {"ownership": {"owner_id": "x"}}
    assert body["partes_faltantes"] == []
    assert body["referencia"]["owner"] == "fnavai"
    assert body["referencia"]["repo"] == "Modulo5-Interface-e-Nuvem"


def test_analisar_com_tipo_sequencia_repassa_ao_gerador():
    gerador = ClienteGeradorFake(diagrama="sequenceDiagram\n  participant A", estrutura={"linguagem": "python"})
    cli = _app(gerador, ClientePerfisFake())
    r = cli.post(
        "/api/projeto/analisar",
        json={"repositorio": "o/r", "caminho": "a.py", "tipo": "sequencia"},
    )
    assert r.status_code == 200
    assert gerador.ultimo_tipo == "sequencia"


def test_analisar_sem_tipo_default_classe():
    gerador = ClienteGeradorFake(diagrama="classDiagram\n  class A")
    cli = _app(gerador, ClientePerfisFake())
    cli.post("/api/projeto/analisar", json={"repositorio": "o/r", "caminho": "a.py"})
    assert gerador.ultimo_tipo == "classe"


def test_analisar_tipo_invalido_400():
    cli = _app(ClienteGeradorFake(diagrama="x"), ClientePerfisFake())
    r = cli.post(
        "/api/projeto/analisar",
        json={"repositorio": "o/r", "caminho": "a.py", "tipo": "xyz"},
    )
    assert r.status_code == 400
    assert "tipo" in r.get_json()["erro"].lower()


def test_repositorio_sem_slash_400():
    cli = _app(ClienteGeradorFake(diagrama="x"), ClientePerfisFake())
    r = cli.post(
        "/api/projeto/analisar", json={"repositorio": "semslash", "caminho": "a.py"}
    )
    assert r.status_code == 400
    assert "owner/repo" in r.get_json()["erro"]


def test_caminho_obrigatorio_400():
    cli = _app(ClienteGeradorFake(diagrama="x"), ClientePerfisFake())
    r = cli.post("/api/projeto/analisar", json={"repositorio": "o/r"})
    assert r.status_code == 400


def test_path_traversal_no_caminho_400():
    cli = _app(ClienteGeradorFake(diagrama="x"), ClientePerfisFake())
    r = cli.post(
        "/api/projeto/analisar",
        json={"repositorio": "o/r", "caminho": "../../etc/passwd"},
    )
    assert r.status_code == 400


def test_branch_default_develop_quando_ausente():
    cli = _app(
        ClienteGeradorFake(diagrama="classDiagram\n A", estrutura={}),
        ClientePerfisFake(ownership={}),
    )
    r = cli.post(
        "/api/projeto/analisar", json={"repositorio": "o/r", "caminho": "a.py"}
    )
    assert r.status_code == 200
    assert r.get_json()["referencia"]["branch"] == "develop"


def test_gerador_indisponivel_502():
    cli = _app(ClienteGeradorFake(falha=True), ClientePerfisFake())
    r = cli.post(
        "/api/projeto/analisar",
        json={"repositorio": "o/r", "branch": "develop", "caminho": "a.py"},
    )
    assert r.status_code == 502
    assert "erro" in r.get_json()

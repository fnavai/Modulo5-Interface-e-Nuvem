# Rotas de download: POST /api/projeto/documento/{pptx,relatorio}.
# Rota isolada: app minimo + ProjetoServiceImpl com fakes.

from flask import Flask

from app.adapters.driving.http.projeto_routes import criar_projeto_routes
from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClienteIAFake,
    ClientePerfisFake,
    FonteCodigoFake,
)
from app.application.services.projeto_service_impl import ProjetoServiceImpl


def _cli(gerador=None):
    service = ProjetoServiceImpl(
        gerador or ClienteGeradorFake(diagrama="classDiagram\n A",
                                      estrutura={"linguagem": "python"}),
        ClientePerfisFake(ownership={"ownership": {"owner_id": "x"}}),
        cliente_ia=ClienteIAFake(qualidade={"acoplamento": []}),
        fonte_codigo=FonteCodigoFake(codigo="class A: pass"),
    )
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(criar_projeto_routes(service))
    return app.test_client()


_BODY = {"repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
         "branch": "develop", "caminho": "app/main.py"}


def test_pptx_200_download():
    r = _cli().post("/api/projeto/documento/pptx", json=_BODY)
    assert r.status_code == 200
    assert r.data.startswith(b"PK")
    assert "attachment" in r.headers["Content-Disposition"]
    assert ".pptx" in r.headers["Content-Disposition"]


def test_relatorio_200_pdf_download():
    r = _cli().post("/api/projeto/documento/relatorio",
                     json={**_BODY, "formato": "pdf"})
    assert r.status_code == 200
    assert r.data.startswith(b"%PDF")
    assert "attachment" in r.headers["Content-Disposition"]


def test_relatorio_formato_invalido_400():
    r = _cli().post("/api/projeto/documento/relatorio",
                     json={**_BODY, "formato": "xlsx"})
    assert r.status_code == 400
    assert "formato" in r.get_json()["erro"]


def test_documento_repositorio_invalido_400():
    r = _cli().post("/api/projeto/documento/pptx",
                     json={"repositorio": "semslash", "caminho": "a.py"})
    assert r.status_code == 400
    assert "owner/repo" in r.get_json()["erro"]


def test_documento_gerador_down_502():
    cli = _cli(ClienteGeradorFake(diagrama="x", estrutura={},
                                  falha_doc=True))
    r = cli.post("/api/projeto/documento/pptx", json=_BODY)
    assert r.status_code == 502
    assert "erro" in r.get_json()


def test_analisar_continua_funcionando():
    # baseline nao regrediu: a rota antiga segue 200 com qualidade no corpo
    r = _cli().post("/api/projeto/analisar", json=_BODY)
    assert r.status_code == 200
    body = r.get_json()
    assert body["diagrama_mermaid"].startswith("classDiagram")
    assert body["qualidade"] == {"acoplamento": []}
    assert body["partes_faltantes"] == []

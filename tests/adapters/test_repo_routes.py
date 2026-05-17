# Rotas GET /api/repo/branches e /api/repo/arquivos (seletores do portal).

from flask import Flask

from app.adapters.driving.http.repo_routes import criar_repo_routes
from app.adapters.driven.clients.clientes_fake import (
    ExploradorRepositorioFake,
)
from app.application.services.repo_service_impl import RepoServiceImpl


def _cli(explorador):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(criar_repo_routes(RepoServiceImpl(explorador)))
    return app.test_client()


def test_branches_200():
    cli = _cli(ExploradorRepositorioFake(branches=["develop", "main"]))
    r = cli.get("/api/repo/branches?repositorio=fnavai/Modulo5-Interface-e-Nuvem")
    assert r.status_code == 200
    assert r.get_json()["branches"] == ["develop", "main"]


def test_arquivos_200_so_codigo_e_branch_default():
    cli = _cli(ExploradorRepositorioFake(
        arquivos=["app/a.py", "README.md", "x/b.js"]))
    r = cli.get("/api/repo/arquivos?repositorio=o/r")
    assert r.status_code == 200
    body = r.get_json()
    assert body["arquivos"] == ["app/a.py", "x/b.js"]
    assert body["branch"] == "develop"


def test_repositorio_invalido_400():
    cli = _cli(ExploradorRepositorioFake())
    r = cli.get("/api/repo/branches?repositorio=semslash")
    assert r.status_code == 400
    assert "owner/repo" in r.get_json()["erro"]


def test_github_down_502():
    cli = _cli(ExploradorRepositorioFake(falha=True))
    r = cli.get("/api/repo/arquivos?repositorio=o/r&branch=develop")
    assert r.status_code == 502
    assert "erro" in r.get_json()

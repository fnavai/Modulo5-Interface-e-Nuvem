# RepoService: filtro puro de codigo + delegacao ao explorador.

import pytest

from app.adapters.driven.clients.clientes_fake import (
    ExploradorRepositorioFake,
)
from app.application.services.repo_service_impl import (
    RepoServiceImpl,
    filtrar_codigo,
)
from app.domain.excecoes import FalhaNaComunicacaoError


def test_filtrar_codigo_so_extensoes_e_py_primeiro():
    entrada = [
        "README.md", "app/x.py", "static/logo.png", "src/a.js",
        "b.PY", "doc.txt", "Main.java", "n.ipynb",
    ]
    out = filtrar_codigo(entrada)
    assert "README.md" not in out and "static/logo.png" not in out
    assert "doc.txt" not in out and "n.ipynb" not in out
    assert set(out) == {"app/x.py", "b.PY", "src/a.js", "Main.java"}
    # arquivos .py vem antes dos demais
    assert out[0].lower().endswith(".py") and out[1].lower().endswith(".py")


def test_filtrar_codigo_vazio_e_none():
    assert filtrar_codigo([]) == []
    assert filtrar_codigo(None) == []


def test_service_lista_branches_e_arquivos_codigo():
    svc = RepoServiceImpl(ExploradorRepositorioFake(
        branches=["develop", "main"],
        arquivos=["app/a.py", "README.md", "f/b.ts"],
    ))
    assert svc.listar_branches("o", "r") == ["develop", "main"]
    assert svc.listar_arquivos_codigo("o", "r", "develop") == [
        "app/a.py", "f/b.ts"]


def test_service_propaga_falha_do_github():
    svc = RepoServiceImpl(ExploradorRepositorioFake(falha=True))
    with pytest.raises(FalhaNaComunicacaoError):
        svc.listar_branches("o", "r")
    with pytest.raises(FalhaNaComunicacaoError):
        svc.listar_arquivos_codigo("o", "r", "develop")

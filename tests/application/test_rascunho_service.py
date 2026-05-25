# Testes do RascunhoServiceImpl (US IN-02).

import pytest

from app.adapters.driven.clients.publicador_pr_github import PublicadorPRFake
from app.adapters.driven.persistence.repositorio_rascunhos_sqlite import (
    RepositorioRascunhosSQLite,
)
from app.application.services.edicao_service_impl import RascunhoServiceImpl
from app.domain.excecoes import (
    PublicacaoPRError,
    RascunhoInvalidoError,
    RascunhoNaoEncontradoError,
)


@pytest.fixture
def cenario(tmp_path):
    repo = RepositorioRascunhosSQLite(str(tmp_path / "rasc.db"))
    publicador = PublicadorPRFake()
    service = RascunhoServiceImpl(repo, publicador)
    yield service, repo, publicador
    repo.fechar()


def _criar_rascunho(service, **overrides):
    base = {
        "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
        "branch_base": "develop",
        "autor_id": "alice",
        "titulo": "Atualizar diagrama de saude",
        "conteudo_mermaid": "classDiagram\n    class Saude\n",
        "descricao_mudanca": "adicionei classe Saude",
    }
    base.update(overrides)
    return service.criar(**base)


# ------------ CRUD basico ------------

def test_criar_persiste(cenario):
    service, repo, _ = cenario
    r = _criar_rascunho(service)
    assert repo.obter(r.id) is not None


def test_criar_repo_invalido_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoInvalidoError):
        _criar_rascunho(service, repositorio="semslash")


def test_criar_branch_invalida_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoInvalidoError):
        _criar_rascunho(service, branch_base="bad branch")


def test_criar_titulo_vazio_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoInvalidoError):
        _criar_rascunho(service, titulo="")


def test_criar_conteudo_vazio_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoInvalidoError):
        _criar_rascunho(service, conteudo_mermaid="")


def test_atualizar_conteudo(cenario):
    service, _, _ = cenario
    r = _criar_rascunho(service)
    novo = service.atualizar(r.id, conteudo_mermaid="classDiagram\n    class A\n")
    assert "class A" in novo.conteudo_mermaid
    assert novo.atualizado_em > r.atualizado_em


def test_atualizar_titulo_e_descricao(cenario):
    service, _, _ = cenario
    r = _criar_rascunho(service)
    novo = service.atualizar(r.id, titulo="Outro titulo", descricao_mudanca="nova nota")
    assert novo.titulo == "Outro titulo"
    assert novo.descricao_mudanca == "nova nota"


def test_atualizar_conteudo_vazio_falha(cenario):
    service, _, _ = cenario
    r = _criar_rascunho(service)
    with pytest.raises(RascunhoInvalidoError):
        service.atualizar(r.id, conteudo_mermaid="")


def test_atualizar_inexistente_404(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoNaoEncontradoError):
        service.atualizar("fantasma", conteudo_mermaid="x")


def test_obter_e_listar(cenario):
    service, _, _ = cenario
    r1 = _criar_rascunho(service, titulo="A")
    r2 = _criar_rascunho(service, titulo="B", autor_id="bob")
    todos = service.listar()
    assert {r.id for r in todos} == {r1.id, r2.id}
    so_alice = service.listar(autor_id="alice")
    assert {r.id for r in so_alice} == {r1.id}


def test_remover(cenario):
    service, _, _ = cenario
    r = _criar_rascunho(service)
    assert service.remover(r.id) is True
    assert service.remover(r.id) is False


# ------------ Publicar como PR ------------

def test_publicar_chama_publicador_e_devolve_resultado(cenario):
    service, _, publicador = cenario
    r = _criar_rascunho(service)
    resultado = service.publicar_como_pr(
        rascunho_id=r.id, caminho_arquivo="docs/saude.mmd",
    )
    assert resultado.pr_numero == 100
    assert resultado.pr_url.endswith("/pull/100")
    assert resultado.arquivo_publicado == "docs/saude.mmd"
    assert resultado.branch_criada.startswith("diagram-edit/atualizar-diagrama-de-saude-")
    assert len(publicador.chamadas) == 1
    chamada = publicador.chamadas[0]
    assert chamada["repositorio"] == r.repositorio
    assert chamada["branch_base"] == "develop"
    assert chamada["caminho_arquivo"] == "docs/saude.mmd"
    assert chamada["conteudo"] == r.conteudo_mermaid


def test_publicar_usa_titulo_e_descricao_default(cenario):
    service, _, publicador = cenario
    r = _criar_rascunho(service)
    service.publicar_como_pr(r.id, caminho_arquivo="docs/x.mmd")
    chamada = publicador.chamadas[0]
    assert "Atualizar diagrama de saude" in chamada["titulo_pr"]
    assert "docs/x.mmd" in chamada["descricao_pr"]
    assert "alice" in chamada["descricao_pr"]
    assert "adicionei classe Saude" in chamada["descricao_pr"]


def test_publicar_caminho_invalido_400(cenario):
    service, _, _ = cenario
    r = _criar_rascunho(service)
    with pytest.raises(RascunhoInvalidoError):
        service.publicar_como_pr(r.id, caminho_arquivo="../../escapa.mmd")
    with pytest.raises(RascunhoInvalidoError):
        service.publicar_como_pr(r.id, caminho_arquivo="")


def test_publicar_rascunho_inexistente_404(cenario):
    service, _, _ = cenario
    with pytest.raises(RascunhoNaoEncontradoError):
        service.publicar_como_pr("fantasma", caminho_arquivo="x.mmd")


def test_publicar_propaga_erro_do_publicador(cenario):
    service, _, publicador = cenario
    publicador.fazer_falhar_com(PublicacaoPRError("branch ja existe"))
    r = _criar_rascunho(service)
    with pytest.raises(PublicacaoPRError):
        service.publicar_como_pr(r.id, caminho_arquivo="docs/x.mmd")


def test_branch_gerada_eh_unica_por_rascunho(cenario):
    service, _, _ = cenario
    r1 = _criar_rascunho(service, titulo="X")
    r2 = _criar_rascunho(service, titulo="X")  # mesmo titulo
    res1 = service.publicar_como_pr(r1.id, caminho_arquivo="x.mmd")
    res2 = service.publicar_como_pr(r2.id, caminho_arquivo="x.mmd")
    assert res1.branch_criada != res2.branch_criada

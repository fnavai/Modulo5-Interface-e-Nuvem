# Testes do AnotacaoServiceImpl + parser de @mencoes (US IN-03).

import pytest

from app.adapters.driven.persistence.repositorio_anotacoes_sqlite import (
    RepositorioAnotacoesSQLite,
)
from app.application.services.anotacao_service_impl import AnotacaoServiceImpl
from app.domain.entidades.anotacao import extrair_mencoes
from app.domain.excecoes import (
    AnotacaoInvalidaError,
    AnotacaoNaoEncontradaError,
    PermissaoAnotacaoNegadaError,
)


@pytest.fixture
def cenario(tmp_path):
    repo = RepositorioAnotacoesSQLite(str(tmp_path / "anot.db"))
    service = AnotacaoServiceImpl(repo)
    yield service, repo
    repo.fechar()


def _criar(service, **overrides):
    base = {
        "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
        "modulo": "app/main.py",
        "componente": "Saude",
        "autor_id": "alice",
        "conteudo": "Esse aqui precisa de revisao @bob",
    }
    base.update(overrides)
    return service.criar(**base)


# ------------ Parser de @mencoes ------------

def test_extrair_mencoes_simples():
    assert extrair_mencoes("oi @alice") == ("alice",)


def test_extrair_mencoes_multiplas_sem_duplicar():
    assert extrair_mencoes("@alice @bob, @alice de novo") == ("alice", "bob")


def test_extrair_mencoes_aceita_hifen_e_underscore():
    assert extrair_mencoes("@joao-silva @maria_souza") == ("joao-silva", "maria_souza")


def test_extrair_mencoes_no_inicio_da_string():
    assert extrair_mencoes("@alice oi") == ("alice",)


def test_extrair_mencoes_email_nao_eh_mencao():
    """alice@example.com nao deve virar mencao porque nao tem espaco antes do @."""
    assert extrair_mencoes("manda email pra alice@example.com") == ()


def test_extrair_mencoes_string_vazia():
    assert extrair_mencoes("") == ()


def test_extrair_mencoes_sem_arroba():
    assert extrair_mencoes("nao tem mencao aqui") == ()


# ------------ CRUD basico ------------

def test_criar_persiste_e_indexa_mencoes(cenario):
    service, repo = cenario
    a = _criar(service, conteudo="oi @bob e @carol")
    assert repo.obter(a.id) is not None
    assert a.mencoes == ("bob", "carol")


def test_criar_repositorio_vazio_400(cenario):
    service, _ = cenario
    with pytest.raises(AnotacaoInvalidaError):
        _criar(service, repositorio="")


def test_criar_conteudo_vazio_400(cenario):
    service, _ = cenario
    with pytest.raises(AnotacaoInvalidaError):
        _criar(service, conteudo="")


def test_criar_resposta_em_thread(cenario):
    service, _ = cenario
    raiz = _criar(service)
    resp = _criar(service, conteudo="concordo @alice", parent_id=raiz.id)
    assert resp.parent_id == raiz.id


def test_criar_resposta_de_resposta_falha(cenario):
    service, _ = cenario
    raiz = _criar(service)
    resp = _criar(service, parent_id=raiz.id)
    with pytest.raises(AnotacaoInvalidaError):
        _criar(service, parent_id=resp.id)


def test_criar_resposta_de_inexistente_404(cenario):
    service, _ = cenario
    with pytest.raises(AnotacaoNaoEncontradaError):
        _criar(service, parent_id="fantasma")


def test_atualizar_so_pelo_autor(cenario):
    service, _ = cenario
    a = _criar(service)
    novo = service.atualizar(a.id, autor_id="alice", conteudo="atualizado @carol")
    assert "atualizado" in novo.conteudo
    assert "carol" in novo.mencoes
    with pytest.raises(PermissaoAnotacaoNegadaError):
        service.atualizar(a.id, autor_id="bob", conteudo="hack")


def test_atualizar_reindexa_mencoes(cenario):
    service, repo = cenario
    a = _criar(service, conteudo="@bob")
    service.atualizar(a.id, autor_id="alice", conteudo="@carol agora")
    encontrados = repo.listar_mencoes_de("bob")
    assert encontrados == []
    encontrados = repo.listar_mencoes_de("carol")
    assert {x.id for x in encontrados} == {a.id}


def test_atualizar_conteudo_vazio_falha(cenario):
    service, _ = cenario
    a = _criar(service)
    with pytest.raises(AnotacaoInvalidaError):
        service.atualizar(a.id, autor_id="alice", conteudo="   ")


def test_resolver_e_reabrir(cenario):
    service, _ = cenario
    a = _criar(service)
    assert a.resolvida is False
    resolvido = service.resolver(a.id)
    assert resolvido.resolvida is True
    reaberto = service.reabrir(a.id)
    assert reaberto.resolvida is False


def test_resolver_idempotente(cenario):
    service, _ = cenario
    a = _criar(service)
    service.resolver(a.id)
    resolvido = service.resolver(a.id)
    assert resolvido.resolvida is True


def test_remover_so_pelo_autor(cenario):
    service, _ = cenario
    a = _criar(service)
    with pytest.raises(PermissaoAnotacaoNegadaError):
        service.remover(a.id, autor_id="bob")
    assert service.remover(a.id, autor_id="alice") is True


def test_remover_inexistente_devolve_false(cenario):
    service, _ = cenario
    assert service.remover("fantasma", autor_id="alice") is False


# ------------ Filtros e thread ------------

def test_listar_filtra_por_componente(cenario):
    service, _ = cenario
    _criar(service, componente="Saude")
    _criar(service, componente="Outro")
    res = service.listar(componente="Saude")
    assert all(a.componente == "Saude" for a in res)
    assert len(res) == 1


def test_listar_filtra_por_resolvida(cenario):
    service, _ = cenario
    a1 = _criar(service)
    a2 = _criar(service)
    service.resolver(a1.id)
    abertas = service.listar(resolvida=False)
    fechadas = service.listar(resolvida=True)
    assert {a.id for a in abertas} == {a2.id}
    assert {a.id for a in fechadas} == {a1.id}


def test_listar_thread(cenario):
    service, _ = cenario
    raiz = _criar(service)
    r1 = _criar(service, parent_id=raiz.id, conteudo="primeira")
    r2 = _criar(service, parent_id=raiz.id, conteudo="segunda")
    respostas = service.listar_thread(raiz.id)
    assert [a.id for a in respostas] == [r1.id, r2.id]  # ordem cronologica


def test_listar_mencoes_de(cenario):
    service, _ = cenario
    a1 = _criar(service, conteudo="oi @bob")
    a2 = _criar(service, conteudo="@bob e @carol")
    _criar(service, conteudo="ninguem mencionado")
    para_bob = service.listar_mencoes_de("bob")
    assert {a.id for a in para_bob} == {a1.id, a2.id}
    para_carol = service.listar_mencoes_de("carol")
    assert {a.id for a in para_carol} == {a2.id}


def test_listar_mencoes_de_usuario_vazio_falha(cenario):
    service, _ = cenario
    with pytest.raises(AnotacaoInvalidaError):
        service.listar_mencoes_de("")

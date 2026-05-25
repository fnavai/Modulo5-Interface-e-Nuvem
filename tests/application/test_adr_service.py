# Testes do ADRServiceImpl (US IN-07) usando repo SQLite em arquivo temporario.

import pytest

from app.adapters.driven.persistence.repositorio_adrs_sqlite import RepositorioADRsSQLite
from app.application.services.adr_service_impl import ADRServiceImpl
from app.domain.entidades.decisao_arquitetural import StatusADR
from app.domain.excecoes import (
    ADRInvalidaError,
    ADRNaoEncontradaError,
    TransicaoStatusInvalidaError,
    VinculoDuplicadoError,
)


@pytest.fixture
def service(tmp_path):
    repo = RepositorioADRsSQLite(str(tmp_path / "adrs.db"))
    yield ADRServiceImpl(repo)
    repo.fechar()


def _criar(service, **kwargs):
    base = {
        "titulo": "Adotar PostgreSQL",
        "contexto": "Precisamos de banco com transacoes ACID.",
        "decisao": "Vamos usar PostgreSQL 16.",
        "consequencias": "Positivas: ACID. Negativas: Mais um servico para operar.",
        "autor_id": "alice",
    }
    base.update(kwargs)
    return service.criar(**base)


def test_template_padrao_tem_4_campos(service):
    t = service.template_padrao()
    assert set(t.keys()) == {"titulo", "contexto", "decisao", "consequencias"}
    assert all(t.values())


def test_criar_em_rascunho(service):
    adr = _criar(service)
    assert adr.status == StatusADR.RASCUNHO
    assert adr.titulo == "Adotar PostgreSQL"


def test_criar_titulo_vazio_400(service):
    with pytest.raises(ADRInvalidaError):
        _criar(service, titulo="")


def test_atualizar_so_em_rascunho(service):
    adr = _criar(service)
    atualizada = service.atualizar(adr.id, "alice", titulo="Adotar PostgreSQL 16")
    assert atualizada.titulo == "Adotar PostgreSQL 16"

    proposta = service.propor(adr.id, "alice")
    with pytest.raises(TransicaoStatusInvalidaError):
        service.atualizar(proposta.id, "alice", titulo="Outro titulo")


def test_propor_e_aceitar(service):
    adr = _criar(service)
    p = service.propor(adr.id, "alice", documento_aprovacao_id="doc-99")
    assert p.status == StatusADR.PROPOSTA
    assert p.documento_aprovacao_id == "doc-99"

    aceita = service.aceitar(p.id, "bob")
    assert aceita.status == StatusADR.ACEITA


def test_descartar_em_rascunho_e_em_proposta(service):
    a = _criar(service)
    descartada = service.descartar(a.id, "alice", motivo="duplicada")
    assert descartada.status == StatusADR.DESCARTADA
    assert descartada.motivo_descarte == "duplicada"

    b = _criar(service)
    service.propor(b.id, "alice")
    desc2 = service.descartar(b.id, "alice", motivo="contexto mudou")
    assert desc2.status == StatusADR.DESCARTADA


def test_descartar_aceita_falha(service):
    adr = _criar(service)
    service.propor(adr.id, "alice")
    service.aceitar(adr.id, "bob")
    with pytest.raises(TransicaoStatusInvalidaError):
        service.descartar(adr.id, "bob", motivo="agora nao quero mais")


def test_descartar_sem_motivo_400(service):
    adr = _criar(service)
    with pytest.raises(ADRInvalidaError):
        service.descartar(adr.id, "alice", motivo="")


def test_deprecar_so_em_aceita(service):
    adr = _criar(service)
    with pytest.raises(TransicaoStatusInvalidaError):
        service.deprecar(adr.id, "alice", motivo="x")
    service.propor(adr.id, "alice")
    service.aceitar(adr.id, "bob")
    deprec = service.deprecar(adr.id, "bob", motivo="substituida pela politica nova")
    assert deprec.status == StatusADR.DEPRECIADA


def test_superar_aponta_para_substituta(service):
    velha = _criar(service)
    service.propor(velha.id, "alice")
    service.aceitar(velha.id, "bob")

    nova = _criar(service, titulo="Migrar para Aurora")
    service.propor(nova.id, "alice")
    service.aceitar(nova.id, "bob")

    superada = service.superar(velha.id, nova.id, "carol")
    assert superada.status == StatusADR.SUPERADA
    assert superada.superada_por_id == nova.id


def test_superar_com_substituta_inexistente_404(service):
    adr = _criar(service)
    service.propor(adr.id, "alice")
    service.aceitar(adr.id, "bob")
    with pytest.raises(ADRNaoEncontradaError):
        service.superar(adr.id, "id-que-nao-existe", "bob")


def test_listar_filtra_por_status(service):
    a = _criar(service)
    b = _criar(service, titulo="Outra")
    service.propor(b.id, "alice")

    rascunhos = service.listar(status=StatusADR.RASCUNHO)
    assert {x.id for x in rascunhos} == {a.id}
    propostas = service.listar(status=StatusADR.PROPOSTA)
    assert {x.id for x in propostas} == {b.id}


def test_vincular_componente_e_consultar(service):
    adr = _criar(service)
    service.vincular_componente(adr.id, "fnavai/Modulo5-Interface-e-Nuvem", "app/main.py", "Bootstrap")
    de_componente = service.adrs_de_componente("fnavai/Modulo5-Interface-e-Nuvem", "app/main.py")
    assert {a.id for a in de_componente} == {adr.id}


def test_vincular_duplicado_409(service):
    adr = _criar(service)
    service.vincular_componente(adr.id, "o/r", "x.py", "X")
    with pytest.raises(VinculoDuplicadoError):
        service.vincular_componente(adr.id, "o/r", "x.py", "X de novo")


def test_desvincular_devolve_true(service):
    adr = _criar(service)
    service.vincular_componente(adr.id, "o/r", "x.py", "X")
    assert service.desvincular_componente(adr.id, "o/r", "x.py") is True
    assert service.desvincular_componente(adr.id, "o/r", "x.py") is False


def test_marcadores_devolve_todos_modulos_solicitados(service):
    adr1 = _criar(service)
    service.propor(adr1.id, "alice")
    service.aceitar(adr1.id, "bob")
    service.vincular_componente(adr1.id, "o/r", "a.py", "A")

    adr2 = _criar(service, titulo="Outra")
    service.vincular_componente(adr2.id, "o/r", "a.py", "A")

    marc = service.marcadores_de_diagrama("o/r", ["a.py", "b.py", "c.py"])
    assert set(marc.keys()) == {"a.py", "b.py", "c.py"}
    assert marc["a.py"]["total"] == 2
    assert marc["a.py"]["tem_adr"] is True
    assert marc["a.py"]["por_status"] == {"aceita": 1, "rascunho": 1}
    assert marc["b.py"]["total"] == 0
    assert marc["b.py"]["tem_adr"] is False


def test_marcadores_sem_modulos_devolve_dict_vazio(service):
    assert service.marcadores_de_diagrama("o/r", []) == {}

import pytest

from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClientePerfisFake,
)
from app.domain.entidades.status_servico import EstadoServico
from app.domain.excecoes import FalhaNaComunicacaoError


def test_gerador_fake_sucesso_devolve_diagrama_e_estrutura():
    fake = ClienteGeradorFake(
        diagrama="classDiagram\n  class A", estrutura={"linguagem": "python"}
    )
    out = fake.gerar_diagrama_branch("o", "r", "develop", "a.py")
    assert out["diagrama_mermaid"] == "classDiagram\n  class A"
    assert out["estrutura"] == {"linguagem": "python"}
    assert out["warnings"] == []
    assert fake.verificar_saude().estado == EstadoServico.DISPONIVEL


def test_gerador_fake_falha_levanta():
    with pytest.raises(FalhaNaComunicacaoError):
        ClienteGeradorFake(falha=True).gerar_diagrama_branch(
            "o", "r", "develop", "a.py"
        )


def test_perfis_fake_sucesso_recebe_modulo():
    fake = ClientePerfisFake(ownership={"ownership": {"owner_id": "x"}})
    assert fake.obter_ownership("o", "r", "a.py") == {"ownership": {"owner_id": "x"}}
    assert fake.verificar_saude().estado == EstadoServico.DISPONIVEL


def test_perfis_fake_falha_levanta():
    with pytest.raises(FalhaNaComunicacaoError):
        ClientePerfisFake(falha=True).obter_ownership("o", "r", "a.py")

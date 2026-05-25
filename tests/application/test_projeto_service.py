import pytest

from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClientePerfisFake,
)
from app.application.services.projeto_service_impl import ProjetoServiceImpl
from app.domain.entidades.projeto_visualizado import ProjetoVisualizado
from app.domain.excecoes import FalhaNaComunicacaoError


def test_orquestra_tudo_ok():
    svc = ProjetoServiceImpl(
        ClienteGeradorFake(
            diagrama="classDiagram\n  class A", estrutura={"linguagem": "python"}
        ),
        ClientePerfisFake(ownership={"ownership": {"owner_id": "x"}}),
    )
    p = svc.analisar("o", "r", "develop", "app/a.py")
    assert isinstance(p, ProjetoVisualizado)
    assert p.tem_diagrama
    assert p.referencia.owner == "o" and p.referencia.caminho == "app/a.py"
    assert p.resumo_ia == {"linguagem": "python"}
    assert p.ownership == {"ownership": {"owner_id": "x"}}
    assert p.partes_faltantes() == []


def test_degrada_quando_perfis_cai():
    svc = ProjetoServiceImpl(
        ClienteGeradorFake(diagrama="classDiagram\n  class A", estrutura={"x": 1}),
        ClientePerfisFake(falha=True),
    )
    p = svc.analisar("o", "r", "develop", "app/a.py")
    assert p.tem_diagrama
    assert p.ownership is None
    assert "ownership" in p.partes_faltantes()
    assert "diagrama" not in p.partes_faltantes()


def test_sem_estrutura_marca_resumo_ia_faltante():
    svc = ProjetoServiceImpl(
        ClienteGeradorFake(diagrama="classDiagram\n  class A", estrutura=None),
        ClientePerfisFake(ownership={"ownership": {}}),
    )
    p = svc.analisar("o", "r", "develop", "app/a.py")
    assert p.resumo_ia is None
    assert "resumo_ia" in p.partes_faltantes()


def test_erro_se_gerador_cai():
    svc = ProjetoServiceImpl(
        ClienteGeradorFake(falha=True), ClientePerfisFake(ownership={})
    )
    with pytest.raises(FalhaNaComunicacaoError):
        svc.analisar("o", "r", "develop", "app/a.py")

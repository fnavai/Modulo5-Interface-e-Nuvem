# ProjetoServiceImpl com IA-qualidade/fonte (best-effort) e os metodos
# de documento. Baseline (construir com 2 args) continua coberto por
# test_projeto_service.py — aqui exercitamos os caminhos novos.

import pytest

from app.adapters.driven.clients.clientes_fake import (
    ClienteGeradorFake,
    ClienteIAFake,
    ClientePerfisFake,
    FonteCodigoFake,
)
from app.application.services.projeto_service_impl import ProjetoServiceImpl
from app.domain.excecoes import FalhaNaComunicacaoError


def _svc(gerador=None, perfis=None, ia=None, fonte=None):
    return ProjetoServiceImpl(
        gerador or ClienteGeradorFake(diagrama="classDiagram\n A",
                                      estrutura={"linguagem": "python"}),
        perfis or ClientePerfisFake(ownership={"ownership": {"owner_id": "x"}}),
        cliente_ia=ia,
        fonte_codigo=fonte,
    )


def test_qualidade_preenchida_quando_ia_e_fonte_ok():
    p = _svc(
        ia=ClienteIAFake(qualidade={"acoplamento": [1], "ciclos": []}),
        fonte=FonteCodigoFake(codigo="class A: pass"),
    ).analisar("o", "r", "develop", "a.py")
    assert p.qualidade == {"acoplamento": [1], "ciclos": []}
    assert p.tem_diagrama and p.partes_faltantes() == []


def test_qualidade_none_quando_sem_ia_ou_fonte():
    # baseline: nenhum dos dois -> qualidade None, fluxo intacto
    p = _svc().analisar("o", "r", "develop", "a.py")
    assert p.qualidade is None
    assert p.tem_diagrama


def test_qualidade_degrada_se_fonte_sem_codigo():
    p = _svc(ia=ClienteIAFake(qualidade={"x": 1}),
             fonte=FonteCodigoFake(codigo=None)).analisar(
        "o", "r", "develop", "a.py")
    assert p.qualidade is None  # sem codigo -> nao chama IA


def test_qualidade_degrada_se_ia_explode():
    p = _svc(ia=ClienteIAFake(falha=True),
             fonte=FonteCodigoFake(codigo="x")).analisar(
        "o", "r", "develop", "a.py")
    assert p.qualidade is None  # excecao da IA nao derruba o fluxo
    assert p.tem_diagrama


def test_documento_pptx_chama_gerador_com_payload_montado():
    ger = ClienteGeradorFake(diagrama="classDiagram\n A",
                             estrutura={"linguagem": "python"})
    out = _svc(gerador=ger).gerar_documento_pptx("o", "r", "develop", "a.py")
    assert out["conteudo"].startswith(b"PK")
    assert out["nome_arquivo"].endswith(".pptx")
    assert ger.ultima_apresentacao["slides"][0]["tipo"] == "capa"


def test_documento_relatorio_repassa_formato_e_resultado():
    ger = ClienteGeradorFake(diagrama="classDiagram\n A", estrutura={})
    out = _svc(gerador=ger).gerar_documento_relatorio(
        "o", "r", "develop", "a.py", "pdf")
    assert out["conteudo"].startswith(b"%PDF")
    assert ger.ultimo_relatorio["formato"] == "pdf"


def test_documento_propaga_falha_do_gerador():
    with pytest.raises(FalhaNaComunicacaoError):
        _svc(gerador=ClienteGeradorFake(diagrama="x", falha_doc=True)
             ).gerar_documento_pptx("o", "r", "develop", "a.py")

# Builders puros ProjetoVisualizado -> payload Gerador.
# Garante: PPTX so usa tipos comprovados (capa/texto/encerramento);
# /reports tem secoes validas; formato cai p/ pdf se invalido;
# entradas degradadas (None) nao quebram.

from app.application.services.documento_builders import (
    montar_apresentacao,
    montar_relatorio,
)
from app.domain.entidades.projeto_visualizado import (
    ProjetoVisualizado,
    ReferenciaRepo,
)

_TIPOS_OK = {"capa", "texto", "encerramento"}


def _proj(qualidade=None, resumo=None, ownership=None, diagrama="classDiagram\n class A"):
    return ProjetoVisualizado(
        referencia=ReferenciaRepo("o", "r", "develop", "app/x.py"),
        diagrama_mermaid=diagrama,
        resumo_ia=resumo,
        ownership=ownership,
        qualidade=qualidade,
    )


def test_apresentacao_so_usa_tipos_comprovados():
    payload = montar_apresentacao(_proj(
        qualidade={"acoplamento": [1, 2]},
        resumo={"linguagem": "python", "componentes": [{"nome": "A"}],
                "relacoes": []},
        ownership={"ownership": {"owner_id": "x", "confianca": 1.0}},
    ))
    tipos = {s["tipo"] for s in payload["slides"]}
    assert tipos.issubset(_TIPOS_OK)
    assert payload["slides"][0]["tipo"] == "capa"
    assert payload["slides"][-1]["tipo"] == "encerramento"
    # slides texto carregam conteudo.texto (shape aceito pelo Gerador)
    for s in payload["slides"]:
        if s["tipo"] == "texto":
            assert isinstance(s["conteudo"]["texto"], str)
    assert "o/r" in payload["titulo"]


def test_apresentacao_degrada_sem_quebrar():
    payload = montar_apresentacao(_proj())  # tudo None menos diagrama
    tipos = {s["tipo"] for s in payload["slides"]}
    assert tipos.issubset(_TIPOS_OK)
    txt = " ".join(s.get("conteudo", {}).get("texto", "")
                   for s in payload["slides"] if s["tipo"] == "texto")
    assert "indisponivel" in txt.lower()


def test_relatorio_schema_e_formato():
    p = montar_relatorio(_proj(resumo={"linguagem": "python",
                                        "componentes": [{"nome": "A"}]}),
                         "pdf")
    assert p["formato"] == "pdf"
    assert p["titulo"] and p["secoes"]
    for sec in p["secoes"]:
        assert sec["titulo"]
        assert isinstance(sec["paragrafos"], list)
        assert isinstance(sec["listas"], list)
    titulos = [s["titulo"] for s in p["secoes"]]
    assert "Referencia" in titulos


def test_relatorio_formato_invalido_cai_para_pdf():
    assert montar_relatorio(_proj(), "xls")["formato"] == "pdf"
    assert montar_relatorio(_proj(), "md")["formato"] == "md"
    assert montar_relatorio(_proj(), "docx")["formato"] == "docx"

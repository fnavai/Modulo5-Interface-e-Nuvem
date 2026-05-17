# Campo qualidade (novo) em ProjetoVisualizado: opcional, NAO entra em
# partes_faltantes (so os 3 originais), aparece no to_dict.

from app.domain.entidades.projeto_visualizado import (
    ProjetoVisualizado,
    ReferenciaRepo,
)


def _ref():
    return ReferenciaRepo(owner="o", repo="r", branch="develop", caminho="a.py")


def test_qualidade_default_none_e_nao_e_parte_faltante():
    p = ProjetoVisualizado(
        referencia=_ref(),
        diagrama_mermaid="classDiagram\n class A",
        resumo_ia={"x": 1},
        ownership={"y": 2},
    )
    assert p.qualidade is None
    assert p.tem_qualidade is False
    # contrato preservado: qualidade NUNCA entra em partes_faltantes
    assert p.partes_faltantes() == []
    assert p.to_dict()["qualidade"] is None


def test_qualidade_preenchida_aparece_no_to_dict():
    p = ProjetoVisualizado(
        referencia=_ref(),
        diagrama_mermaid="classDiagram\n class A",
        resumo_ia=None,
        ownership=None,
        qualidade={"acoplamento": [], "ciclos": []},
    )
    assert p.tem_qualidade is True
    assert p.to_dict()["qualidade"] == {"acoplamento": [], "ciclos": []}
    # so resumo_ia/ownership faltam; qualidade nao polui a lista
    assert set(p.partes_faltantes()) == {"resumo_ia", "ownership"}

from app.domain.entidades.projeto_visualizado import (
    ProjetoVisualizado,
    ReferenciaRepo,
)


def _ref():
    return ReferenciaRepo(owner="o", repo="r", branch="develop", caminho="a.py")


def test_projeto_completo_nao_tem_partes_faltantes():
    p = ProjetoVisualizado(
        referencia=_ref(),
        diagrama_mermaid="classDiagram\n  class A",
        resumo_ia={"classes": 3},
        ownership={"owners": ["x"]},
    )
    assert p.tem_diagrama is True
    assert p.partes_faltantes() == []


def test_projeto_marca_partes_faltantes_quando_none():
    p = ProjetoVisualizado(
        referencia=_ref(),
        diagrama_mermaid="classDiagram\n  class A",
        resumo_ia=None,
        ownership=None,
    )
    faltantes = p.partes_faltantes()
    assert "resumo_ia" in faltantes and "ownership" in faltantes
    assert "diagrama" not in faltantes


def test_sem_diagrama_marca_diagrama_faltante():
    p = ProjetoVisualizado(
        referencia=_ref(), diagrama_mermaid=None, resumo_ia=None, ownership=None
    )
    assert p.tem_diagrama is False
    assert "diagrama" in p.partes_faltantes()


def test_to_dict_serializa_tudo():
    p = ProjetoVisualizado(
        referencia=_ref(),
        diagrama_mermaid="classDiagram\n  class A",
        resumo_ia={"classes": 3},
        ownership={"owners": ["x"]},
    )
    d = p.to_dict()
    assert d["referencia"] == {
        "owner": "o",
        "repo": "r",
        "branch": "develop",
        "caminho": "a.py",
    }
    assert d["diagrama_mermaid"].startswith("classDiagram")
    assert d["resumo_ia"] == {"classes": 3}
    assert d["ownership"] == {"owners": ["x"]}
    assert d["partes_faltantes"] == []

# Builders puros: ProjetoVisualizado -> payload do Gerador.
# Sem I/O — faceis de testar. Usam apenas tipos de slide comprovados
# (capa/texto/encerramento) e o schema /reports (secoes texto/listas).

from app.domain.entidades.projeto_visualizado import ProjetoVisualizado

_LIMITE_LISTA = 30
_LIMITE_TXT = 4000


def _fmt_estrutura(resumo: "dict | None") -> tuple:
    """(linhas de texto, lista de nomes de componentes)."""
    if not isinstance(resumo, dict) or not resumo:
        return (["Resumo estrutural da IA indisponivel."], [])
    comps = resumo.get("componentes") or []
    rels = resumo.get("relacoes") or []
    nomes = []
    for c in comps:
        if isinstance(c, dict):
            nomes.append(str(c.get("nome") or c.get("name") or "?"))
        else:
            nomes.append(str(c))
    linhas = [
        f"Linguagem: {resumo.get('linguagem', 'n/d')}",
        f"Componentes: {len(comps)}",
        f"Relacoes: {len(rels)}",
    ]
    return (linhas, nomes[:_LIMITE_LISTA])


def _fmt_qualidade(qualidade: "dict | None") -> list:
    if not isinstance(qualidade, dict) or not qualidade:
        return ["Diagnostico de qualidade indisponivel (IA ou codigo "
                "nao obtido) — degradacao graciosa."]
    linhas = []
    for chave, valor in qualidade.items():
        if isinstance(valor, (list, tuple)):
            linhas.append(f"{chave}: {len(valor)} item(ns)")
        elif isinstance(valor, dict):
            linhas.append(f"{chave}: {len(valor)} chave(s)")
        else:
            linhas.append(f"{chave}: {str(valor)[:200]}")
    return linhas[:_LIMITE_LISTA] or ["(sem dados de qualidade)"]


def _fmt_ownership(ownership: "dict | None") -> list:
    if not isinstance(ownership, dict) or not ownership:
        return ["Ownership indisponivel (Perfis fora ou sem dado)."]
    o = ownership.get("ownership") if isinstance(
        ownership.get("ownership"), dict) else ownership
    linhas = []
    if o.get("owner_id") is not None:
        linhas.append(f"Owner: {o.get('owner_id')}")
    if o.get("confianca") is not None:
        try:
            linhas.append(f"Confianca: {float(o['confianca']) * 100:.1f}%")
        except (TypeError, ValueError):
            pass
    if o.get("total_commits") is not None:
        linhas.append(f"Commits: {o.get('total_commits')}")
    if ownership.get("origem"):
        linhas.append(f"Origem: {ownership.get('origem')}")
    return linhas or ["Sem ownership registrado para este modulo."]


def _slide_texto(titulo: str, linhas: list) -> dict:
    return {
        "tipo": "texto",
        "titulo": titulo,
        "conteudo": {"texto": "\n".join(linhas)[:_LIMITE_TXT]},
    }


def montar_apresentacao(projeto: ProjetoVisualizado) -> dict:
    """Payload para POST /apresentacao/gerar (so tipos comprovados)."""
    ref = projeto.referencia
    estrut_linhas, nomes = _fmt_estrutura(projeto.resumo_ia)
    if nomes:
        estrut_linhas.append("Componentes: " + ", ".join(nomes))
    mermaid = projeto.diagrama_mermaid or "(diagrama indisponivel)"
    return {
        "titulo": f"Analise: {ref.owner}/{ref.repo}",
        "subtitulo": f"{ref.caminho} @ {ref.branch}",
        "autor": "Portal Modulo 5",
        "slides": [
            {"tipo": "capa",
             "titulo": f"Analise de {ref.owner}/{ref.repo}",
             "subtitulo": f"{ref.caminho} @ {ref.branch}"},
            _slide_texto("Estrutura (IA)", estrut_linhas),
            _slide_texto("Qualidade (IA)", _fmt_qualidade(projeto.qualidade)),
            _slide_texto("Ownership (Perfis)",
                         _fmt_ownership(projeto.ownership)),
            _slide_texto("Diagrama de classes (Mermaid)",
                         [mermaid]),
            {"tipo": "encerramento",
             "titulo": "Gerado pelo Portal Modulo 5",
             "subtitulo": "Gerador -> GitHub -> IA - Perfis"},
        ],
    }


def montar_relatorio(
    projeto: ProjetoVisualizado, formato: str = "pdf"
) -> dict:
    """Payload para POST /reports (secoes texto + listas)."""
    ref = projeto.referencia
    estrut_linhas, nomes = _fmt_estrutura(projeto.resumo_ia)
    secoes = [
        {"titulo": "Referencia",
         "paragrafos": [
             f"Repositorio: {ref.owner}/{ref.repo}",
             f"Branch: {ref.branch}",
             f"Arquivo: {ref.caminho}",
         ],
         "listas": []},
        {"titulo": "Estrutura (IA)",
         "paragrafos": estrut_linhas,
         "listas": [nomes] if nomes else []},
        {"titulo": "Qualidade (IA)",
         "paragrafos": _fmt_qualidade(projeto.qualidade),
         "listas": []},
        {"titulo": "Ownership (Perfis)",
         "paragrafos": _fmt_ownership(projeto.ownership),
         "listas": []},
        {"titulo": "Diagrama de classes (Mermaid)",
         "paragrafos": [projeto.diagrama_mermaid
                        or "(diagrama indisponivel)"],
         "listas": []},
    ]
    fmt = (formato or "pdf").lower().strip()
    if fmt not in ("md", "markdown", "docx", "pdf"):
        fmt = "pdf"
    return {
        "titulo": f"Relatorio do Projeto - {ref.owner}/{ref.repo}",
        "formato": fmt,
        "subtitulo": f"{ref.caminho} @ {ref.branch}",
        "autor": "Portal Modulo 5",
        "metadados": {"gerado_por": "Portal Modulo 5",
                      "pipeline": "Gerador->GitHub->IA - Perfis"},
        "secoes": secoes,
    }

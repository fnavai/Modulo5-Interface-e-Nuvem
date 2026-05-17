# Implementacao do ProjetoService: orquestra Gerador (obrigatorio) e
# Perfis (best-effort) no fluxo unificado do portal.

from app.application.ports.driving.projeto_service import ProjetoService
from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.domain.entidades.projeto_visualizado import (
    ProjetoVisualizado,
    ReferenciaRepo,
)


class ProjetoServiceImpl(ProjetoService):

    def __init__(self, cliente_gerador: ClienteGerador, cliente_perfis: ClientePerfis):
        self._gerador = cliente_gerador
        self._perfis = cliente_perfis

    def analisar(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> ProjetoVisualizado:
        referencia = ReferenciaRepo(
            owner=owner, repo=repo, branch=branch, caminho=caminho
        )

        # Parte obrigatoria: Gerador (pipeline Gerador->GitHub->IA).
        # Se falhar, a excecao de dominio sobe (a tela nao tem o que mostrar).
        diagrama = self._gerador.gerar_diagrama_branch(
            owner, repo, branch, caminho
        )
        diagrama_mermaid = diagrama.get("diagrama_mermaid")
        resumo_ia = diagrama.get("estrutura")

        # Parte best-effort: ownership do Perfis. Qualquer falha vira None
        # (degradacao graciosa) — nunca derruba o fluxo unificado.
        try:
            ownership = self._perfis.obter_ownership(owner, repo, caminho)
        except Exception:
            ownership = None

        return ProjetoVisualizado(
            referencia=referencia,
            diagrama_mermaid=diagrama_mermaid,
            resumo_ia=resumo_ia,
            ownership=ownership,
        )

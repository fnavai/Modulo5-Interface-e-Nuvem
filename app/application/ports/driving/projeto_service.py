# Porta driving: ProjetoService
# Responsabilidade: contrato do fluxo unificado do portal — dado um
# repo/branch/arquivo, agrega diagrama+estrutura (Gerador, que orquestra
# GitHub->IA) e ownership (Perfis) numa visao unica do projeto.

from abc import ABC, abstractmethod

from app.domain.entidades.projeto_visualizado import ProjetoVisualizado


class ProjetoService(ABC):

    @abstractmethod
    def analisar(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> ProjetoVisualizado:
        """
        Executa o fluxo unificado. O diagrama (via Gerador) e obrigatorio:
        se o Gerador falhar, levanta excecao de dominio. Ownership (Perfis)
        e best-effort: se cair, retorna None nessa parte (degradacao
        graciosa — uma falha parcial nao derruba a visao).
        """
        pass

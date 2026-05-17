# Porta driven: ClienteGerador
# Responsabilidade: contrato de comunicação com o serviço Gerador-Documentacao.

from abc import ABC, abstractmethod
from app.domain.entidades.status_servico import StatusServico


class ClienteGerador(ABC):

    @abstractmethod
    def verificar_saude(self) -> StatusServico:
        """
        Consulta o health check do Gerador-Documentacao.
        Nunca levanta excecao — retorna StatusServico com estado adequado.
        """
        pass

    @abstractmethod
    def gerar_diagrama_branch(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        """
        Pede ao Gerador (POST /diagrama/branch, formato=mermaid) o diagrama
        de um arquivo numa branch — pipeline Gerador->GitHub->IA. Retorna um
        dict normalizado: {"diagrama_mermaid": str, "estrutura": dict|None,
        "warnings": list}. "estrutura" e a analise estrutural que a IA
        produziu (componentes/relacoes/linguagem), surfaceada via Gerador.
        Levanta excecao de dominio se o Gerador falhar (parte obrigatoria
        do fluxo unificado).
        """
        pass
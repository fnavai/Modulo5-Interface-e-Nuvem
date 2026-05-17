# Porta driven: ClienteIAAnalise
# Responsabilidade: contrato de comunicacao com o servico IA-Analise-Codigo.

from abc import ABC, abstractmethod
from app.domain.entidades.status_servico import StatusServico


class ClienteIAAnalise(ABC):

    @abstractmethod
    def verificar_saude(self) -> StatusServico:
        """
        Consulta o health check do IA-Analise-Codigo.
        Nunca levanta excecao — retorna StatusServico com estado adequado.
        """
        pass

    # Obs: a IA nao expoe endpoint por owner/repo/branch/file (so
    # POST /estrutura/diagrama com {"codigo": ...}). O resumo estrutural
    # do fluxo unificado vem do campo "estrutura" que o Gerador ja devolve
    # em POST /diagrama/branch (formato=mermaid). Por isso este port
    # permanece apenas com verificar_saude.
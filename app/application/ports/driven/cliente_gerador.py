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
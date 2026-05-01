# Porta driven: ClientePerfis
# Responsabilidade: contrato de comunicacao com o servico Perfis-Usuarios.

from abc import ABC, abstractmethod
from app.domain.entidades.status_servico import StatusServico


class ClientePerfis(ABC):

    @abstractmethod
    def verificar_saude(self) -> StatusServico:
        """
        Consulta o health check do Perfis-Usuarios.
        Nunca levanta excecao — retorna StatusServico com estado adequado.
        """
        pass
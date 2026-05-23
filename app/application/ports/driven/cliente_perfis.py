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

    @abstractmethod
    def obter_ownership(
        self, owner: str, repo: str, modulo: str
    ) -> "dict | None":
        """
        Consulta ownership/aprovacao no Perfis-Usuarios para
        repositorio="owner/repo" e modulo=<caminho do arquivo/dir>
        (o endpoint /api/ownership do Perfis exige o modulo).
        Best-effort: retorna None se o Perfis estiver indisponivel ou
        nao encontrar (nunca derruba o fluxo unificado).
        """
        pass

    # Metodo NAO-abstrato de proposito: nao quebrar fakes existentes
    # (padrao ja usado em ClienteIA/ClienteGerador para metodos opcionais).
    def obter_diagrama_perfis(self) -> "dict | None":
        """
        GET /api/perfis/diagrama no Perfis-Usuarios — devolve o diagrama
        global (papeis + templates + personas legadas) em Mermaid.
        Best-effort: None em qualquer falha.
        """
        return None
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

    # Metodo NAO-abstrato de proposito: manter __abstractmethods__ ==
    # {"verificar_saude"} (contrato testado) e nao quebrar fakes/adapters
    # existentes. So o adapter HTTP real sobrescreve; o default e o
    # comportamento best-effort (sem qualidade).
    def analisar_qualidade(self, codigo: str) -> "dict | None":
        """
        Pede a IA o diagnostico de qualidade do codigo
        (POST /qualidade/analisar com {"codigo": ...}): acoplamento,
        ciclos e severidade. Best-effort: retorna None se a IA falhar
        ou o codigo nao puder ser obtido (nunca derruba o fluxo).
        """
        return None

    # Obs: a IA nao expoe endpoint por owner/repo/branch/file (so
    # POST /estrutura/diagrama e /qualidade/analisar com {"codigo": ...}).
    # O resumo estrutural do fluxo unificado vem do campo "estrutura" que
    # o Gerador ja devolve em POST /diagrama/branch (formato=mermaid); a
    # qualidade exige o codigo cru, obtido via FonteCodigo (GitHub raw).
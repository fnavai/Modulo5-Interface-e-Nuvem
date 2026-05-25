# Porta driven: CacheSaude
# Responsabilidade: contrato de cache do ultimo estado conhecido de cada servico,
# usado para servir respostas degradadas (stale) quando o downstream cai.

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entidades.status_servico import StatusServico


class CacheSaude(ABC):

    @abstractmethod
    def salvar(self, status: StatusServico) -> None:
        """Registra o ultimo estado conhecido de um servico."""
        pass

    @abstractmethod
    def obter(self, nome_servico: str) -> Optional[StatusServico]:
        """
        Retorna o ultimo estado conhecido se ainda valido (dentro do TTL).
        Retorna None se nao houver entrada ou se ela expirou.
        O StatusServico devolvido vem com origem='cache' e stale_segundos preenchido.
        """
        pass

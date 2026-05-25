# Porta driving: SaudeService
# Responsabilidade: contrato do health check agregado do módulo 5.

from abc import ABC, abstractmethod
from typing import Dict


class SaudeService(ABC):

    @abstractmethod
    def verificar_liveness(self) -> Dict:
        """
        Verifica se o portal esta no ar. Sempre retorna algo, nunca levanta excecao.
        """
        pass

    @abstractmethod
    def verificar_readiness(self) -> Dict:
        """
        Consulta o status de cada servico dependente. Retorna estado agregado com detalhes por serviço.
        Nunca levanta exceção — falha de servico é informada no payload.
        """
        pass
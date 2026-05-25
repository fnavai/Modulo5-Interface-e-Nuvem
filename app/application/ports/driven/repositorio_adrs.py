# Porta driven: RepositorioADRs (US IN-07)
# Cobre tanto ADRs quanto vinculos ADR-componente — duas tabelas relacionadas,
# faz sentido manter o port unico para garantir consistencia transacional no adapter.

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.decisao_arquitetural import (
    ADR,
    StatusADR,
    VinculoComponenteADR,
)


class RepositorioADRs(ABC):

    # --- ADRs ---
    @abstractmethod
    def salvar(self, adr: ADR) -> None:
        """Insere ou atualiza por id."""
        pass

    @abstractmethod
    def obter(self, adr_id: str) -> Optional[ADR]:
        pass

    @abstractmethod
    def listar(
        self,
        status: Optional[StatusADR] = None,
        autor_id: Optional[str] = None,
    ) -> List[ADR]:
        pass

    # --- Vinculos ---
    @abstractmethod
    def vincular(self, vinculo: VinculoComponenteADR) -> None:
        """Insere o vinculo. Levanta VinculoDuplicadoError se ja existir."""
        pass

    @abstractmethod
    def desvincular(self, adr_id: str, repositorio: str, modulo: str) -> bool:
        """Retorna True se removeu, False se nao existia."""
        pass

    @abstractmethod
    def listar_vinculos_de_adr(self, adr_id: str) -> List[VinculoComponenteADR]:
        pass

    @abstractmethod
    def listar_adrs_de_componente(
        self, repositorio: str, modulo: str,
    ) -> List[ADR]:
        pass

    @abstractmethod
    def contar_adrs_por_modulo(
        self,
        repositorio: str,
        modulos: List[str],
    ) -> dict:
        """
        Retorna dict {modulo: {status_value: count}} para todos os modulos pedidos.
        Util para o front desenhar marcadores no diagrama.
        """
        pass

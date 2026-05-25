# Porta driven: RepositorioRascunhos (US IN-02)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.rascunho_edicao import RascunhoDiagrama


class RepositorioRascunhos(ABC):

    @abstractmethod
    def salvar(self, rascunho: RascunhoDiagrama) -> None:
        """Insere ou atualiza por id."""
        pass

    @abstractmethod
    def obter(self, rascunho_id: str) -> Optional[RascunhoDiagrama]:
        pass

    @abstractmethod
    def listar(
        self,
        autor_id: Optional[str] = None,
        repositorio: Optional[str] = None,
    ) -> List[RascunhoDiagrama]:
        pass

    @abstractmethod
    def remover(self, rascunho_id: str) -> bool:
        pass

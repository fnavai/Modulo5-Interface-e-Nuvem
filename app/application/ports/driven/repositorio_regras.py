# Porta driven: RepositorioRegras (US IN-09)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.regra_arquitetural import RegraArquitetural


class RepositorioRegras(ABC):

    @abstractmethod
    def salvar(self, regra: RegraArquitetural) -> None:
        """Insere ou atualiza por id."""
        pass

    @abstractmethod
    def obter(self, regra_id: str) -> Optional[RegraArquitetural]:
        pass

    @abstractmethod
    def listar(self, ativa: Optional[bool] = None) -> List[RegraArquitetural]:
        pass

    @abstractmethod
    def remover(self, regra_id: str) -> bool:
        pass

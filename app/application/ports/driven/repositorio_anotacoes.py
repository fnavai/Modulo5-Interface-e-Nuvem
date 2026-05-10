# Porta driven: RepositorioAnotacoes (US IN-03)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.anotacao import Anotacao


class RepositorioAnotacoes(ABC):

    @abstractmethod
    def salvar(self, anotacao: Anotacao) -> None:
        """Insere ou atualiza por id. Reindexar mencoes a cada save."""
        pass

    @abstractmethod
    def obter(self, anotacao_id: str) -> Optional[Anotacao]:
        pass

    @abstractmethod
    def listar(
        self,
        repositorio: Optional[str] = None,
        modulo: Optional[str] = None,
        componente: Optional[str] = None,
        resolvida: Optional[bool] = None,
        autor_id: Optional[str] = None,
    ) -> List[Anotacao]:
        pass

    @abstractmethod
    def listar_thread(self, parent_id: str) -> List[Anotacao]:
        """Respostas de uma anotacao raiz, ordenadas por criacao."""
        pass

    @abstractmethod
    def listar_mencoes_de(self, usuario_id: str) -> List[Anotacao]:
        """Anotacoes onde o usuario foi mencionado."""
        pass

    @abstractmethod
    def remover(self, anotacao_id: str) -> bool:
        pass

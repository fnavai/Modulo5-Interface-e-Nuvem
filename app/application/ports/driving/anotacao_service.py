# Porta driving: AnotacaoService (US IN-03)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.anotacao import Anotacao


class AnotacaoService(ABC):

    @abstractmethod
    def criar(
        self,
        repositorio: str,
        modulo: str,
        componente: str,
        autor_id: str,
        conteudo: str,
        parent_id: Optional[str] = None,
    ) -> Anotacao:
        """Se parent_id for informado, cria como resposta no thread daquele id."""
        pass

    @abstractmethod
    def atualizar(self, anotacao_id: str, autor_id: str, conteudo: str) -> Anotacao:
        """Apenas o autor pode editar — levanta PermissaoAnotacaoNegadaError caso contrario."""
        pass

    @abstractmethod
    def resolver(self, anotacao_id: str) -> Anotacao:
        pass

    @abstractmethod
    def reabrir(self, anotacao_id: str) -> Anotacao:
        pass

    @abstractmethod
    def remover(self, anotacao_id: str, autor_id: str) -> bool:
        """Apenas o autor pode remover."""
        pass

    @abstractmethod
    def obter(self, anotacao_id: str) -> Anotacao:
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
        pass

    @abstractmethod
    def listar_mencoes_de(self, usuario_id: str) -> List[Anotacao]:
        pass

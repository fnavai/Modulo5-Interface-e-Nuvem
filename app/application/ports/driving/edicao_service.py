# Porta driving: RascunhoService (US IN-02)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.rascunho_edicao import RascunhoDiagrama, ResultadoPR


class RascunhoService(ABC):

    @abstractmethod
    def criar(
        self,
        repositorio: str,
        branch_base: str,
        autor_id: str,
        titulo: str,
        conteudo_mermaid: str,
        descricao_mudanca: str = "",
    ) -> RascunhoDiagrama:
        pass

    @abstractmethod
    def atualizar(
        self,
        rascunho_id: str,
        conteudo_mermaid: Optional[str] = None,
        descricao_mudanca: Optional[str] = None,
        titulo: Optional[str] = None,
    ) -> RascunhoDiagrama:
        pass

    @abstractmethod
    def obter(self, rascunho_id: str) -> RascunhoDiagrama:
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

    @abstractmethod
    def publicar_como_pr(
        self,
        rascunho_id: str,
        caminho_arquivo: str,
        mensagem_commit: str = "",
        titulo_pr: str = "",
        descricao_pr: str = "",
    ) -> ResultadoPR:
        """
        Cria branch + commit + PR no GitHub. Mantem o rascunho persistido — o time
        pode descartar via DELETE depois que o PR for mergeado.
        """
        pass

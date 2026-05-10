# Porta driving: RegraService (US IN-09)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.domain.entidades.regra_arquitetural import (
    RegraArquitetural,
    ResultadoAvaliacao,
    Severidade,
    TipoRegra,
)


class RegraService(ABC):

    @abstractmethod
    def criar(
        self,
        nome: str,
        tipo: TipoRegra,
        severidade: Severidade,
        parametros: Dict[str, Any],
        mensagem: str,
        criada_por: str,
    ) -> RegraArquitetural:
        pass

    @abstractmethod
    def atualizar(
        self,
        regra_id: str,
        nome: Optional[str] = None,
        severidade: Optional[Severidade] = None,
        parametros: Optional[Dict[str, Any]] = None,
        mensagem: Optional[str] = None,
        ativa: Optional[bool] = None,
    ) -> RegraArquitetural:
        pass

    @abstractmethod
    def obter(self, regra_id: str) -> RegraArquitetural:
        pass

    @abstractmethod
    def listar(self, ativa: Optional[bool] = None) -> List[RegraArquitetural]:
        pass

    @abstractmethod
    def remover(self, regra_id: str) -> bool:
        pass

    @abstractmethod
    def avaliar(
        self,
        repositorio: str,
        branch_head: str,
        arquivos_modificados: Tuple[str, ...],
    ) -> ResultadoAvaliacao:
        """Aplica todas as regras ATIVAS sobre as mudancas e devolve violacoes."""
        pass

    @abstractmethod
    def avaliar_e_comentar(
        self,
        repositorio: str,
        pr_numero: int,
        branch_head: str,
        arquivos_modificados: Tuple[str, ...],
    ) -> Tuple[ResultadoAvaliacao, Optional[int]]:
        """
        Avalia regras e, se houver violacoes, posta comentario no PR.
        Devolve (resultado, comentario_id_no_github_ou_None).
        """
        pass

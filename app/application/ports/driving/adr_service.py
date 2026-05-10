# Porta driving: ADRService (US IN-07)

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.domain.entidades.decisao_arquitetural import (
    ADR,
    StatusADR,
    VinculoComponenteADR,
)


class ADRService(ABC):

    @abstractmethod
    def template_padrao(self) -> Dict[str, str]:
        """Devolve o template para preenchimento (nao cria nada)."""
        pass

    @abstractmethod
    def criar(
        self,
        titulo: str,
        contexto: str,
        decisao: str,
        consequencias: str,
        autor_id: str,
    ) -> ADR:
        """Cria como RASCUNHO."""
        pass

    @abstractmethod
    def atualizar(
        self,
        adr_id: str,
        autor_id: str,
        titulo: Optional[str] = None,
        contexto: Optional[str] = None,
        decisao: Optional[str] = None,
        consequencias: Optional[str] = None,
    ) -> ADR:
        """Atualiza campos de uma ADR — apenas em RASCUNHO."""
        pass

    @abstractmethod
    def propor(self, adr_id: str, autor_id: str, documento_aprovacao_id: Optional[str] = None) -> ADR:
        """RASCUNHO -> PROPOSTA. Aceita opcional ref a documento PU-05."""
        pass

    @abstractmethod
    def aceitar(self, adr_id: str, autor_id: str) -> ADR:
        """PROPOSTA -> ACEITA."""
        pass

    @abstractmethod
    def descartar(self, adr_id: str, autor_id: str, motivo: str) -> ADR:
        """RASCUNHO/PROPOSTA -> DESCARTADA."""
        pass

    @abstractmethod
    def deprecar(self, adr_id: str, autor_id: str, motivo: str) -> ADR:
        """ACEITA -> DEPRECIADA."""
        pass

    @abstractmethod
    def superar(self, adr_id: str, nova_adr_id: str, autor_id: str) -> ADR:
        """ACEITA -> SUPERADA, anotando qual ADR substituiu."""
        pass

    @abstractmethod
    def obter(self, adr_id: str) -> ADR:
        pass

    @abstractmethod
    def listar(
        self,
        status: Optional[StatusADR] = None,
        autor_id: Optional[str] = None,
    ) -> List[ADR]:
        pass

    @abstractmethod
    def vincular_componente(
        self,
        adr_id: str,
        repositorio: str,
        modulo: str,
        descricao_componente: str,
    ) -> VinculoComponenteADR:
        pass

    @abstractmethod
    def desvincular_componente(self, adr_id: str, repositorio: str, modulo: str) -> bool:
        pass

    @abstractmethod
    def adrs_de_componente(self, repositorio: str, modulo: str) -> List[ADR]:
        pass

    @abstractmethod
    def marcadores_de_diagrama(
        self,
        repositorio: str,
        modulos: List[str],
    ) -> Dict[str, dict]:
        """Para cada modulo: contagem de ADRs por status, para o front desenhar icone."""
        pass

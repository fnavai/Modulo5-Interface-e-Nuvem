# Porta driving: NavegacaoService (US IN-01)

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.domain.entidades.link_codigo import LinkCodigo, ResultadoValidacao


@dataclass(frozen=True)
class RespostaNavegacao:
    link: LinkCodigo
    validacao: ResultadoValidacao

    def to_dict(self) -> dict:
        d = self.link.to_dict()
        d["validacao"] = self.validacao.to_dict()
        return d


class NavegacaoService(ABC):

    @abstractmethod
    def gerar_link(
        self,
        repositorio: str,
        arquivo: str,
        ref: str = "HEAD",
        linha: Optional[int] = None,
        linha_fim: Optional[int] = None,
        validar_existencia: bool = False,
    ) -> RespostaNavegacao:
        """
        Gera URL para visualizar arquivo+linha no GitHub.
        Se validar_existencia=True, faz HEAD na Contents API e retorna o resultado
        em RespostaNavegacao.validacao (sempre 200 — o link sai mesmo invalido).
        Levanta NavegacaoInvalidaError em inputs malformados.
        """
        pass

# Entidade de dominio: LinkCodigo (US IN-01)
# Representa um link clicavel para um arquivo no GitHub, com linha opcional.

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class LinkCodigo:
    repositorio: str   # ex: "fnavai/Modulo5-Interface-e-Nuvem"
    arquivo: str       # ex: "app/main.py"
    ref: str = "HEAD"  # branch, tag ou sha
    linha: Optional[int] = None
    linha_fim: Optional[int] = None
    abre_em_nova_aba: bool = True  # hint para o front: target="_blank"

    @property
    def url(self) -> str:
        base = f"https://github.com/{self.repositorio}/blob/{self.ref}/{self.arquivo}"
        if self.linha is None:
            return base
        if self.linha_fim is None or self.linha_fim == self.linha:
            return f"{base}#L{self.linha}"
        return f"{base}#L{self.linha}-L{self.linha_fim}"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "abre_em_nova_aba": self.abre_em_nova_aba,
            "componentes": {
                "repositorio": self.repositorio,
                "arquivo": self.arquivo,
                "ref": self.ref,
                "linha": self.linha,
                "linha_fim": self.linha_fim,
            },
        }


@dataclass(frozen=True)
class ResultadoValidacao:
    """
    Resultado da validacao opcional de existencia do arquivo no GitHub.
    `existe`:
       True  -> confirmado que existe
       False -> confirmado que nao existe (404)
       None  -> nao foi possivel verificar (GitHub fora, timeout)
    """
    executada: bool
    existe: Optional[bool] = None
    mensagem: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "executada": self.executada,
            "existe": self.existe,
            "mensagem": self.mensagem,
        }


_NAO_EXECUTADA = ResultadoValidacao(executada=False)


def validacao_nao_executada() -> ResultadoValidacao:
    return _NAO_EXECUTADA

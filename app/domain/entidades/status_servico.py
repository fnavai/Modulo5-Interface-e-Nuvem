# Entidade de dominio: StatusServico
# Responsabilidade: representar o estado de saúde de um servico externo,
# incluindo origem da resposta (live vs cache) para suportar fallback degradado.

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EstadoServico(Enum):
    DISPONIVEL = "disponivel"
    INDISPONIVEL = "indisponivel"
    DEGRADADO = "degradado"


@dataclass
class StatusServico:
    nome: str
    estado: EstadoServico
    detalhes: str = ""
    origem: str = "live"  # "live" = chamada fresca; "cache" = ultimo estado conhecido
    stale_segundos: Optional[int] = None  # idade do cache em segundos quando origem="cache"

    def esta_disponivel(self) -> bool:
        return self.estado == EstadoServico.DISPONIVEL

    def veio_do_cache(self) -> bool:
        return self.origem == "cache"

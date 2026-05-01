# Entidade de dominio: StatusServico
# Responsabilidade: representar o estado de saúde de um servico externo.

from dataclasses import dataclass
from enum import Enum


class EstadoServico(Enum):
    DISPONIVEL = "disponivel"
    INDISPONIVEL = "indisponivel"
    DEGRADADO = "degradado"


@dataclass
class StatusServico:
    nome: str
    estado: EstadoServico
    detalhes: str = ""

    def esta_disponivel(self) -> bool:
        return self.estado == EstadoServico.DISPONIVEL
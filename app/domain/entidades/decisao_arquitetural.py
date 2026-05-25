# Entidades de dominio para Decisoes Arquiteturais (US IN-07).

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class StatusADR(Enum):
    RASCUNHO = "rascunho"
    PROPOSTA = "proposta"
    ACEITA = "aceita"
    DESCARTADA = "descartada"
    DEPRECIADA = "depreciada"
    SUPERADA = "superada"


# Template padrao seguindo a convencao Michael Nygard.
TEMPLATE_ADR_PADRAO = {
    "titulo": "[Titulo curto da decisao em afirmativa, ex: 'Adotar PostgreSQL como banco principal']",
    "contexto": (
        "Descreva o problema e o contexto que motivam esta decisao. "
        "Quais forcas estao em jogo (tecnicas, politicas, sociais, projeto)?"
    ),
    "decisao": (
        "Descreva a decisao em afirmativa, ex: 'Vamos fazer X.' "
        "Inclua brevemente as alternativas consideradas e por que foram descartadas."
    ),
    "consequencias": (
        "Positivas:\n- ...\n\n"
        "Negativas:\n- ...\n\n"
        "Neutras (impacto a observar):\n- ..."
    ),
}


@dataclass(frozen=True)
class ADR:
    titulo: str
    contexto: str
    decisao: str
    consequencias: str
    autor_id: str
    status: StatusADR = StatusADR.RASCUNHO
    documento_aprovacao_id: Optional[str] = None  # ref opcional ao PU-05
    superada_por_id: Optional[str] = None
    motivo_descarte: Optional[str] = None
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "contexto": self.contexto,
            "decisao": self.decisao,
            "consequencias": self.consequencias,
            "autor_id": self.autor_id,
            "status": self.status.value,
            "documento_aprovacao_id": self.documento_aprovacao_id,
            "superada_por_id": self.superada_por_id,
            "motivo_descarte": self.motivo_descarte,
            "criada_em": self.criada_em.isoformat(),
            "atualizada_em": self.atualizada_em.isoformat(),
        }


@dataclass(frozen=True)
class VinculoComponenteADR:
    adr_id: str
    repositorio: str
    modulo: str
    descricao_componente: str = ""
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "adr_id": self.adr_id,
            "repositorio": self.repositorio,
            "modulo": self.modulo,
            "descricao_componente": self.descricao_componente,
            "criado_em": self.criado_em.isoformat(),
        }

# Entidades de dominio para regras arquiteturais e alertas em PR (US IN-09).

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Tuple
import uuid


class TipoRegra(Enum):
    ARQUIVO_PROIBIDO = "arquivo_proibido"        # parametros: {padrao_glob}
    LIMITE_ARQUIVOS = "limite_arquivos"          # parametros: {limite}
    PAR_OBRIGATORIO = "par_obrigatorio"          # parametros: {padrao_origem, padrao_par}
    PADRAO_BRANCH = "padrao_branch"              # parametros: {regex}


class Severidade(Enum):
    INFO = "info"        # comentario informativo
    WARNING = "warning"  # alerta — recomenda revisar
    ERROR = "error"      # bloqueador moral (nao bloqueia merge no GitHub, apenas sinaliza)


# Severidades ordenadas por gravidade — usado pra sumarizar e exibir.
ORDEM_SEVERIDADE = (Severidade.INFO, Severidade.WARNING, Severidade.ERROR)


@dataclass(frozen=True)
class RegraArquitetural:
    nome: str
    tipo: TipoRegra
    severidade: Severidade
    parametros: Dict[str, Any] = field(default_factory=dict)
    mensagem: str = ""
    ativa: bool = True
    criada_por: str = "system"
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo.value,
            "severidade": self.severidade.value,
            "parametros": dict(self.parametros),
            "mensagem": self.mensagem,
            "ativa": self.ativa,
            "criada_por": self.criada_por,
            "criada_em": self.criada_em.isoformat(),
            "atualizada_em": self.atualizada_em.isoformat(),
        }


@dataclass(frozen=True)
class ViolacaoRegra:
    regra_id: str
    regra_nome: str
    tipo: TipoRegra
    severidade: Severidade
    mensagem: str
    arquivos_envolvidos: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regra_id": self.regra_id,
            "regra_nome": self.regra_nome,
            "tipo": self.tipo.value,
            "severidade": self.severidade.value,
            "mensagem": self.mensagem,
            "arquivos_envolvidos": list(self.arquivos_envolvidos),
        }


@dataclass(frozen=True)
class ResultadoAvaliacao:
    repositorio: str
    branch_head: str
    arquivos_modificados: Tuple[str, ...]
    regras_aplicadas: int
    violacoes: Tuple[ViolacaoRegra, ...]

    @property
    def tem_violacoes(self) -> bool:
        return len(self.violacoes) > 0

    @property
    def total_por_severidade(self) -> Dict[str, int]:
        out = {s.value: 0 for s in Severidade}
        for v in self.violacoes:
            out[v.severidade.value] += 1
        return out

    @property
    def severidade_maxima(self) -> str:
        if not self.violacoes:
            return "ok"
        for sev in reversed(ORDEM_SEVERIDADE):
            if any(v.severidade == sev for v in self.violacoes):
                return sev.value
        return "ok"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositorio": self.repositorio,
            "branch_head": self.branch_head,
            "arquivos_modificados": list(self.arquivos_modificados),
            "regras_aplicadas": self.regras_aplicadas,
            "tem_violacoes": self.tem_violacoes,
            "severidade_maxima": self.severidade_maxima,
            "total_por_severidade": self.total_por_severidade,
            "violacoes": [v.to_dict() for v in self.violacoes],
        }

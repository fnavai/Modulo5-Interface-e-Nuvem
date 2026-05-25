# Entidade de dominio: Anotacao (US IN-03)
# Comentarios ancorados em (repositorio, modulo, componente) com threads e @mencoes.

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
import uuid


# Regex para extrair @mencoes do conteudo. Aceita letras, numeros, hifen e underscore.
# Captura sem o '@' inicial.
_REGEX_MENCAO = re.compile(r"(?:^|\s)@([A-Za-z0-9_-]+)")


def extrair_mencoes(conteudo: str) -> Tuple[str, ...]:
    """
    Extrai @mencoes do conteudo, mantendo ordem de aparicao e sem duplicatas.
    Exemplo: 'Olha @alice e @bob, depois @alice de novo' -> ('alice', 'bob')
    """
    if not conteudo:
        return ()
    vistos = set()
    ordem: list = []
    for match in _REGEX_MENCAO.finditer(conteudo):
        usuario = match.group(1)
        if usuario not in vistos:
            vistos.add(usuario)
            ordem.append(usuario)
    return tuple(ordem)


@dataclass(frozen=True)
class Anotacao:
    repositorio: str
    modulo: str
    componente: str
    autor_id: str
    conteudo: str
    parent_id: Optional[str] = None     # None = raiz do thread; senao, resposta
    resolvida: bool = False
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def mencoes(self) -> Tuple[str, ...]:
        """Calculada on demand a partir do conteudo — fonte da verdade."""
        return extrair_mencoes(self.conteudo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "repositorio": self.repositorio,
            "modulo": self.modulo,
            "componente": self.componente,
            "autor_id": self.autor_id,
            "conteudo": self.conteudo,
            "mencoes": list(self.mencoes),
            "parent_id": self.parent_id,
            "resolvida": self.resolvida,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
        }

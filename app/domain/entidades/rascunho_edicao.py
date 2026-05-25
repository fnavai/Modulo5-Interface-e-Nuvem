# Entidades de dominio para o editor de diagramas (US IN-02).

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


@dataclass(frozen=True)
class RascunhoDiagrama:
    repositorio: str          # "owner/repo" — onde o PR sera aberto
    branch_base: str          # branch que vai receber o merge (ex: "develop")
    autor_id: str
    titulo: str
    conteudo_mermaid: str     # codigo Mermaid produzido pelo editor visual
    descricao_mudanca: str = ""
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "repositorio": self.repositorio,
            "branch_base": self.branch_base,
            "autor_id": self.autor_id,
            "titulo": self.titulo,
            "conteudo_mermaid": self.conteudo_mermaid,
            "descricao_mudanca": self.descricao_mudanca,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
        }


@dataclass(frozen=True)
class ResultadoPR:
    """Saida da publicacao de um rascunho como PR no GitHub."""
    repositorio: str
    branch_criada: str
    branch_base: str
    commit_sha: str
    pr_numero: int
    pr_url: str
    arquivo_publicado: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositorio": self.repositorio,
            "branch_criada": self.branch_criada,
            "branch_base": self.branch_base,
            "commit_sha": self.commit_sha,
            "pr_numero": self.pr_numero,
            "pr_url": self.pr_url,
            "arquivo_publicado": self.arquivo_publicado,
        }

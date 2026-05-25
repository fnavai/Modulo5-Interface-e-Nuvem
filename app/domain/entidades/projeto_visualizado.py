# Entidade de dominio: ProjetoVisualizado
# Responsabilidade: agregar o resultado do fluxo unificado do portal
# (diagrama do Gerador + resumo da IA + ownership do Perfis) numa unica
# visao, sinalizando partes que faltaram (degradacao graciosa: uma falha
# parcial nao derruba a tela).

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReferenciaRepo:
    owner: str
    repo: str
    branch: str
    caminho: str

    def to_dict(self) -> dict:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "branch": self.branch,
            "caminho": self.caminho,
        }


@dataclass
class ProjetoVisualizado:
    referencia: ReferenciaRepo
    diagrama_mermaid: Optional[str]
    resumo_ia: Optional[dict]
    ownership: Optional[dict]
    # Diagnostico de qualidade da IA (acoplamento/ciclos/severidade).
    # Opcional e best-effort: None quando a IA/fonte do codigo falha.
    # NAO entra em partes_faltantes (so os 3 originais) — a tela mostra
    # o vazio no proprio painel, como faz com resumo_ia/ownership.
    qualidade: Optional[dict] = None

    @property
    def tem_diagrama(self) -> bool:
        return bool(self.diagrama_mermaid)

    @property
    def tem_qualidade(self) -> bool:
        return self.qualidade is not None

    def partes_faltantes(self) -> list:
        faltantes = []
        if not self.tem_diagrama:
            faltantes.append("diagrama")
        if self.resumo_ia is None:
            faltantes.append("resumo_ia")
        if self.ownership is None:
            faltantes.append("ownership")
        return faltantes

    def to_dict(self) -> dict:
        return {
            "referencia": self.referencia.to_dict(),
            "diagrama_mermaid": self.diagrama_mermaid,
            "resumo_ia": self.resumo_ia,
            "ownership": self.ownership,
            "qualidade": self.qualidade,
            "partes_faltantes": self.partes_faltantes(),
        }

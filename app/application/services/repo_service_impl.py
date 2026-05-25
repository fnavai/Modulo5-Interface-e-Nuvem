# Implementacao do RepoService: delega ao ExploradorRepositorio e
# filtra arquivos por extensao de codigo (funcao pura, testavel).

from app.application.ports.driving.repo_service import RepoService
from app.application.ports.driven.explorador_repositorio import (
    ExploradorRepositorio,
)

# Extensoes consideradas "codigo" (o que rende diagrama/qualidade).
# .py primeiro na ordenacao (a IA analisa Python por AST).
EXTENSOES_CODIGO = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb",
    ".cs", ".cpp", ".cc", ".c", ".h", ".hpp", ".rs", ".kt", ".php",
    ".swift", ".scala", ".m", ".mm",
)
_LIMITE = 2000  # nao explodir o dropdown / payload


def filtrar_codigo(caminhos: list) -> list:
    """Mantem so arquivos de codigo; .py primeiro, depois alfabetico."""
    sel = [
        c for c in (caminhos or [])
        if isinstance(c, str) and c.lower().endswith(EXTENSOES_CODIGO)
    ]
    sel.sort(key=lambda c: (0 if c.lower().endswith(".py") else 1, c))
    return sel[:_LIMITE]


class RepoServiceImpl(RepoService):

    def __init__(self, explorador: ExploradorRepositorio):
        self._exp = explorador

    def listar_branches(self, owner: str, repo: str) -> list:
        return self._exp.listar_branches(owner, repo)

    def listar_arquivos_codigo(
        self, owner: str, repo: str, branch: str
    ) -> list:
        return filtrar_codigo(
            self._exp.listar_arquivos(owner, repo, branch)
        )

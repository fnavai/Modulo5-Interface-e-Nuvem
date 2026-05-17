# Porta driving: RepoService
# Contrato para os seletores do portal: branches e arquivos de codigo
# de um repo do GitHub.

from abc import ABC, abstractmethod


class RepoService(ABC):

    @abstractmethod
    def listar_branches(self, owner: str, repo: str) -> list:
        """Nomes das branches (develop/main primeiro)."""
        pass

    @abstractmethod
    def listar_arquivos_codigo(
        self, owner: str, repo: str, branch: str
    ) -> list:
        """Caminhos de arquivos de codigo (filtrados por extensao)."""
        pass

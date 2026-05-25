# Porta driven: ValidadorArquivoGitHub (US IN-01)
# Verifica se um caminho existe num repositorio + ref do GitHub.

from abc import ABC, abstractmethod


class ValidadorArquivoGitHub(ABC):

    @abstractmethod
    def existe(self, repositorio: str, arquivo: str, ref: str) -> bool:
        """
        True se o arquivo existir, False se 404.
        Levanta GitHubIndisponivelError se nao conseguir alcancar o GitHub.
        """
        pass

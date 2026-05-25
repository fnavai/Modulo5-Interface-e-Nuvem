# Porta driven: ExploradorRepositorio
# Lista branches e caminhos de arquivos de um repo do GitHub, para o
# portal oferecer seletores (sem o usuario digitar branch/arquivo).

from abc import ABC, abstractmethod


class ExploradorRepositorio(ABC):

    @abstractmethod
    def listar_branches(self, owner: str, repo: str) -> list:
        """
        Lista os nomes das branches do repo. Levanta excecao de dominio
        (FalhaNaComunicacaoError) se o GitHub falhar; lista vazia se o
        repo nao tiver branches.
        """
        pass

    @abstractmethod
    def listar_arquivos(self, owner: str, repo: str, branch: str) -> list:
        """
        Lista os caminhos de TODOS os arquivos (blobs) do repo na branch
        (a filtragem por extensao de codigo e responsabilidade do
        RepoService). Levanta excecao de dominio se o GitHub falhar.
        """
        pass

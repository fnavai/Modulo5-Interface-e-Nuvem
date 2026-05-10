# Porta driven: PublicadorPR (US IN-02)
# Cria branch, commita arquivo e abre PR no GitHub a partir de um rascunho.

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PRPublicado:
    branch_criada: str
    commit_sha: str
    pr_numero: int
    pr_url: str


class PublicadorPR(ABC):

    @abstractmethod
    def publicar(
        self,
        repositorio: str,
        branch_base: str,
        nome_branch: str,
        caminho_arquivo: str,
        conteudo: str,
        mensagem_commit: str,
        titulo_pr: str,
        descricao_pr: str,
    ) -> PRPublicado:
        """
        Fluxo: pega SHA do branch_base -> cria nova branch -> PUT do arquivo
        (com SHA se ja existir) -> abre PR. Levanta PublicacaoPRError em qualquer falha.
        """
        pass

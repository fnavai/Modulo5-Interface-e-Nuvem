# Adaptador fake — usado em testes e dev offline.

from typing import Dict, Optional, Tuple

from app.application.ports.driven.validador_arquivo_github import ValidadorArquivoGitHub
from app.domain.excecoes import GitHubIndisponivelError


class ValidadorArquivoGitHubFake(ValidadorArquivoGitHub):

    def __init__(self):
        self._respostas: Dict[Tuple[str, str, str], bool] = {}
        self._falha: Optional[Exception] = None

    def configurar(self, repo: str, arquivo: str, ref: str, existe: bool) -> None:
        self._respostas[(repo, arquivo, ref)] = existe

    def fazer_falhar_com(self, excecao: Exception) -> None:
        self._falha = excecao

    def reset(self) -> None:
        self._respostas.clear()
        self._falha = None

    def existe(self, repositorio: str, arquivo: str, ref: str) -> bool:
        if self._falha is not None:
            raise self._falha
        chave = (repositorio, arquivo, ref)
        if chave in self._respostas:
            return self._respostas[chave]
        # Default: nao existe — forca configuracao explicita nos testes.
        return False

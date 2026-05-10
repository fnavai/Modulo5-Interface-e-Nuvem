# Adaptador driven: usa Contents API do GitHub para verificar existencia do arquivo.
# HEAD na URL ja basta — economiza payload.

from typing import Optional

import requests

from app.application.ports.driven.validador_arquivo_github import ValidadorArquivoGitHub
from app.domain.excecoes import GitHubIndisponivelError


class ValidadorArquivoGitHubHTTP(ValidadorArquivoGitHub):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 5.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

    def existe(self, repositorio: str, arquivo: str, ref: str) -> bool:
        url = f"{self._base}/repos/{repositorio}/contents/{arquivo}"
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        params = {"ref": ref} if ref and ref != "HEAD" else None
        try:
            resposta = requests.head(
                url, headers=headers, params=params, timeout=self._timeout, allow_redirects=True
            )
        except requests.exceptions.RequestException as e:
            raise GitHubIndisponivelError(f"falha de rede: {e}") from e

        if resposta.status_code == 200:
            return True
        if resposta.status_code == 404:
            return False
        if resposta.status_code in (403, 429):
            raise GitHubIndisponivelError(
                f"GitHub bloqueou a chamada ({resposta.status_code}, possivel rate-limit)."
            )
        if resposta.status_code in (502, 503, 504):
            raise GitHubIndisponivelError(f"GitHub respondeu {resposta.status_code}.")
        # Outros codigos: nao sabemos — tratamos como indisponibilidade pra nao mentir pro usuario.
        raise GitHubIndisponivelError(f"GitHub retornou {resposta.status_code} inesperado.")

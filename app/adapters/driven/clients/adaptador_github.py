# Adaptador driven: FonteCodigo via raw.githubusercontent.com
# Busca o conteudo cru de um arquivo (best-effort). Usado para alimentar
# a analise de qualidade da IA (que recebe {"codigo": <str>}).

import requests

from app.application.ports.driven.fonte_codigo import FonteCodigo
from app.config.settings import GITHUB_TOKEN, GITHUB_TIMEOUT_SEGUNDOS

_RAW_BASE = "https://raw.githubusercontent.com"


class AdaptadorGitHub(FonteCodigo):

    def __init__(self, token: str = None, timeout_segundos: float = None):
        self._token = token if token is not None else (GITHUB_TOKEN or None)
        self._timeout = (
            timeout_segundos
            if timeout_segundos is not None
            else GITHUB_TIMEOUT_SEGUNDOS
        )

    def obter_arquivo(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> "str | None":
        caminho = (caminho or "").lstrip("/")
        if not owner or not repo or not branch or not caminho:
            return None
        if ".." in caminho:  # defense-in-depth (rota ja bloqueia)
            return None
        url = f"{_RAW_BASE}/{owner}/{repo}/{branch}/{caminho}"
        headers = {}
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        try:
            resp = requests.get(url, headers=headers, timeout=self._timeout)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError):
            return None
        if resp.status_code != 200:
            return None
        try:
            texto = resp.text
        except Exception:
            return None
        # Evita mandar binario p/ a IA (ela faz ast.parse).
        if "\x00" in texto[:4096]:
            return None
        return texto

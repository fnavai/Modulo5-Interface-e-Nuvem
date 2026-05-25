# Adaptador driven: ExploradorRepositorio via GitHub REST API.
# Branches: GET /repos/{o}/{r}/branches  (paginado)
# Arquivos: GET /repos/{o}/{r}/git/trees/{branch}?recursive=1

import requests

from app.application.ports.driven.explorador_repositorio import (
    ExploradorRepositorio,
)
from app.config.settings import (
    GITHUB_BASE_URL,
    GITHUB_TOKEN,
    GITHUB_TIMEOUT_SEGUNDOS,
)
from app.domain.excecoes import FalhaNaComunicacaoError

_MAX_PAGINAS = 5  # 5*100 = ate 500 branches


class AdaptadorGitHubExplorador(ExploradorRepositorio):

    def __init__(self, base_url: str = None, token: str = None,
                 timeout_segundos: float = None):
        self._base = (base_url or GITHUB_BASE_URL).rstrip("/")
        self._token = token if token is not None else (GITHUB_TOKEN or None)
        self._timeout = (timeout_segundos
                         if timeout_segundos is not None
                         else GITHUB_TIMEOUT_SEGUNDOS)

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _get(self, url: str, params: dict = None):
        try:
            return requests.get(url, headers=self._headers(),
                                 params=params, timeout=self._timeout)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            raise FalhaNaComunicacaoError(
                f"GitHub inacessivel: {e}") from e

    def listar_branches(self, owner: str, repo: str) -> list:
        nomes = []
        for pagina in range(1, _MAX_PAGINAS + 1):
            r = self._get(
                f"{self._base}/repos/{owner}/{repo}/branches",
                {"per_page": 100, "page": pagina},
            )
            if r.status_code != 200:
                raise FalhaNaComunicacaoError(
                    f"GitHub respondeu {r.status_code} ao listar branches.")
            try:
                lote = r.json()
            except ValueError:
                break
            if not isinstance(lote, list) or not lote:
                break
            nomes.extend(b.get("name") for b in lote if b.get("name"))
            if len(lote) < 100:
                break
        # develop/main primeiro (conveniencia do portal)
        prioridade = {"develop": 0, "main": 1, "master": 2}
        return sorted(nomes, key=lambda n: (prioridade.get(n, 9), n))

    def listar_arquivos(self, owner: str, repo: str, branch: str) -> list:
        r = self._get(
            f"{self._base}/repos/{owner}/{repo}/git/trees/{branch}",
            {"recursive": "1"},
        )
        if r.status_code != 200:
            raise FalhaNaComunicacaoError(
                f"GitHub respondeu {r.status_code} ao listar arquivos "
                f"(branch '{branch}').")
        try:
            dados = r.json()
        except ValueError:
            return []
        arvore = dados.get("tree") or []
        return [
            n.get("path") for n in arvore
            if n.get("type") == "blob" and n.get("path")
        ]

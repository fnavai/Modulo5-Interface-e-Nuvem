# Adaptador driven: posta comentarios em PRs do GitHub via Issues API (US IN-09).

import logging
from typing import List, Optional

import requests

from app.application.ports.driven.notificador_comentario_pr import (
    NotificadorComentarioPR,
)
from app.domain.excecoes import ComentarioPRError


_logger = logging.getLogger("interface.notificador_pr")


class NotificadorComentarioPRGitHubHTTP(NotificadorComentarioPR):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 10.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

    def comentar(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        if not self._token:
            raise ComentarioPRError(
                "GITHUB_TOKEN ausente — necessario com permissao de issues:write."
            )
        url = f"{self._base}/repos/{repositorio}/issues/{pr_numero}/comments"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
        }
        try:
            r = requests.post(url, headers=headers, json={"body": mensagem}, timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise ComentarioPRError(f"erro de rede ao postar comentario: {e}") from e
        if r.status_code in (200, 201):
            return (r.json() or {}).get("id")
        raise ComentarioPRError(
            f"GitHub retornou {r.status_code} ao postar comentario: {r.text[:200]}"
        )


class NotificadorComentarioPRFake(NotificadorComentarioPR):
    """Fake para testes — registra cada chamada."""

    def __init__(self):
        self.chamadas: List[dict] = []
        self._proximo_id = 500
        self._falhar: bool = False

    def fazer_falhar(self) -> None:
        self._falhar = True

    def comentar(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        if self._falhar:
            raise ComentarioPRError("fake configurado para falhar")
        registro = {
            "repositorio": repositorio, "pr_numero": pr_numero,
            "mensagem": mensagem, "id": self._proximo_id,
        }
        self.chamadas.append(registro)
        self._proximo_id += 1
        return registro["id"]

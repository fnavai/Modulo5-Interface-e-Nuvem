# Adaptador driven: cria branch + commit + PR no GitHub (US IN-02).

import base64
from typing import Optional

import requests

from app.application.ports.driven.publicador_pr import PRPublicado, PublicadorPR
from app.domain.excecoes import PublicacaoPRError


class PublicadorPRGitHubHTTP(PublicadorPR):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 10.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

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
        if not self._token:
            raise PublicacaoPRError(
                "GITHUB_TOKEN ausente — necessario com permissao de write para criar branch e PR."
            )

        sha_base = self._sha_da_branch(repositorio, branch_base)
        self._criar_ref(repositorio, nome_branch, sha_base)

        sha_existente = self._sha_de_arquivo(repositorio, caminho_arquivo, nome_branch)
        commit_sha = self._put_arquivo(
            repositorio, caminho_arquivo, conteudo, mensagem_commit, nome_branch, sha_existente,
        )
        pr_numero, pr_url = self._abrir_pr(
            repositorio, nome_branch, branch_base, titulo_pr, descricao_pr,
        )
        return PRPublicado(
            branch_criada=nome_branch, commit_sha=commit_sha,
            pr_numero=pr_numero, pr_url=pr_url,
        )

    # ------------------------------------------------------------------
    # Chamadas individuais ao GitHub
    # ------------------------------------------------------------------

    def _sha_da_branch(self, repo: str, branch: str) -> str:
        url = f"{self._base}/repos/{repo}/git/ref/heads/{branch}"
        resposta = self._get(url, "obter SHA da branch base")
        return resposta.json()["object"]["sha"]

    def _criar_ref(self, repo: str, nome_branch: str, sha_base: str) -> None:
        url = f"{self._base}/repos/{repo}/git/refs"
        payload = {"ref": f"refs/heads/{nome_branch}", "sha": sha_base}
        try:
            r = requests.post(url, headers=self._headers(), json=payload, timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise PublicacaoPRError(f"erro de rede ao criar branch: {e}") from e
        if r.status_code == 422 and "already exists" in r.text.lower():
            raise PublicacaoPRError(
                f"Branch '{nome_branch}' ja existe — gere outro rascunho ou apague a branch."
            )
        if r.status_code not in (200, 201):
            raise PublicacaoPRError(
                f"GitHub retornou {r.status_code} ao criar branch: {r.text[:200]}"
            )

    def _sha_de_arquivo(self, repo: str, caminho: str, branch: str) -> Optional[str]:
        """Retorna SHA do arquivo se ja existir na branch (necessario pra update); None se 404."""
        url = f"{self._base}/repos/{repo}/contents/{caminho}"
        try:
            r = requests.get(
                url, headers=self._headers(), params={"ref": branch}, timeout=self._timeout,
            )
        except requests.exceptions.RequestException as e:
            raise PublicacaoPRError(f"erro de rede ao consultar arquivo: {e}") from e
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise PublicacaoPRError(
                f"GitHub retornou {r.status_code} ao consultar arquivo: {r.text[:200]}"
            )
        return r.json().get("sha")

    def _put_arquivo(
        self,
        repo: str, caminho: str, conteudo: str,
        mensagem: str, branch: str, sha_existente: Optional[str],
    ) -> str:
        url = f"{self._base}/repos/{repo}/contents/{caminho}"
        payload = {
            "message": mensagem,
            "content": base64.b64encode(conteudo.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha_existente:
            payload["sha"] = sha_existente
        try:
            r = requests.put(url, headers=self._headers(), json=payload, timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise PublicacaoPRError(f"erro de rede ao commitar arquivo: {e}") from e
        if r.status_code not in (200, 201):
            raise PublicacaoPRError(
                f"GitHub retornou {r.status_code} ao commitar arquivo: {r.text[:200]}"
            )
        return r.json()["commit"]["sha"]

    def _abrir_pr(
        self, repo: str, head: str, base: str, titulo: str, descricao: str,
    ) -> tuple:
        url = f"{self._base}/repos/{repo}/pulls"
        payload = {"title": titulo, "head": head, "base": base, "body": descricao}
        try:
            r = requests.post(url, headers=self._headers(), json=payload, timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise PublicacaoPRError(f"erro de rede ao abrir PR: {e}") from e
        if r.status_code not in (200, 201):
            raise PublicacaoPRError(
                f"GitHub retornou {r.status_code} ao abrir PR: {r.text[:200]}"
            )
        body = r.json()
        return body["number"], body["html_url"]

    def _get(self, url: str, contexto: str):
        try:
            r = requests.get(url, headers=self._headers(), timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise PublicacaoPRError(f"erro de rede ao {contexto}: {e}") from e
        if r.status_code != 200:
            raise PublicacaoPRError(
                f"GitHub retornou {r.status_code} ao {contexto}: {r.text[:200]}"
            )
        return r

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
        }


class PublicadorPRFake(PublicadorPR):
    """Fake para testes — registra cada chamada e devolve dados simulados."""

    def __init__(self):
        self.chamadas: list = []
        self._proximo_pr = 100
        self._falha: Optional[Exception] = None

    def fazer_falhar_com(self, exc: Exception) -> None:
        self._falha = exc

    def publicar(
        self,
        repositorio, branch_base, nome_branch, caminho_arquivo,
        conteudo, mensagem_commit, titulo_pr, descricao_pr,
    ) -> PRPublicado:
        if self._falha is not None:
            raise self._falha
        self.chamadas.append({
            "repositorio": repositorio, "branch_base": branch_base,
            "nome_branch": nome_branch, "caminho_arquivo": caminho_arquivo,
            "conteudo": conteudo, "mensagem_commit": mensagem_commit,
            "titulo_pr": titulo_pr, "descricao_pr": descricao_pr,
        })
        publicado = PRPublicado(
            branch_criada=nome_branch,
            commit_sha=f"fake-sha-{self._proximo_pr}",
            pr_numero=self._proximo_pr,
            pr_url=f"https://github.com/{repositorio}/pull/{self._proximo_pr}",
        )
        self._proximo_pr += 1
        return publicado

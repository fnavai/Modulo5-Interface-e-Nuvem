# Implementacao do RascunhoService (US IN-02).
# Persiste rascunhos localmente e usa PublicadorPR para criar branch+commit+PR no GitHub.

import re
from dataclasses import replace
from datetime import datetime, timezone
from typing import List, Optional

from app.application.ports.driven.publicador_pr import PublicadorPR
from app.application.ports.driven.repositorio_rascunhos import RepositorioRascunhos
from app.application.ports.driving.edicao_service import RascunhoService
from app.domain.entidades.rascunho_edicao import RascunhoDiagrama, ResultadoPR
from app.domain.excecoes import (
    RascunhoInvalidoError,
    RascunhoNaoEncontradoError,
)


_REGEX_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
_REGEX_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")


class RascunhoServiceImpl(RascunhoService):

    def __init__(self, repositorio: RepositorioRascunhos, publicador: PublicadorPR):
        self._repo = repositorio
        self._publicador = publicador

    def criar(
        self,
        repositorio: str,
        branch_base: str,
        autor_id: str,
        titulo: str,
        conteudo_mermaid: str,
        descricao_mudanca: str = "",
    ) -> RascunhoDiagrama:
        repo = self._validar_repo(repositorio)
        branch = self._validar_branch(branch_base)
        self._exigir_strings(autor_id=autor_id, titulo=titulo, conteudo_mermaid=conteudo_mermaid)
        rascunho = RascunhoDiagrama(
            repositorio=repo,
            branch_base=branch,
            autor_id=autor_id.strip(),
            titulo=titulo.strip(),
            conteudo_mermaid=conteudo_mermaid,
            descricao_mudanca=(descricao_mudanca or "").strip(),
        )
        self._repo.salvar(rascunho)
        return rascunho

    def atualizar(
        self,
        rascunho_id: str,
        conteudo_mermaid: Optional[str] = None,
        descricao_mudanca: Optional[str] = None,
        titulo: Optional[str] = None,
    ) -> RascunhoDiagrama:
        atual = self._exigir(rascunho_id)
        novos = {"atualizado_em": datetime.now(timezone.utc)}
        if conteudo_mermaid is not None:
            if not conteudo_mermaid or not conteudo_mermaid.strip():
                raise RascunhoInvalidoError("conteudo_mermaid nao pode ser vazio.")
            novos["conteudo_mermaid"] = conteudo_mermaid
        if descricao_mudanca is not None:
            novos["descricao_mudanca"] = descricao_mudanca.strip()
        if titulo is not None:
            if not titulo.strip():
                raise RascunhoInvalidoError("titulo nao pode ser vazio.")
            novos["titulo"] = titulo.strip()
        atualizado = replace(atual, **novos)
        self._repo.salvar(atualizado)
        return atualizado

    def obter(self, rascunho_id: str) -> RascunhoDiagrama:
        return self._exigir(rascunho_id)

    def listar(
        self,
        autor_id: Optional[str] = None,
        repositorio: Optional[str] = None,
    ) -> List[RascunhoDiagrama]:
        return self._repo.listar(autor_id=autor_id, repositorio=repositorio)

    def remover(self, rascunho_id: str) -> bool:
        return self._repo.remover(rascunho_id)

    def publicar_como_pr(
        self,
        rascunho_id: str,
        caminho_arquivo: str,
        mensagem_commit: str = "",
        titulo_pr: str = "",
        descricao_pr: str = "",
    ) -> ResultadoPR:
        rascunho = self._exigir(rascunho_id)
        caminho = self._validar_caminho(caminho_arquivo)

        nome_branch = self._gerar_nome_branch(rascunho)
        msg_commit = mensagem_commit.strip() or f"docs(diagrama): {rascunho.titulo}"
        titulo = titulo_pr.strip() or f"docs(diagrama): {rascunho.titulo}"
        descricao = descricao_pr.strip() or self._descricao_pr_default(rascunho, caminho)

        publicado = self._publicador.publicar(
            repositorio=rascunho.repositorio,
            branch_base=rascunho.branch_base,
            nome_branch=nome_branch,
            caminho_arquivo=caminho,
            conteudo=rascunho.conteudo_mermaid,
            mensagem_commit=msg_commit,
            titulo_pr=titulo,
            descricao_pr=descricao,
        )

        return ResultadoPR(
            repositorio=rascunho.repositorio,
            branch_criada=publicado.branch_criada,
            branch_base=rascunho.branch_base,
            commit_sha=publicado.commit_sha,
            pr_numero=publicado.pr_numero,
            pr_url=publicado.pr_url,
            arquivo_publicado=caminho,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _exigir(self, rascunho_id: str) -> RascunhoDiagrama:
        if not rascunho_id or not rascunho_id.strip():
            raise RascunhoNaoEncontradoError("rascunho_id obrigatorio.")
        r = self._repo.obter(rascunho_id.strip())
        if r is None:
            raise RascunhoNaoEncontradoError(f"Rascunho {rascunho_id} nao existe.")
        return r

    @staticmethod
    def _validar_repo(repo: str) -> str:
        if not repo or not repo.strip():
            raise RascunhoInvalidoError("repositorio e obrigatorio.")
        n = repo.strip()
        if not _REGEX_REPO.match(n):
            raise RascunhoInvalidoError(f"repositorio '{repo}' invalido. Use 'owner/repo'.")
        return n

    @staticmethod
    def _validar_branch(branch: str) -> str:
        if not branch or not branch.strip():
            raise RascunhoInvalidoError("branch_base e obrigatorio.")
        n = branch.strip()
        if not _REGEX_BRANCH.match(n):
            raise RascunhoInvalidoError(f"branch '{branch}' contem caracteres invalidos.")
        return n

    @staticmethod
    def _validar_caminho(caminho: str) -> str:
        if not caminho or not caminho.strip():
            raise RascunhoInvalidoError("caminho_arquivo e obrigatorio.")
        n = caminho.strip().lstrip("/")
        if ".." in n.split("/"):
            raise RascunhoInvalidoError(f"caminho_arquivo '{caminho}' contem '..' — nao permitido.")
        return n

    @staticmethod
    def _exigir_strings(**campos: str) -> None:
        for nome, valor in campos.items():
            if not valor or not valor.strip():
                raise RascunhoInvalidoError(f"campo '{nome}' e obrigatorio.")

    @staticmethod
    def _gerar_nome_branch(rascunho: RascunhoDiagrama) -> str:
        sufixo = rascunho.id[:8]
        slug = re.sub(r"[^a-z0-9-]+", "-", rascunho.titulo.lower()).strip("-")[:40] or "diagrama"
        return f"diagram-edit/{slug}-{sufixo}"

    @staticmethod
    def _descricao_pr_default(rascunho: RascunhoDiagrama, caminho: str) -> str:
        partes = [
            f"Atualizacao do diagrama em `{caminho}` via editor visual (Interface-e-Nuvem).",
            "",
            f"**Autor:** {rascunho.autor_id}",
            f"**Branch base:** `{rascunho.branch_base}`",
        ]
        if rascunho.descricao_mudanca:
            partes.append("")
            partes.append("### Mudancas")
            partes.append(rascunho.descricao_mudanca)
        return "\n".join(partes)

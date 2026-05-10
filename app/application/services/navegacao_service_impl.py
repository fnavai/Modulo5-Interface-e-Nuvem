# Implementacao do NavegacaoService (US IN-01).
# Valida inputs, monta o LinkCodigo e (opcionalmente) consulta o GitHub.

import re
from typing import Optional

from app.application.ports.driven.validador_arquivo_github import ValidadorArquivoGitHub
from app.application.ports.driving.navegacao_service import (
    NavegacaoService,
    RespostaNavegacao,
)
from app.domain.entidades.link_codigo import (
    LinkCodigo,
    ResultadoValidacao,
    validacao_nao_executada,
)
from app.domain.excecoes import GitHubIndisponivelError, NavegacaoInvalidaError


_REGEX_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


class NavegacaoServiceImpl(NavegacaoService):

    def __init__(self, validador: Optional[ValidadorArquivoGitHub] = None):
        # Validador opcional — quando None, validar_existencia retorna mensagem amigavel
        # de "validador nao configurado".
        self._validador = validador

    def gerar_link(
        self,
        repositorio: str,
        arquivo: str,
        ref: str = "HEAD",
        linha: Optional[int] = None,
        linha_fim: Optional[int] = None,
        validar_existencia: bool = False,
    ) -> RespostaNavegacao:
        repositorio_n = self._validar_repositorio(repositorio)
        arquivo_n = self._validar_arquivo(arquivo)
        ref_n = self._validar_ref(ref)
        self._validar_linhas(linha, linha_fim)

        link = LinkCodigo(
            repositorio=repositorio_n,
            arquivo=arquivo_n,
            ref=ref_n,
            linha=linha,
            linha_fim=linha_fim,
        )

        if not validar_existencia:
            return RespostaNavegacao(link=link, validacao=validacao_nao_executada())

        validacao = self._executar_validacao(repositorio_n, arquivo_n, ref_n)
        return RespostaNavegacao(link=link, validacao=validacao)

    # ------------------------------------------------------------------
    # Validacao
    # ------------------------------------------------------------------

    def _executar_validacao(self, repo: str, arquivo: str, ref: str) -> ResultadoValidacao:
        if self._validador is None:
            return ResultadoValidacao(
                executada=True,
                existe=None,
                mensagem="Validacao nao foi executada porque nao ha integracao com GitHub configurada.",
            )
        try:
            existe = self._validador.existe(repo, arquivo, ref)
        except GitHubIndisponivelError as e:
            return ResultadoValidacao(
                executada=True,
                existe=None,
                mensagem=(
                    f"Nao conseguimos verificar se o arquivo existe agora "
                    f"({e}). O link foi gerado e pode estar correto — "
                    f"tente abri-lo no GitHub."
                ),
            )

        if existe:
            return ResultadoValidacao(executada=True, existe=True, mensagem=None)
        return ResultadoValidacao(
            executada=True,
            existe=False,
            mensagem=(
                f"Arquivo '{arquivo}' nao foi encontrado em '{repo}' no ref '{ref}'. "
                f"Verifique se o caminho esta correto ou se o arquivo existe nesse branch."
            ),
        )

    @staticmethod
    def _validar_repositorio(repo: str) -> str:
        if not repo or not repo.strip():
            raise NavegacaoInvalidaError("repositorio e obrigatorio.")
        normalizado = repo.strip()
        if not _REGEX_REPO.match(normalizado):
            raise NavegacaoInvalidaError(
                f"repositorio '{repo}' invalido. Use o formato 'owner/repo'."
            )
        return normalizado

    @staticmethod
    def _validar_arquivo(arquivo: str) -> str:
        if not arquivo or not arquivo.strip():
            raise NavegacaoInvalidaError("arquivo e obrigatorio.")
        normalizado = arquivo.strip().lstrip("/")
        if ".." in normalizado.split("/"):
            raise NavegacaoInvalidaError(
                f"arquivo '{arquivo}' contem '..' — nao eh permitido."
            )
        return normalizado

    @staticmethod
    def _validar_ref(ref: str) -> str:
        if not ref or not ref.strip():
            return "HEAD"
        return ref.strip()

    @staticmethod
    def _validar_linhas(linha: Optional[int], linha_fim: Optional[int]) -> None:
        if linha is not None and linha < 1:
            raise NavegacaoInvalidaError("linha deve ser >= 1.")
        if linha_fim is not None and linha_fim < 1:
            raise NavegacaoInvalidaError("linha_fim deve ser >= 1.")
        if linha_fim is not None and linha is None:
            raise NavegacaoInvalidaError("linha_fim exige que linha seja informada.")
        if linha is not None and linha_fim is not None and linha_fim < linha:
            raise NavegacaoInvalidaError("linha_fim nao pode ser menor que linha.")

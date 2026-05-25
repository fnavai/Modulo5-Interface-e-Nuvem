# Implementacao do RegraService (US IN-09).

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.application.ports.driven.notificador_comentario_pr import (
    NotificadorComentarioPR,
)
from app.application.ports.driven.repositorio_regras import RepositorioRegras
from app.application.ports.driving.regra_service import RegraService
from app.application.services.avaliador_regras import avaliar_regra
from app.domain.entidades.regra_arquitetural import (
    ORDEM_SEVERIDADE,
    RegraArquitetural,
    ResultadoAvaliacao,
    Severidade,
    TipoRegra,
    ViolacaoRegra,
)
from app.domain.excecoes import (
    ComentarioPRError,
    RegraInvalidaError,
    RegraNaoEncontradaError,
)


_logger = logging.getLogger("interface.regras")


_PARAMETROS_OBRIGATORIOS: Dict[TipoRegra, Tuple[str, ...]] = {
    TipoRegra.ARQUIVO_PROIBIDO: ("padrao_glob",),
    TipoRegra.LIMITE_ARQUIVOS: ("limite",),
    TipoRegra.PAR_OBRIGATORIO: ("padrao_origem", "padrao_par"),
    TipoRegra.PADRAO_BRANCH: ("regex",),
}


class RegraServiceImpl(RegraService):

    def __init__(
        self,
        repositorio: RepositorioRegras,
        notificador: NotificadorComentarioPR,
    ):
        self._repo = repositorio
        self._notificador = notificador

    def criar(self, nome, tipo, severidade, parametros, mensagem, criada_por) -> RegraArquitetural:
        self._validar_strings(nome=nome, criada_por=criada_por)
        self._validar_parametros(tipo, parametros or {})
        regra = RegraArquitetural(
            nome=nome.strip(),
            tipo=tipo,
            severidade=severidade,
            parametros=dict(parametros or {}),
            mensagem=(mensagem or "").strip(),
            criada_por=criada_por.strip(),
        )
        self._repo.salvar(regra)
        return regra

    def atualizar(
        self,
        regra_id: str,
        nome: Optional[str] = None,
        severidade: Optional[Severidade] = None,
        parametros: Optional[Dict[str, Any]] = None,
        mensagem: Optional[str] = None,
        ativa: Optional[bool] = None,
    ) -> RegraArquitetural:
        atual = self._exigir(regra_id)
        novos = {"atualizada_em": datetime.now(timezone.utc)}
        if nome is not None:
            if not nome.strip():
                raise RegraInvalidaError("nome nao pode ser vazio.")
            novos["nome"] = nome.strip()
        if severidade is not None:
            novos["severidade"] = severidade
        if parametros is not None:
            self._validar_parametros(atual.tipo, parametros)
            novos["parametros"] = dict(parametros)
        if mensagem is not None:
            novos["mensagem"] = mensagem.strip()
        if ativa is not None:
            novos["ativa"] = bool(ativa)
        atualizada = replace(atual, **novos)
        self._repo.salvar(atualizada)
        return atualizada

    def obter(self, regra_id: str) -> RegraArquitetural:
        return self._exigir(regra_id)

    def listar(self, ativa: Optional[bool] = None) -> List[RegraArquitetural]:
        return self._repo.listar(ativa=ativa)

    def remover(self, regra_id: str) -> bool:
        return self._repo.remover(regra_id)

    def avaliar(
        self,
        repositorio: str,
        branch_head: str,
        arquivos_modificados: Tuple[str, ...],
    ) -> ResultadoAvaliacao:
        self._validar_strings(repositorio=repositorio)
        regras = self._repo.listar(ativa=True)
        violacoes: List[ViolacaoRegra] = []
        for regra in regras:
            violacoes.extend(avaliar_regra(regra, branch_head or "", tuple(arquivos_modificados)))
        return ResultadoAvaliacao(
            repositorio=repositorio,
            branch_head=branch_head or "",
            arquivos_modificados=tuple(arquivos_modificados),
            regras_aplicadas=len(regras),
            violacoes=tuple(violacoes),
        )

    def avaliar_e_comentar(
        self,
        repositorio: str,
        pr_numero: int,
        branch_head: str,
        arquivos_modificados: Tuple[str, ...],
    ) -> Tuple[ResultadoAvaliacao, Optional[int]]:
        if pr_numero <= 0:
            raise RegraInvalidaError("pr_numero deve ser positivo.")
        resultado = self.avaliar(repositorio, branch_head, arquivos_modificados)
        if not resultado.tem_violacoes:
            return resultado, None
        mensagem = self._formatar_comentario(resultado)
        try:
            comentario_id = self._notificador.comentar(repositorio, pr_numero, mensagem)
        except ComentarioPRError as e:
            _logger.warning("Falha ao postar comentario de regras no PR %s: %s", pr_numero, e)
            comentario_id = None
        return resultado, comentario_id

    def _exigir(self, regra_id: str) -> RegraArquitetural:
        if not regra_id or not regra_id.strip():
            raise RegraNaoEncontradaError("regra_id obrigatorio.")
        r = self._repo.obter(regra_id.strip())
        if r is None:
            raise RegraNaoEncontradaError(f"Regra {regra_id} nao existe.")
        return r

    @staticmethod
    def _validar_strings(**campos: str) -> None:
        for nome, valor in campos.items():
            if not valor or not str(valor).strip():
                raise RegraInvalidaError(f"campo '{nome}' e obrigatorio.")

    @staticmethod
    def _validar_parametros(tipo: TipoRegra, parametros: Dict[str, Any]) -> None:
        obrigatorios = _PARAMETROS_OBRIGATORIOS.get(tipo, ())
        faltando = [p for p in obrigatorios if not parametros.get(p)]
        if faltando:
            raise RegraInvalidaError(
                f"parametros faltando para tipo '{tipo.value}': {', '.join(faltando)}"
            )

    @staticmethod
    def _formatar_comentario(resultado: ResultadoAvaliacao) -> str:
        emoji_por_severidade = {"info": "INFO", "warning": "WARN", "error": "ERROR"}
        linhas = ["## Alerta de Regras Arquiteturais (IN-09)", ""]
        linhas.append(f"Branch: `{resultado.branch_head}`  Arquivos: {len(resultado.arquivos_modificados)}")
        linhas.append("")
        linhas.append("### Resumo")
        for sev in reversed(ORDEM_SEVERIDADE):
            qtd = resultado.total_por_severidade[sev.value]
            if qtd > 0:
                linhas.append(f"- **{emoji_por_severidade[sev.value]}**: {qtd}")
        linhas.append("")
        linhas.append("### Violacoes")
        for v in resultado.violacoes:
            tag = emoji_por_severidade[v.severidade.value]
            linhas.append(f"- [**{tag}**] **{v.regra_nome}** — {v.mensagem}")
            if v.arquivos_envolvidos:
                arquivos = ", ".join(f"`{a}`" for a in v.arquivos_envolvidos[:5])
                resto = ""
                if len(v.arquivos_envolvidos) > 5:
                    resto = f" (+{len(v.arquivos_envolvidos) - 5})"
                linhas.append(f"  - Arquivos: {arquivos}{resto}")
        linhas.append("")
        linhas.append("---")
        linhas.append("*Avaliacao automatica do Interface-e-Nuvem. Severidade nao bloqueia merge — apenas sinaliza.*")
        return "\n".join(linhas)

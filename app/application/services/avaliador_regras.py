# Avaliadores deterministicos por tipo de regra (US IN-09).
# Cada classe sabe avaliar UM tipo de regra e devolver lista de violacoes.

import fnmatch
import re
from abc import ABC, abstractmethod
from typing import List, Tuple

from app.domain.entidades.regra_arquitetural import (
    RegraArquitetural,
    Severidade,
    TipoRegra,
    ViolacaoRegra,
)


class Avaliador(ABC):

    @abstractmethod
    def avaliar(
        self,
        regra: RegraArquitetural,
        branch_head: str,
        arquivos_modificados: Tuple[str, ...],
    ) -> List[ViolacaoRegra]:
        pass

    @staticmethod
    def _violar(regra: RegraArquitetural, mensagem: str, arquivos: Tuple[str, ...] = ()) -> ViolacaoRegra:
        msg = regra.mensagem.strip() or mensagem
        return ViolacaoRegra(
            regra_id=regra.id, regra_nome=regra.nome,
            tipo=regra.tipo, severidade=regra.severidade,
            mensagem=msg, arquivos_envolvidos=arquivos,
        )


class AvaliadorArquivoProibido(Avaliador):
    def avaliar(self, regra, branch_head, arquivos_modificados):
        padrao = regra.parametros.get("padrao_glob", "")
        if not padrao:
            return []
        casados = tuple(a for a in arquivos_modificados if fnmatch.fnmatch(a, padrao))
        if not casados:
            return []
        return [self._violar(
            regra,
            f"PR modifica arquivo(s) que casam com padrao proibido '{padrao}': {', '.join(casados)}",
            arquivos=casados,
        )]


class AvaliadorLimiteArquivos(Avaliador):
    def avaliar(self, regra, branch_head, arquivos_modificados):
        try:
            limite = int(regra.parametros.get("limite", 0))
        except (TypeError, ValueError):
            return []
        if limite <= 0 or len(arquivos_modificados) <= limite:
            return []
        return [self._violar(
            regra,
            f"PR modifica {len(arquivos_modificados)} arquivos (limite: {limite}). "
            f"Considere quebrar em PRs menores.",
        )]


class AvaliadorParObrigatorio(Avaliador):
    def avaliar(self, regra, branch_head, arquivos_modificados):
        padrao_origem = regra.parametros.get("padrao_origem", "")
        padrao_par = regra.parametros.get("padrao_par", "")
        if not padrao_origem or not padrao_par:
            return []
        modificados_origem = [a for a in arquivos_modificados if fnmatch.fnmatch(a, padrao_origem)]
        if not modificados_origem:
            return []
        # Existe pelo menos UM arquivo do padrao_par mexido?
        tem_par = any(fnmatch.fnmatch(a, padrao_par) for a in arquivos_modificados)
        if tem_par:
            return []
        return [self._violar(
            regra,
            f"PR mexe em '{padrao_origem}' ({len(modificados_origem)} arquivo(s)) mas nao "
            f"toca em nenhum '{padrao_par}'.",
            arquivos=tuple(modificados_origem),
        )]


class AvaliadorPadraoBranch(Avaliador):
    def avaliar(self, regra, branch_head, arquivos_modificados):
        regex = regra.parametros.get("regex", "")
        if not regex:
            return []
        try:
            if re.match(regex, branch_head or ""):
                return []
        except re.error:
            return []
        return [self._violar(
            regra,
            f"Branch '{branch_head}' nao casa com o padrao exigido: `{regex}`.",
        )]


_AVALIADORES = {
    TipoRegra.ARQUIVO_PROIBIDO: AvaliadorArquivoProibido(),
    TipoRegra.LIMITE_ARQUIVOS: AvaliadorLimiteArquivos(),
    TipoRegra.PAR_OBRIGATORIO: AvaliadorParObrigatorio(),
    TipoRegra.PADRAO_BRANCH: AvaliadorPadraoBranch(),
}


def avaliar_regra(
    regra: RegraArquitetural,
    branch_head: str,
    arquivos_modificados: Tuple[str, ...],
) -> List[ViolacaoRegra]:
    avaliador = _AVALIADORES.get(regra.tipo)
    if avaliador is None:
        return []
    return avaliador.avaliar(regra, branch_head, arquivos_modificados)

# Implementacao do ADRService (US IN-07).
# Maquina de estados:
#   RASCUNHO -> PROPOSTA, DESCARTADA
#   PROPOSTA -> ACEITA, DESCARTADA
#   ACEITA   -> DEPRECIADA, SUPERADA
#   (DESCARTADA/DEPRECIADA/SUPERADA sao terminais)

from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.application.ports.driven.repositorio_adrs import RepositorioADRs
from app.application.ports.driving.adr_service import ADRService
from app.domain.entidades.decisao_arquitetural import (
    ADR,
    StatusADR,
    TEMPLATE_ADR_PADRAO,
    VinculoComponenteADR,
)
from app.domain.excecoes import (
    ADRInvalidaError,
    ADRNaoEncontradaError,
    TransicaoStatusInvalidaError,
)


_TRANSICOES_PERMITIDAS = {
    StatusADR.RASCUNHO: {StatusADR.PROPOSTA, StatusADR.DESCARTADA},
    StatusADR.PROPOSTA: {StatusADR.ACEITA, StatusADR.DESCARTADA},
    StatusADR.ACEITA: {StatusADR.DEPRECIADA, StatusADR.SUPERADA},
    # Terminais: nada sai daqui
    StatusADR.DESCARTADA: set(),
    StatusADR.DEPRECIADA: set(),
    StatusADR.SUPERADA: set(),
}


class ADRServiceImpl(ADRService):

    def __init__(self, repositorio: RepositorioADRs):
        self._repo = repositorio

    # ------------------------------------------------------------------
    # Template
    # ------------------------------------------------------------------

    def template_padrao(self) -> Dict[str, str]:
        return dict(TEMPLATE_ADR_PADRAO)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def criar(self, titulo, contexto, decisao, consequencias, autor_id) -> ADR:
        self._exigir_strings(titulo=titulo, contexto=contexto, decisao=decisao,
                             consequencias=consequencias, autor_id=autor_id)
        adr = ADR(
            titulo=titulo.strip(),
            contexto=contexto,
            decisao=decisao,
            consequencias=consequencias,
            autor_id=autor_id.strip(),
        )
        self._repo.salvar(adr)
        return adr

    def atualizar(self, adr_id, autor_id, titulo=None, contexto=None, decisao=None, consequencias=None) -> ADR:
        adr = self._exigir_adr(adr_id)
        if adr.status != StatusADR.RASCUNHO:
            raise TransicaoStatusInvalidaError(
                f"ADR ja saiu de RASCUNHO (status={adr.status.value}); nao pode mais editar conteudo."
            )
        self._exigir_strings(autor_id=autor_id)
        novos = {
            "titulo": titulo.strip() if titulo is not None and titulo.strip() else adr.titulo,
            "contexto": contexto if contexto is not None else adr.contexto,
            "decisao": decisao if decisao is not None else adr.decisao,
            "consequencias": consequencias if consequencias is not None else adr.consequencias,
            "atualizada_em": datetime.now(timezone.utc),
        }
        atualizada = replace(adr, **novos)
        self._repo.salvar(atualizada)
        return atualizada

    # ------------------------------------------------------------------
    # Maquina de estados
    # ------------------------------------------------------------------

    def propor(self, adr_id, autor_id, documento_aprovacao_id=None) -> ADR:
        return self._transitar(
            adr_id, StatusADR.PROPOSTA,
            extras={"documento_aprovacao_id": documento_aprovacao_id} if documento_aprovacao_id else {},
        )

    def aceitar(self, adr_id, autor_id) -> ADR:
        return self._transitar(adr_id, StatusADR.ACEITA)

    def descartar(self, adr_id, autor_id, motivo) -> ADR:
        if not motivo or not motivo.strip():
            raise ADRInvalidaError("motivo do descarte e obrigatorio.")
        return self._transitar(adr_id, StatusADR.DESCARTADA, extras={"motivo_descarte": motivo.strip()})

    def deprecar(self, adr_id, autor_id, motivo) -> ADR:
        if not motivo or not motivo.strip():
            raise ADRInvalidaError("motivo da depreciacao e obrigatorio.")
        return self._transitar(adr_id, StatusADR.DEPRECIADA, extras={"motivo_descarte": motivo.strip()})

    def superar(self, adr_id, nova_adr_id, autor_id) -> ADR:
        if not nova_adr_id or not nova_adr_id.strip():
            raise ADRInvalidaError("nova_adr_id e obrigatorio.")
        nova = self._repo.obter(nova_adr_id.strip())
        if nova is None:
            raise ADRNaoEncontradaError(f"ADR substituta '{nova_adr_id}' nao existe.")
        return self._transitar(adr_id, StatusADR.SUPERADA, extras={"superada_por_id": nova.id})

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def obter(self, adr_id) -> ADR:
        return self._exigir_adr(adr_id)

    def listar(self, status=None, autor_id=None) -> List[ADR]:
        return self._repo.listar(status=status, autor_id=autor_id)

    # ------------------------------------------------------------------
    # Vinculos
    # ------------------------------------------------------------------

    def vincular_componente(self, adr_id, repositorio, modulo, descricao_componente) -> VinculoComponenteADR:
        self._exigir_adr(adr_id)  # garante que existe
        self._exigir_strings(repositorio=repositorio, modulo=modulo)
        vinculo = VinculoComponenteADR(
            adr_id=adr_id.strip(),
            repositorio=repositorio.strip(),
            modulo=modulo.strip(),
            descricao_componente=(descricao_componente or "").strip(),
        )
        self._repo.vincular(vinculo)
        return vinculo

    def desvincular_componente(self, adr_id, repositorio, modulo) -> bool:
        return self._repo.desvincular(adr_id, repositorio, modulo)

    def adrs_de_componente(self, repositorio, modulo) -> List[ADR]:
        return self._repo.listar_adrs_de_componente(repositorio, modulo)

    def marcadores_de_diagrama(self, repositorio, modulos) -> Dict[str, dict]:
        if not modulos:
            return {}
        contagens = self._repo.contar_adrs_por_modulo(repositorio, modulos)
        # Garantir que todos os modulos pedidos aparecem (mesmo zerados) — UI precisa.
        resultado = {}
        for m in modulos:
            por_status = contagens.get(m, {})
            total = sum(por_status.values())
            resultado[m] = {
                "total": total,
                "tem_adr": total > 0,
                "por_status": por_status,
            }
        return resultado

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _transitar(self, adr_id: str, novo_status: StatusADR, extras: Optional[dict] = None) -> ADR:
        adr = self._exigir_adr(adr_id)
        permitidos = _TRANSICOES_PERMITIDAS.get(adr.status, set())
        if novo_status not in permitidos:
            raise TransicaoStatusInvalidaError(
                f"Transicao {adr.status.value} -> {novo_status.value} nao permitida."
            )
        kwargs = {"status": novo_status, "atualizada_em": datetime.now(timezone.utc)}
        if extras:
            kwargs.update(extras)
        atualizada = replace(adr, **kwargs)
        self._repo.salvar(atualizada)
        return atualizada

    def _exigir_adr(self, adr_id: str) -> ADR:
        if not adr_id or not adr_id.strip():
            raise ADRNaoEncontradaError("adr_id obrigatorio.")
        adr = self._repo.obter(adr_id.strip())
        if adr is None:
            raise ADRNaoEncontradaError(f"ADR '{adr_id}' nao existe.")
        return adr

    @staticmethod
    def _exigir_strings(**campos) -> None:
        for nome, valor in campos.items():
            if not valor or not valor.strip():
                raise ADRInvalidaError(f"Campo '{nome}' e obrigatorio.")

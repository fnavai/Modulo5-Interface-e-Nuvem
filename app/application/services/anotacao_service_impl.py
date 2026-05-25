# Implementacao do AnotacaoService (US IN-03).

from dataclasses import replace
from datetime import datetime, timezone
from typing import List, Optional

from app.application.ports.driven.repositorio_anotacoes import RepositorioAnotacoes
from app.application.ports.driving.anotacao_service import AnotacaoService
from app.domain.entidades.anotacao import Anotacao
from app.domain.excecoes import (
    AnotacaoInvalidaError,
    AnotacaoNaoEncontradaError,
    PermissaoAnotacaoNegadaError,
)


class AnotacaoServiceImpl(AnotacaoService):

    def __init__(self, repositorio: RepositorioAnotacoes):
        self._repo = repositorio

    def criar(
        self,
        repositorio: str,
        modulo: str,
        componente: str,
        autor_id: str,
        conteudo: str,
        parent_id: Optional[str] = None,
    ) -> Anotacao:
        self._validar_strings(
            repositorio=repositorio, modulo=modulo, componente=componente,
            autor_id=autor_id, conteudo=conteudo,
        )
        if parent_id is not None:
            parent = self._repo.obter(parent_id)
            if parent is None:
                raise AnotacaoNaoEncontradaError(
                    f"Anotacao raiz {parent_id} nao existe."
                )
            if parent.parent_id is not None:
                raise AnotacaoInvalidaError(
                    "parent_id deve apontar para uma anotacao raiz, nao para resposta."
                )
        anotacao = Anotacao(
            repositorio=repositorio.strip(),
            modulo=modulo.strip(),
            componente=componente.strip(),
            autor_id=autor_id.strip(),
            conteudo=conteudo.strip(),
            parent_id=parent_id.strip() if parent_id else None,
        )
        self._repo.salvar(anotacao)
        return anotacao

    def atualizar(self, anotacao_id: str, autor_id: str, conteudo: str) -> Anotacao:
        atual = self._exigir(anotacao_id)
        if not autor_id or not autor_id.strip():
            raise AnotacaoInvalidaError("autor_id e obrigatorio.")
        if atual.autor_id != autor_id.strip():
            raise PermissaoAnotacaoNegadaError(
                f"Apenas '{atual.autor_id}' pode editar essa anotacao."
            )
        if not conteudo or not conteudo.strip():
            raise AnotacaoInvalidaError("conteudo nao pode ser vazio.")
        atualizado = replace(
            atual, conteudo=conteudo.strip(),
            atualizado_em=datetime.now(timezone.utc),
        )
        self._repo.salvar(atualizado)
        return atualizado

    def resolver(self, anotacao_id: str) -> Anotacao:
        atual = self._exigir(anotacao_id)
        if atual.resolvida:
            return atual
        atualizado = replace(
            atual, resolvida=True,
            atualizado_em=datetime.now(timezone.utc),
        )
        self._repo.salvar(atualizado)
        return atualizado

    def reabrir(self, anotacao_id: str) -> Anotacao:
        atual = self._exigir(anotacao_id)
        if not atual.resolvida:
            return atual
        atualizado = replace(
            atual, resolvida=False,
            atualizado_em=datetime.now(timezone.utc),
        )
        self._repo.salvar(atualizado)
        return atualizado

    def remover(self, anotacao_id: str, autor_id: str) -> bool:
        atual = self._repo.obter(anotacao_id)
        if atual is None:
            return False
        if atual.autor_id != (autor_id or "").strip():
            raise PermissaoAnotacaoNegadaError(
                f"Apenas '{atual.autor_id}' pode remover essa anotacao."
            )
        return self._repo.remover(anotacao_id)

    def obter(self, anotacao_id: str) -> Anotacao:
        return self._exigir(anotacao_id)

    def listar(
        self,
        repositorio: Optional[str] = None,
        modulo: Optional[str] = None,
        componente: Optional[str] = None,
        resolvida: Optional[bool] = None,
        autor_id: Optional[str] = None,
    ) -> List[Anotacao]:
        return self._repo.listar(
            repositorio=repositorio, modulo=modulo, componente=componente,
            resolvida=resolvida, autor_id=autor_id,
        )

    def listar_thread(self, parent_id: str) -> List[Anotacao]:
        return self._repo.listar_thread(parent_id)

    def listar_mencoes_de(self, usuario_id: str) -> List[Anotacao]:
        if not usuario_id or not usuario_id.strip():
            raise AnotacaoInvalidaError("usuario_id e obrigatorio.")
        return self._repo.listar_mencoes_de(usuario_id.strip())

    def _exigir(self, anotacao_id: str) -> Anotacao:
        if not anotacao_id or not anotacao_id.strip():
            raise AnotacaoNaoEncontradaError("anotacao_id obrigatorio.")
        a = self._repo.obter(anotacao_id.strip())
        if a is None:
            raise AnotacaoNaoEncontradaError(f"Anotacao {anotacao_id} nao existe.")
        return a

    @staticmethod
    def _validar_strings(**campos: str) -> None:
        for nome, valor in campos.items():
            if not valor or not valor.strip():
                raise AnotacaoInvalidaError(f"campo '{nome}' e obrigatorio.")

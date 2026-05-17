# Fakes dos clientes Gerador/Perfis para testes do fluxo unificado (BFF).
# Implementam os ports reais; permitem injetar sucesso ou simular falha.
# Nao sao usados em producao (composition_root usa os adapters HTTP).

from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.domain.excecoes import FalhaNaComunicacaoError


def _saude(nome: str) -> StatusServico:
    return StatusServico(
        nome=nome, estado=EstadoServico.DISPONIVEL, detalhes="fake."
    )


class ClienteGeradorFake(ClienteGerador):
    def __init__(self, diagrama=None, estrutura=None, falha=False):
        self._diagrama = diagrama
        self._estrutura = estrutura
        self._falha = falha

    def verificar_saude(self) -> StatusServico:
        return _saude("gerador_documentacao")

    def gerar_diagrama_branch(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        if self._falha:
            raise FalhaNaComunicacaoError("Gerador indisponivel (fake).")
        return {
            "diagrama_mermaid": self._diagrama,
            "estrutura": self._estrutura,
            "warnings": [],
        }


class ClientePerfisFake(ClientePerfis):
    def __init__(self, ownership=None, falha=False):
        self._ownership = ownership
        self._falha = falha

    def verificar_saude(self) -> StatusServico:
        return _saude("perfis_usuarios")

    def obter_ownership(self, owner: str, repo: str, modulo: str):
        if self._falha:
            raise FalhaNaComunicacaoError("Perfis indisponivel (fake).")
        return self._ownership

# Adaptador driven: cliente HTTP para o IA-Analise-Codigo

import requests

from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.config.settings import IA_ANALISE_URL, HTTP_TIMEOUT

# A analise de qualidade e AST (rapida), mas damos folga p/ import frio.
_QUALIDADE_TIMEOUT = max(HTTP_TIMEOUT, 15)


class AdaptadorClienteIA(ClienteIAAnalise):

    def verificar_saude(self) -> StatusServico:
        try:
            resposta = requests.get(
                f"{IA_ANALISE_URL}/saude/ia", # refactor: veio do desenvolvimento do Fê.
                timeout=HTTP_TIMEOUT
            )
            if resposta.status_code == 200:
                return StatusServico(
                    nome="ia_analise_codigo",
                    estado=EstadoServico.DISPONIVEL,
                    detalhes="Respondendo normalmente."
                )
            return StatusServico(
                nome="ia_analise_codigo",
                estado=EstadoServico.DEGRADADO,
                detalhes=f"Status inesperado: {resposta.status_code}"
            )
        except requests.exceptions.Timeout:
            return StatusServico(
                nome="ia_analise_codigo",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Timeout ao conectar."
            )
        except requests.exceptions.ConnectionError:
            return StatusServico(
                nome="ia_analise_codigo",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Servico inacessivel."
            )

    def analisar_qualidade(self, codigo: str) -> "dict | None":
        # Best-effort: POST /qualidade/analisar {"codigo": ...} -> dict
        # (acoplamento/ciclos/severidade). Qualquer falha -> None, para
        # nao derrubar o fluxo unificado (a qualidade e opcional).
        if not codigo or not codigo.strip():
            return None
        try:
            resposta = requests.post(
                f"{IA_ANALISE_URL}/qualidade/analisar",
                json={"codigo": codigo},
                timeout=_QUALIDADE_TIMEOUT,
            )
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError):
            return None
        if resposta.status_code != 200:
            return None
        try:
            dados = resposta.json()
        except ValueError:
            return None
        return dados if isinstance(dados, dict) else {"resultado": dados}
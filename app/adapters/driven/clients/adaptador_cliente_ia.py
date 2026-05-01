# Adaptador driven: cliente HTTP para o IA-Analise-Codigo

import requests

from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.config.settings import IA_ANALISE_URL, HTTP_TIMEOUT


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
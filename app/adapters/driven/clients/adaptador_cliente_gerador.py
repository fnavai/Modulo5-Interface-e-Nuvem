# Adaptador driven: cliente HTTP para o Gerador-Documentacao

import requests

from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.config.settings import GERADOR_URL, HTTP_TIMEOUT


class AdaptadorClienteGerador(ClienteGerador):

    def verificar_saude(self) -> StatusServico:
        try:
            resposta = requests.get(
                f"{GERADOR_URL}/health/ready",
                timeout=HTTP_TIMEOUT
            )
            if resposta.status_code == 200:
                return StatusServico(
                    nome="gerador_documentacao",
                    estado=EstadoServico.DISPONIVEL,
                    detalhes="Respondendo normalmente."
                )
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.DEGRADADO,
                detalhes=f"Status inesperado: {resposta.status_code}"
            )
        except requests.exceptions.Timeout:
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Timeout ao conectar."
            )
        except requests.exceptions.ConnectionError:
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Servico inacessivel."
            )
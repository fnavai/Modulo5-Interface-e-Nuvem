# Adaptador driven: cliente HTTP para o Perfis-Usuarios
# Responsabilidade: implementar ClientePerfis chamando o servico real via HTTP.

import requests

from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.config.settings import PERFIS_URL, HTTP_TIMEOUT


class AdaptadorClientePerfis(ClientePerfis):

    def verificar_saude(self) -> StatusServico:
        try:
            resposta = requests.get(
                f"{PERFIS_URL}/health/ready",
                timeout=HTTP_TIMEOUT
            )
            if resposta.status_code == 200:
                return StatusServico(
                    nome="perfis_usuarios",
                    estado=EstadoServico.DISPONIVEL,
                    detalhes="Respondendo normalmente."
                )
            return StatusServico(
                nome="perfis_usuarios",
                estado=EstadoServico.DEGRADADO,
                detalhes=f"Status inesperado: {resposta.status_code}"
            )
        except requests.exceptions.Timeout:
            return StatusServico(
                nome="perfis_usuarios",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Timeout ao conectar."
            )
        except requests.exceptions.ConnectionError:
            return StatusServico(
                nome="perfis_usuarios",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Servico inacessivel."
            )
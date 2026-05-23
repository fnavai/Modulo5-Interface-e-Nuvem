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

    def obter_ownership(self, owner: str, repo: str, modulo: str):
        # Best-effort: qualquer falha (503 "nao encontrado", timeout, conexao,
        # status inesperado) vira None — nao derruba o fluxo unificado.
        try:
            resposta = requests.get(
                f"{PERFIS_URL}/api/ownership",
                params={"repositorio": f"{owner}/{repo}", "modulo": modulo},
                timeout=HTTP_TIMEOUT,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None
        if resposta.status_code != 200:
            return None
        try:
            return resposta.json()
        except ValueError:
            return None

    def obter_diagrama_perfis(self):
        # Best-effort: qualquer falha vira None.
        try:
            resposta = requests.get(
                f"{PERFIS_URL}/api/perfis/diagrama",
                timeout=HTTP_TIMEOUT,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None
        if resposta.status_code != 200:
            return None
        try:
            return resposta.json()
        except ValueError:
            return None
# Implementação do SaudeService
# Responsabilidade: agregar status dos 3 serviços e expor health check do portal.

from datetime import datetime, timezone
from typing import Dict

from app.application.ports.driving.saude_service import SaudeService
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.domain.entidades.status_servico import EstadoServico

VERSAO = "1.0.0"


class SaudeServiceImpl(SaudeService):

    def __init__(
        self,
        cliente_perfis: ClientePerfis,
        cliente_ia: ClienteIAAnalise,
        cliente_gerador: ClienteGerador
    ):
        self._cliente_perfis = cliente_perfis
        self._cliente_ia = cliente_ia
        self._cliente_gerador = cliente_gerador

    def verificar_liveness(self) -> Dict:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "versao": VERSAO
        }

    def verificar_readiness(self) -> Dict:
        status_perfis = self._cliente_perfis.verificar_saude()
        status_ia = self._cliente_ia.verificar_saude()
        status_gerador = self._cliente_gerador.verificar_saude()

        todos_disponiveis = all([
            status_perfis.esta_disponivel(),
            status_ia.esta_disponivel(),
            status_gerador.esta_disponivel()
        ])

        estado_geral = "ok" if todos_disponiveis else "degradado"

        return {
            "status": estado_geral,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "versao": VERSAO,
            "servicos": {
                "perfis_usuarios": {
                    "estado": status_perfis.estado.value,
                    "detalhes": status_perfis.detalhes
                },
                "ia_analise_codigo": {
                    "estado": status_ia.estado.value,
                    "detalhes": status_ia.detalhes
                },
                "gerador_documentacao": {
                    "estado": status_gerador.estado.value,
                    "detalhes": status_gerador.detalhes
                }
            }
        }
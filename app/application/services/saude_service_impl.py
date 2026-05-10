# Implementação do SaudeService
# Responsabilidade: agregar status dos 3 serviços e expor health check do portal,
# usando cache de ultimo estado conhecido como fallback quando algum cair.

from datetime import datetime, timezone
from typing import Dict, Optional

from app.application.ports.driving.saude_service import SaudeService
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cache_saude import CacheSaude
from app.domain.entidades.status_servico import StatusServico, EstadoServico

VERSAO = "1.0.0"


class SaudeServiceImpl(SaudeService):

    def __init__(
        self,
        cliente_perfis: ClientePerfis,
        cliente_ia: ClienteIAAnalise,
        cliente_gerador: ClienteGerador,
        cache: Optional[CacheSaude] = None,
    ):
        self._cliente_perfis = cliente_perfis
        self._cliente_ia = cliente_ia
        self._cliente_gerador = cliente_gerador
        self._cache = cache

    def verificar_liveness(self) -> Dict:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "versao": VERSAO
        }

    def verificar_readiness(self) -> Dict:
        status_perfis = self._consultar_com_fallback(self._cliente_perfis.verificar_saude)
        status_ia = self._consultar_com_fallback(self._cliente_ia.verificar_saude)
        status_gerador = self._consultar_com_fallback(self._cliente_gerador.verificar_saude)

        servicos = [status_perfis, status_ia, status_gerador]

        todos_disponiveis = all(s.esta_disponivel() for s in servicos)
        algum_do_cache = any(s.veio_do_cache() for s in servicos)

        if todos_disponiveis and not algum_do_cache:
            estado_geral = "ok"
        elif todos_disponiveis and algum_do_cache:
            # Tudo disponivel mas algum dado eh stale — sinaliza fallback.
            estado_geral = "fallback"
        else:
            estado_geral = "degradado"

        return {
            "status": estado_geral,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "versao": VERSAO,
            "servicos": {
                "perfis_usuarios": self._serializar(status_perfis),
                "ia_analise_codigo": self._serializar(status_ia),
                "gerador_documentacao": self._serializar(status_gerador),
            }
        }

    def _consultar_com_fallback(self, consultar) -> StatusServico:
        """
        Chama o cliente; se a resposta vier viva, atualiza o cache.
        Se vier INDISPONIVEL e houver cache valido, devolve a versao do cache
        (marcada como origem='cache' + stale_segundos).
        """
        atual = consultar()

        if atual.estado == EstadoServico.INDISPONIVEL and self._cache is not None:
            cacheado = self._cache.obter(atual.nome)
            if cacheado is not None:
                # Anexamos o motivo da falha original aos detalhes do cache,
                # para o operador entender por que voltou stale.
                cacheado.detalhes = (
                    f"{cacheado.detalhes} (servindo do cache; falha atual: {atual.detalhes})"
                )
                return cacheado
            return atual

        if self._cache is not None and atual.estado != EstadoServico.INDISPONIVEL:
            self._cache.salvar(atual)
        return atual

    @staticmethod
    def _serializar(status: StatusServico) -> Dict:
        return {
            "estado": status.estado.value,
            "detalhes": status.detalhes,
            "origem": status.origem,
            "stale_segundos": status.stale_segundos,
        }

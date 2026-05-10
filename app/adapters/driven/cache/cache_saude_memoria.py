# Adaptador driven: cache em memoria do ultimo estado conhecido de cada servico.
# Implementacao simples por dicionario com TTL — suficiente para o portal,
# que tem 1 unica instancia. Se virarmos multi-instancia, trocar por Redis.

from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from app.application.ports.driven.cache_saude import CacheSaude
from app.domain.entidades.status_servico import StatusServico


class CacheSaudeMemoria(CacheSaude):

    def __init__(self, ttl_segundos: int):
        if ttl_segundos <= 0:
            raise ValueError("ttl_segundos deve ser positivo.")
        self._ttl = ttl_segundos
        # nome_servico -> (status_capturado, timestamp_utc)
        self._entradas: Dict[str, Tuple[StatusServico, datetime]] = {}

    def salvar(self, status: StatusServico) -> None:
        # So armazenamos respostas vivas — cache de cache nao faz sentido.
        if status.origem != "live":
            return
        # Normaliza para garantir que o que sai do cache nao carrega stale_segundos antigo.
        snapshot = replace(status, stale_segundos=None)
        self._entradas[status.nome] = (snapshot, datetime.now(timezone.utc))

    def obter(self, nome_servico: str) -> Optional[StatusServico]:
        entrada = self._entradas.get(nome_servico)
        if entrada is None:
            return None

        snapshot, capturado_em = entrada
        idade = (datetime.now(timezone.utc) - capturado_em).total_seconds()
        if idade > self._ttl:
            # Expirou — remove para nao crescer indefinidamente.
            self._entradas.pop(nome_servico, None)
            return None

        return replace(snapshot, origem="cache", stale_segundos=int(idade))

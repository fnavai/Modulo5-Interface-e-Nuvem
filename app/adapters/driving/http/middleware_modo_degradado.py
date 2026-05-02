
import time
from typing import Optional
from flask import Flask, request, jsonify

from app.application.ports.driving.saude_service import SaudeService

METODOS_DE_ESCRITA = {"POST", "PUT", "PATCH", "DELETE"}
ROTAS_LIVRES = ("/health",)  # endpoints de saude nunca bloqueiam
TTL_CACHE_SEGUNDOS = 5


class _CacheEstado:
    def init(self) -> None:
        self._ultimo_check: float = 0.0
        self._ultimo_resultado: Optional[dict] = None

    def obter(self, saude_service: SaudeService) -> dict:
        agora = time.monotonic()
        if self._ultimo_resultado is None or (agora - self._ultimo_check) > TTL_CACHE_SEGUNDOS:
            self._ultimo_resultado = saude_service.verificar_readiness()
            self._ultimo_check = agora
        return self._ultimo_resultado


def registrar_modo_degradado(app: Flask, saude_service: SaudeService) -> None:
    cache = _CacheEstado()

    @app.before_request
    def bloquear_escritas_se_degradado():
        if request.method not in METODOS_DE_ESCRITA:
            return None
        if any(request.path.startswith(p) for p in ROTAS_LIVRES):
            return None

        estado = cache.obter(saude_service)
        if estado["status"] == "ok":
            return None

        servicos_fora = [
            nome for nome, info in estado["servicos"].items()
            if info["estado"] != "disponivel"
        ]
        return jsonify({
            "erro": "modo_degradado",
            "mensagem": (
                "O portal está em modo somente-leitura. "
                "Operações de escrita estão temporariamente desabilitadas."
            ),
            "servicos_indisponiveis": servicos_fora,
            "tente_novamente_em_segundos": TTL_CACHE_SEGUNDOS,
        }), 503
# Adaptador driving: rotas HTTP de health check agregado
# Responsabilidade: expor liveness e readiness do portal.

from flask import Blueprint, jsonify

from app.application.ports.driving.saude_service import SaudeService

saude_bp = Blueprint("saude", __name__, url_prefix="")


def criar_saude_routes(saude_service: SaudeService) -> Blueprint:

    @saude_bp.get("/health")
    def liveness():
        resultado = saude_service.verificar_liveness()
        return jsonify(resultado), 200

    @saude_bp.get("/health/ready")
    def readiness():
        resultado = saude_service.verificar_readiness()
        # ok        -> 200 (todos vivos, sem cache)
        # fallback  -> 200 (todos respondendo, mas algum servido do cache)
        # degradado -> 207 (algum fora; portal segue operando parcialmente)
        status_http = 200 if resultado["status"] in ("ok", "fallback") else 207
        return jsonify(resultado), status_http

    return saude_bp

# Nota sobre o status 207: quando o portal está no ar mas algum serviço dependente está degradado, retornamos 207 (Multi-Status) em vez de 503.
# Isso porque o portal continua funcionando — só parcialmente. 503 implicaria que o portal inteiro está fora, o que não é verdade.
# O status "fallback" continua sendo 200 porque a resposta ainda é util — apenas vinda de cache.

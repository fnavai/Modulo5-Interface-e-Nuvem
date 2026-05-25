# Adaptador driving: rotas HTTP de health check agregado
# Responsabilidade: expor liveness e readiness do portal.

from flask import Blueprint, jsonify

from app.application.ports.driving.saude_service import SaudeService


def criar_saude_routes(saude_service: SaudeService) -> Blueprint:
    # Blueprint criado dentro da factory pra suportar create_app() multiplas vezes.
    bp = Blueprint("saude", __name__, url_prefix="")

    @bp.get("/health")
    def liveness():
        resultado = saude_service.verificar_liveness()
        return jsonify(resultado), 200

    @bp.get("/health/ready")
    def readiness():
        resultado = saude_service.verificar_readiness()
        # ok        -> 200 (todos vivos, sem cache)
        # fallback  -> 200 (todos respondendo, mas algum servido do cache)
        # degradado -> 207 (algum fora; portal segue operando parcialmente)
        status_http = 200 if resultado["status"] in ("ok", "fallback") else 207
        return jsonify(resultado), status_http

    return bp

# Nota sobre o status 207: quando o portal esta no ar mas algum servico dependente esta degradado,
# retornamos 207 (Multi-Status) em vez de 503. Isso porque o portal continua funcionando —
# so parcialmente. 503 implicaria que o portal inteiro esta fora, o que nao e verdade.
# O status "fallback" continua sendo 200 porque a resposta ainda e util — apenas vinda de cache.

# Composition Root do Interface-e-Nuvem
# Responsabilidade: único lugar que conhece implementações concretas.

from flask import Flask

from app.adapters.driven.clients.adaptador_cliente_perfis import AdaptadorClientePerfis
from app.adapters.driven.clients.adaptador_cliente_ia import AdaptadorClienteIA
from app.adapters.driven.clients.adaptador_cliente_gerador import AdaptadorClienteGerador
from app.adapters.driven.cache.cache_saude_memoria import CacheSaudeMemoria
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driving.http.saude_routes import criar_saude_routes
from app.config.settings import CACHE_SAUDE_TTL_SEGUNDOS


def create_app() -> Flask:
    app = Flask(__name__)

    # Adaptadores driven
    cliente_perfis = AdaptadorClientePerfis()
    cliente_ia = AdaptadorClienteIA()
    cliente_gerador = AdaptadorClienteGerador()

    # Cache de saude para fallback degradado (None desliga o fallback)
    cache_saude = CacheSaudeMemoria(CACHE_SAUDE_TTL_SEGUNDOS) if CACHE_SAUDE_TTL_SEGUNDOS > 0 else None

    # Services
    saude_service = SaudeServiceImpl(cliente_perfis, cliente_ia, cliente_gerador, cache=cache_saude)

    # Rotas
    app.register_blueprint(criar_saude_routes(saude_service))

    return app

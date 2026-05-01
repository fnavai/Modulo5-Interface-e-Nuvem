# Composition Root do Interface-e-Nuvem
# Responsabilidade: único lugar que conhece implementações concretas.

from flask import Flask

from app.adapters.driven.clients.adaptador_cliente_perfis import AdaptadorClientePerfis
from app.adapters.driven.clients.adaptador_cliente_ia import AdaptadorClienteIA
from app.adapters.driven.clients.adaptador_cliente_gerador import AdaptadorClienteGerador
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driving.http.saude_routes import criar_saude_routes


def create_app() -> Flask:
    app = Flask(__name__)

    # Adaptadores driven
    cliente_perfis = AdaptadorClientePerfis()
    cliente_ia = AdaptadorClienteIA()
    cliente_gerador = AdaptadorClienteGerador()

    # Services
    saude_service = SaudeServiceImpl(cliente_perfis, cliente_ia, cliente_gerador)

    # Rotas
    app.register_blueprint(criar_saude_routes(saude_service))

    return app
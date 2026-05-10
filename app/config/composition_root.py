# Composition Root do Interface-e-Nuvem
# Responsabilidade: único lugar que conhece implementações concretas.

from flask import Flask

from app.adapters.driven.clients.adaptador_cliente_perfis import AdaptadorClientePerfis
from app.adapters.driven.clients.adaptador_cliente_ia import AdaptadorClienteIA
from app.adapters.driven.clients.adaptador_cliente_gerador import AdaptadorClienteGerador
from app.adapters.driven.clients.validador_arquivo_github_http import (
    ValidadorArquivoGitHubHTTP,
)
from app.adapters.driven.clients.validador_arquivo_github_fake import (
    ValidadorArquivoGitHubFake,
)
from app.adapters.driven.cache.cache_saude_memoria import CacheSaudeMemoria
from app.adapters.driven.persistence.repositorio_adrs_sqlite import RepositorioADRsSQLite
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.application.services.navegacao_service_impl import NavegacaoServiceImpl
from app.application.services.adr_service_impl import ADRServiceImpl
from app.adapters.driving.http.saude_routes import criar_saude_routes
from app.adapters.driving.http.navegacao_routes import criar_navegacao_routes
from app.adapters.driving.http.adr_routes import criar_adr_routes
from app.config.settings import (
    ADRS_SQLITE_PATH,
    CACHE_SAUDE_TTL_SEGUNDOS,
    GITHUB_BASE_URL,
    GITHUB_TIMEOUT_SEGUNDOS,
    GITHUB_TOKEN,
    VALIDADOR_GITHUB,
)


def _criar_validador_github():
    tipo = (VALIDADOR_GITHUB or "http").lower()
    if tipo == "fake":
        return ValidadorArquivoGitHubFake()
    if tipo == "http":
        return ValidadorArquivoGitHubHTTP(
            base_url=GITHUB_BASE_URL,
            token=GITHUB_TOKEN or None,
            timeout_segundos=GITHUB_TIMEOUT_SEGUNDOS,
        )
    raise ValueError(f"VALIDADOR_GITHUB desconhecido: {tipo}")


def create_app() -> Flask:
    app = Flask(__name__)

    # Adaptadores driven
    cliente_perfis = AdaptadorClientePerfis()
    cliente_ia = AdaptadorClienteIA()
    cliente_gerador = AdaptadorClienteGerador()
    validador_github = _criar_validador_github()
    repositorio_adrs = RepositorioADRsSQLite(ADRS_SQLITE_PATH)

    cache_saude = CacheSaudeMemoria(CACHE_SAUDE_TTL_SEGUNDOS) if CACHE_SAUDE_TTL_SEGUNDOS > 0 else None

    # Services
    saude_service = SaudeServiceImpl(cliente_perfis, cliente_ia, cliente_gerador, cache=cache_saude)
    navegacao_service = NavegacaoServiceImpl(validador=validador_github)
    adr_service = ADRServiceImpl(repositorio=repositorio_adrs)

    # Rotas
    app.register_blueprint(criar_saude_routes(saude_service))
    app.register_blueprint(criar_navegacao_routes(navegacao_service))
    app.register_blueprint(criar_adr_routes(adr_service))

    # Disponibiliza para testes (substituicao de adapters).
    app.config["validador_github"] = validador_github
    app.config["navegacao_service"] = navegacao_service
    app.config["adr_service"] = adr_service
    app.config["repositorio_adrs"] = repositorio_adrs

    return app

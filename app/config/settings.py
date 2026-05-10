# Configuracoes do Interface-e-Nuvem
# Responsabilidade: centralizar variáveis de ambiente.

import os

# Flask
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = FLASK_ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-trocar-em-producao")

# URLs dos servicos do módulo 5 - Localmente cada serviço roda numa porta diferente
PERFIS_URL = os.getenv("PERFIS_URL", "http://localhost:5002")
IA_ANALISE_URL = os.getenv("IA_ANALISE_URL", "http://localhost:5001")
GERADOR_URL = os.getenv("GERADOR_URL", "http://localhost:5003")

# Timeout padrão para chamadas HTTP entre servicos (segundos)
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "5"))

# Cache de saude: por quanto tempo (em segundos) servimos o ultimo estado conhecido
# de um servico que ficou indisponivel. Se 0, fallback fica desligado.
CACHE_SAUDE_TTL_SEGUNDOS = int(os.getenv("CACHE_SAUDE_TTL_SEGUNDOS", "300"))

# GitHub para validar caminhos de arquivos clicados nos diagramas (US IN-01).
GITHUB_BASE_URL = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # opcional — sem token bate em rate-limit anonimo
GITHUB_TIMEOUT_SEGUNDOS = float(os.getenv("GITHUB_TIMEOUT_SEGUNDOS", "5.0"))
# "http" = usa Contents API real; "fake" = adapter local (dev offline e testes).
VALIDADOR_GITHUB = os.getenv("VALIDADOR_GITHUB", "http")

# Persistencia das ADRs e vinculos com componentes (US IN-07).
ADRS_SQLITE_PATH = os.getenv("ADRS_SQLITE_PATH", "interface_adrs.db")
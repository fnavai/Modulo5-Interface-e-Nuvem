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
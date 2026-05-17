# Regressão do bug de integração: defaults de porta errados no settings.py
# (IA apontava :5001 e Gerador :5003, mas os serviços reais sobem em :8001 e :8000).

import importlib


def test_defaults_de_porta_corretos(monkeypatch):
    for var in ("IA_ANALISE_URL", "GERADOR_URL", "PERFIS_URL"):
        monkeypatch.delenv(var, raising=False)

    import app.config.settings as settings
    importlib.reload(settings)

    assert settings.IA_ANALISE_URL == "http://localhost:8001"
    assert settings.GERADOR_URL == "http://localhost:8000"
    assert settings.PERFIS_URL == "http://localhost:5002"


def test_env_var_ainda_sobrepoe_o_default(monkeypatch):
    monkeypatch.setenv("IA_ANALISE_URL", "http://ia.interno:9999")

    import app.config.settings as settings
    importlib.reload(settings)

    assert settings.IA_ANALISE_URL == "http://ia.interno:9999"

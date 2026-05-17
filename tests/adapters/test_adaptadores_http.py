# Testes dos adapters HTTP reais (Gerador obrigatorio; Perfis best-effort).
# HTTP mockado via monkeypatch de requests.post/get.

import pytest
import requests

from app.adapters.driven.clients.adaptador_cliente_gerador import (
    AdaptadorClienteGerador,
)
from app.adapters.driven.clients.adaptador_cliente_perfis import (
    AdaptadorClientePerfis,
)
from app.domain.excecoes import (
    FalhaNaComunicacaoError,
    ServicoIndisponivelError,
)


class _Resp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("sem json")
        return self._payload


# ---- Gerador.gerar_diagrama_branch ----

def test_gerador_sucesso_normaliza_mermaid_e_estrutura(monkeypatch):
    capturado = {}

    def fake_post(url, json=None, timeout=None):
        capturado["url"] = url
        capturado["json"] = json
        capturado["timeout"] = timeout
        return _Resp(
            200,
            {
                "mermaid": "classDiagram\n  class A",
                "estrutura": {"linguagem": "python", "componentes": []},
                "warnings": ["w1"],
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)
    out = AdaptadorClienteGerador().gerar_diagrama_branch(
        "fnavai", "Modulo5-Interface-e-Nuvem", "develop", "app/main.py"
    )
    assert out == {
        "diagrama_mermaid": "classDiagram\n  class A",
        "estrutura": {"linguagem": "python", "componentes": []},
        "warnings": ["w1"],
    }
    assert capturado["url"].endswith("/diagrama/branch")
    assert capturado["json"] == {
        "repositorio": "fnavai/Modulo5-Interface-e-Nuvem",
        "branch": "develop",
        "arquivo": "app/main.py",
        "formato": "mermaid",
    }
    assert capturado["timeout"] >= 20  # generoso p/ pipeline GitHub+IA


def test_gerador_502_levanta_falha(monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _Resp(502, {"detail": "IA-Analise: fora"})
    )
    with pytest.raises(FalhaNaComunicacaoError):
        AdaptadorClienteGerador().gerar_diagrama_branch("o", "r", "develop", "a.py")


def test_gerador_connection_error_levanta_indisponivel(monkeypatch):
    def boom(*a, **k):
        raise requests.exceptions.ConnectionError("recusou")

    monkeypatch.setattr(requests, "post", boom)
    with pytest.raises(ServicoIndisponivelError):
        AdaptadorClienteGerador().gerar_diagrama_branch("o", "r", "develop", "a.py")


# ---- Perfis.obter_ownership (best-effort) ----

def test_perfis_sucesso_devolve_dict(monkeypatch):
    capturado = {}

    def fake_get(url, params=None, timeout=None):
        capturado["url"] = url
        capturado["params"] = params
        return _Resp(200, {"ownership": {"owner_id": "joao"}, "origem": "github_vivo"})

    monkeypatch.setattr(requests, "get", fake_get)
    out = AdaptadorClientePerfis().obter_ownership("o", "r", "app/x.py")
    assert out == {"ownership": {"owner_id": "joao"}, "origem": "github_vivo"}
    assert capturado["url"].endswith("/api/ownership")
    assert capturado["params"] == {"repositorio": "o/r", "modulo": "app/x.py"}


def test_perfis_503_devolve_none(monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _Resp(503, {"detail": {"mensagem": "nao achou"}})
    )
    assert AdaptadorClientePerfis().obter_ownership("o", "r", "x.py") is None


def test_perfis_connection_error_devolve_none(monkeypatch):
    def boom(*a, **k):
        raise requests.exceptions.ConnectionError("recusou")

    monkeypatch.setattr(requests, "get", boom)
    assert AdaptadorClientePerfis().obter_ownership("o", "r", "x.py") is None

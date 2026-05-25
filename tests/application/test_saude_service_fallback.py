# Testes do fallback degradado do SaudeServiceImpl (US IN-11).
# Cobrem: cache populado em sucesso, servido em falha, ausente/expirado nao serve.

from app.application.services.saude_service_impl import SaudeServiceImpl
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.adapters.driven.cache.cache_saude_memoria import CacheSaudeMemoria
from app.domain.entidades.status_servico import StatusServico, EstadoServico


def _ok(nome):
    return StatusServico(nome=nome, estado=EstadoServico.DISPONIVEL, detalhes="ok")


def _fora(nome):
    return StatusServico(nome=nome, estado=EstadoServico.INDISPONIVEL, detalhes="connection refused")


class _Cliente(ClientePerfis, ClienteIAAnalise, ClienteGerador):
    """Cliente programavel — devolve o que estiver na fila de respostas."""
    def __init__(self, nome, respostas):
        self._nome = nome
        self._respostas = list(respostas)

    def verificar_saude(self) -> StatusServico:
        if not self._respostas:
            raise AssertionError(f"Cliente {self._nome} chamado mais vezes que o esperado.")
        return self._respostas.pop(0)

    # Metodos do contrato estendido dos ports — nao exercitados por estes
    # testes de saude/fallback; presentes apenas para o double ser concreto.
    def gerar_diagrama_branch(self, owner, repo, branch, caminho) -> dict:
        return {}

    def obter_ownership(self, owner, repo, modulo):
        return None


def test_primeira_chamada_sucesso_popula_cache_e_status_ok():
    perfis = _Cliente("perfis_usuarios", [_ok("perfis_usuarios")])
    ia = _Cliente("ia_analise_codigo", [_ok("ia_analise_codigo")])
    gerador = _Cliente("gerador_documentacao", [_ok("gerador_documentacao")])
    cache = CacheSaudeMemoria(ttl_segundos=60)

    service = SaudeServiceImpl(perfis, ia, gerador, cache=cache)
    resultado = service.verificar_readiness()

    assert resultado["status"] == "ok"
    for chave in ("perfis_usuarios", "ia_analise_codigo", "gerador_documentacao"):
        assert resultado["servicos"][chave]["origem"] == "live"
        assert resultado["servicos"][chave]["stale_segundos"] is None


def test_falha_apos_sucesso_serve_do_cache_com_status_fallback():
    perfis = _Cliente("perfis_usuarios", [_ok("perfis_usuarios"), _fora("perfis_usuarios")])
    ia = _Cliente("ia_analise_codigo", [_ok("ia_analise_codigo"), _ok("ia_analise_codigo")])
    gerador = _Cliente("gerador_documentacao", [_ok("gerador_documentacao"), _ok("gerador_documentacao")])
    cache = CacheSaudeMemoria(ttl_segundos=60)

    service = SaudeServiceImpl(perfis, ia, gerador, cache=cache)
    service.verificar_readiness()  # popula cache
    resultado = service.verificar_readiness()  # perfis cai

    assert resultado["status"] == "fallback"
    perfis_resp = resultado["servicos"]["perfis_usuarios"]
    assert perfis_resp["estado"] == "disponivel"
    assert perfis_resp["origem"] == "cache"
    assert perfis_resp["stale_segundos"] is not None
    assert perfis_resp["stale_segundos"] >= 0
    assert "servindo do cache" in perfis_resp["detalhes"]


def test_falha_sem_cache_previo_devolve_indisponivel():
    perfis = _Cliente("perfis_usuarios", [_fora("perfis_usuarios")])
    ia = _Cliente("ia_analise_codigo", [_ok("ia_analise_codigo")])
    gerador = _Cliente("gerador_documentacao", [_ok("gerador_documentacao")])
    cache = CacheSaudeMemoria(ttl_segundos=60)

    service = SaudeServiceImpl(perfis, ia, gerador, cache=cache)
    resultado = service.verificar_readiness()

    assert resultado["status"] == "degradado"
    assert resultado["servicos"]["perfis_usuarios"]["estado"] == "indisponivel"
    assert resultado["servicos"]["perfis_usuarios"]["origem"] == "live"


def test_cache_expirado_nao_eh_servido():
    perfis = _Cliente("perfis_usuarios", [_ok("perfis_usuarios"), _fora("perfis_usuarios")])
    ia = _Cliente("ia_analise_codigo", [_ok("ia_analise_codigo"), _ok("ia_analise_codigo")])
    gerador = _Cliente("gerador_documentacao", [_ok("gerador_documentacao"), _ok("gerador_documentacao")])
    cache = CacheSaudeMemoria(ttl_segundos=60)

    service = SaudeServiceImpl(perfis, ia, gerador, cache=cache)
    service.verificar_readiness()

    # Forca expiracao manipulando o timestamp interno do cache.
    from datetime import datetime, timedelta, timezone
    snap, _ts = cache._entradas["perfis_usuarios"]
    cache._entradas["perfis_usuarios"] = (snap, datetime.now(timezone.utc) - timedelta(seconds=120))

    resultado = service.verificar_readiness()
    assert resultado["status"] == "degradado"
    assert resultado["servicos"]["perfis_usuarios"]["estado"] == "indisponivel"


def test_servico_sem_cache_funciona_sem_fallback():
    """SaudeServiceImpl tambem deve funcionar sem cache injetado."""
    perfis = _Cliente("perfis_usuarios", [_fora("perfis_usuarios")])
    ia = _Cliente("ia_analise_codigo", [_ok("ia_analise_codigo")])
    gerador = _Cliente("gerador_documentacao", [_ok("gerador_documentacao")])

    service = SaudeServiceImpl(perfis, ia, gerador, cache=None)
    resultado = service.verificar_readiness()

    assert resultado["status"] == "degradado"
    assert resultado["servicos"]["perfis_usuarios"]["origem"] == "live"

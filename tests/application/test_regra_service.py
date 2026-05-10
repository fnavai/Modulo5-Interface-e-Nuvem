# Testes do RegraServiceImpl (US IN-09).

import pytest

from app.adapters.driven.clients.notificador_comentario_pr_github import (
    NotificadorComentarioPRFake,
)
from app.adapters.driven.persistence.repositorio_regras_sqlite import (
    RepositorioRegrasSQLite,
)
from app.application.services.regra_service_impl import RegraServiceImpl
from app.domain.entidades.regra_arquitetural import Severidade, TipoRegra
from app.domain.excecoes import (
    RegraInvalidaError,
    RegraNaoEncontradaError,
)


@pytest.fixture
def cenario(tmp_path):
    repo = RepositorioRegrasSQLite(str(tmp_path / "regras.db"))
    notificador = NotificadorComentarioPRFake()
    service = RegraServiceImpl(repo, notificador)
    yield service, repo, notificador
    repo.fechar()


def _criar_regra_proibido(service, padrao="app/legacy/*", sev=Severidade.WARNING):
    return service.criar(
        nome=f"Nao mexer em {padrao}",
        tipo=TipoRegra.ARQUIVO_PROIBIDO,
        severidade=sev,
        parametros={"padrao_glob": padrao},
        mensagem="Codigo legado — pedir review extra.",
        criada_por="alice",
    )


# ---------- CRUD ----------

def test_criar_persiste(cenario):
    service, repo, _ = cenario
    r = _criar_regra_proibido(service)
    assert repo.obter(r.id) is not None
    assert r.tipo == TipoRegra.ARQUIVO_PROIBIDO
    assert r.severidade == Severidade.WARNING
    assert r.ativa is True


def test_criar_parametros_faltando_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RegraInvalidaError):
        service.criar(
            nome="X", tipo=TipoRegra.ARQUIVO_PROIBIDO, severidade=Severidade.INFO,
            parametros={}, mensagem="", criada_por="alice",
        )


def test_criar_nome_vazio_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RegraInvalidaError):
        service.criar(
            nome="", tipo=TipoRegra.ARQUIVO_PROIBIDO, severidade=Severidade.INFO,
            parametros={"padrao_glob": "*"}, mensagem="", criada_por="alice",
        )


def test_atualizar_severidade_e_ativa(cenario):
    service, _, _ = cenario
    r = _criar_regra_proibido(service)
    novo = service.atualizar(r.id, severidade=Severidade.ERROR, ativa=False)
    assert novo.severidade == Severidade.ERROR
    assert novo.ativa is False


def test_atualizar_inexistente_404(cenario):
    service, _, _ = cenario
    with pytest.raises(RegraNaoEncontradaError):
        service.atualizar("fantasma", ativa=False)


def test_listar_filtra_por_ativa(cenario):
    service, _, _ = cenario
    r1 = _criar_regra_proibido(service, padrao="a/*")
    r2 = _criar_regra_proibido(service, padrao="b/*")
    service.atualizar(r2.id, ativa=False)
    ativas = service.listar(ativa=True)
    assert {r.id for r in ativas} == {r1.id}


def test_remover(cenario):
    service, _, _ = cenario
    r = _criar_regra_proibido(service)
    assert service.remover(r.id) is True
    assert service.remover(r.id) is False


# ---------- Avaliadores ----------

def test_avaliador_arquivo_proibido_detecta(cenario):
    service, _, _ = cenario
    _criar_regra_proibido(service, padrao="app/legacy/*")
    res = service.avaliar("o/r", "main", ("app/legacy/foo.py", "app/novo.py"))
    assert res.tem_violacoes is True
    assert len(res.violacoes) == 1
    assert "app/legacy/foo.py" in res.violacoes[0].arquivos_envolvidos


def test_avaliador_arquivo_proibido_nao_detecta(cenario):
    service, _, _ = cenario
    _criar_regra_proibido(service, padrao="app/legacy/*")
    res = service.avaliar("o/r", "main", ("app/novo.py",))
    assert res.tem_violacoes is False


def test_avaliador_limite_arquivos(cenario):
    service, _, _ = cenario
    service.criar(
        nome="Limite 3", tipo=TipoRegra.LIMITE_ARQUIVOS, severidade=Severidade.INFO,
        parametros={"limite": 3}, mensagem="", criada_por="alice",
    )
    res = service.avaliar("o/r", "main", ("a.py", "b.py", "c.py", "d.py"))
    assert len(res.violacoes) == 1
    assert "4 arquivos" in res.violacoes[0].mensagem


def test_avaliador_par_obrigatorio_detecta_par_faltando(cenario):
    service, _, _ = cenario
    service.criar(
        nome="Codigo precisa de teste",
        tipo=TipoRegra.PAR_OBRIGATORIO, severidade=Severidade.ERROR,
        parametros={"padrao_origem": "app/*.py", "padrao_par": "tests/*.py"},
        mensagem="Sem teste!", criada_por="alice",
    )
    # mexeu em app sem teste
    res = service.avaliar("o/r", "main", ("app/main.py",))
    assert res.tem_violacoes is True
    # mexeu em app com teste — passa
    res = service.avaliar("o/r", "main", ("app/main.py", "tests/test_main.py"))
    assert res.tem_violacoes is False


def test_avaliador_padrao_branch(cenario):
    service, _, _ = cenario
    service.criar(
        nome="Padrao branch", tipo=TipoRegra.PADRAO_BRANCH,
        severidade=Severidade.WARNING,
        parametros={"regex": "^(feature|fix|chore)/.+"},
        mensagem="Use prefixo feature/ ou fix/", criada_por="alice",
    )
    assert service.avaliar("o/r", "feature/x", ()).tem_violacoes is False
    assert service.avaliar("o/r", "minha-branch", ()).tem_violacoes is True


def test_regras_inativas_nao_avaliam(cenario):
    service, _, _ = cenario
    r = _criar_regra_proibido(service, padrao="*.py")
    service.atualizar(r.id, ativa=False)
    res = service.avaliar("o/r", "main", ("qualquer.py",))
    assert res.regras_aplicadas == 0
    assert res.tem_violacoes is False


def test_severidade_maxima_calculada(cenario):
    service, _, _ = cenario
    _criar_regra_proibido(service, padrao="a*", sev=Severidade.INFO)
    _criar_regra_proibido(service, padrao="b*", sev=Severidade.ERROR)
    res = service.avaliar("o/r", "main", ("a.py", "b.py"))
    assert res.severidade_maxima == "error"


def test_sem_violacoes_severidade_maxima_eh_ok(cenario):
    service, _, _ = cenario
    _criar_regra_proibido(service, padrao="legacy/*")
    res = service.avaliar("o/r", "main", ("app/main.py",))
    assert res.severidade_maxima == "ok"


# ---------- avaliar_e_comentar ----------

def test_avaliar_e_comentar_posta_quando_ha_violacao(cenario):
    service, _, notificador = cenario
    _criar_regra_proibido(service, padrao="app/legacy/*", sev=Severidade.WARNING)
    resultado, comentario_id = service.avaliar_e_comentar(
        "o/r", pr_numero=42, branch_head="main",
        arquivos_modificados=("app/legacy/x.py",),
    )
    assert resultado.tem_violacoes is True
    assert comentario_id is not None
    assert len(notificador.chamadas) == 1
    msg = notificador.chamadas[0]["mensagem"]
    assert "Alerta de Regras Arquiteturais" in msg
    assert "WARN" in msg
    assert "app/legacy/x.py" in msg


def test_avaliar_e_comentar_nao_posta_se_sem_violacao(cenario):
    service, _, notificador = cenario
    _criar_regra_proibido(service, padrao="legacy/*")
    resultado, comentario_id = service.avaliar_e_comentar(
        "o/r", pr_numero=42, branch_head="main",
        arquivos_modificados=("app/novo.py",),
    )
    assert resultado.tem_violacoes is False
    assert comentario_id is None
    assert notificador.chamadas == []


def test_avaliar_e_comentar_pr_invalido_400(cenario):
    service, _, _ = cenario
    with pytest.raises(RegraInvalidaError):
        service.avaliar_e_comentar("o/r", pr_numero=0, branch_head="main", arquivos_modificados=())


def test_avaliar_e_comentar_falha_no_github_nao_quebra(cenario):
    service, _, notificador = cenario
    _criar_regra_proibido(service, padrao="*.py", sev=Severidade.ERROR)
    notificador.fazer_falhar()
    resultado, comentario_id = service.avaliar_e_comentar(
        "o/r", pr_numero=1, branch_head="main", arquivos_modificados=("x.py",),
    )
    assert resultado.tem_violacoes is True
    assert comentario_id is None  # falha foi engolida — resultado ainda devolvido

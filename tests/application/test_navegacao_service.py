# Testes do NavegacaoServiceImpl (US IN-01).

import pytest

from app.adapters.driven.clients.validador_arquivo_github_fake import (
    ValidadorArquivoGitHubFake,
)
from app.application.services.navegacao_service_impl import NavegacaoServiceImpl
from app.domain.excecoes import GitHubIndisponivelError, NavegacaoInvalidaError


def test_gera_url_sem_linha():
    s = NavegacaoServiceImpl()
    r = s.gerar_link("fnavai/Modulo5-Interface-e-Nuvem", "app/main.py", ref="develop")
    assert r.link.url == "https://github.com/fnavai/Modulo5-Interface-e-Nuvem/blob/develop/app/main.py"
    assert r.link.abre_em_nova_aba is True
    assert r.validacao.executada is False


def test_gera_url_com_linha_unica():
    s = NavegacaoServiceImpl()
    r = s.gerar_link("o/r", "x.py", ref="main", linha=42)
    assert r.link.url == "https://github.com/o/r/blob/main/x.py#L42"


def test_gera_url_com_range_de_linhas():
    s = NavegacaoServiceImpl()
    r = s.gerar_link("o/r", "x.py", linha=10, linha_fim=20)
    assert r.link.url == "https://github.com/o/r/blob/HEAD/x.py#L10-L20"


def test_repositorio_invalido_400():
    s = NavegacaoServiceImpl()
    with pytest.raises(NavegacaoInvalidaError):
        s.gerar_link("nao_tem_barra", "x.py")


def test_arquivo_com_path_traversal_falha():
    s = NavegacaoServiceImpl()
    with pytest.raises(NavegacaoInvalidaError):
        s.gerar_link("o/r", "app/../../etc/passwd")


def test_arquivo_com_barra_inicial_eh_normalizado():
    s = NavegacaoServiceImpl()
    r = s.gerar_link("o/r", "/app/main.py", ref="main")
    # Sem barra dupla apos blob/main/
    assert "//app/main.py" not in r.link.url
    assert r.link.url == "https://github.com/o/r/blob/main/app/main.py"


def test_linha_zero_invalida():
    s = NavegacaoServiceImpl()
    with pytest.raises(NavegacaoInvalidaError):
        s.gerar_link("o/r", "x.py", linha=0)


def test_linha_fim_sem_linha_falha():
    s = NavegacaoServiceImpl()
    with pytest.raises(NavegacaoInvalidaError):
        s.gerar_link("o/r", "x.py", linha_fim=10)


def test_linha_fim_menor_que_linha_falha():
    s = NavegacaoServiceImpl()
    with pytest.raises(NavegacaoInvalidaError):
        s.gerar_link("o/r", "x.py", linha=20, linha_fim=10)


def test_validar_existencia_sem_validador_devolve_mensagem_amigavel():
    s = NavegacaoServiceImpl(validador=None)
    r = s.gerar_link("o/r", "x.py", validar_existencia=True)
    assert r.validacao.executada is True
    assert r.validacao.existe is None
    assert "nao ha integracao" in r.validacao.mensagem.lower()


def test_validar_existencia_arquivo_existe():
    fake = ValidadorArquivoGitHubFake()
    fake.configurar("o/r", "x.py", "main", existe=True)
    s = NavegacaoServiceImpl(validador=fake)
    r = s.gerar_link("o/r", "x.py", ref="main", validar_existencia=True)
    assert r.validacao.executada is True
    assert r.validacao.existe is True
    assert r.validacao.mensagem is None


def test_validar_existencia_arquivo_nao_encontrado_msg_amigavel():
    fake = ValidadorArquivoGitHubFake()
    fake.configurar("o/r", "x.py", "main", existe=False)
    s = NavegacaoServiceImpl(validador=fake)
    r = s.gerar_link("o/r", "x.py", ref="main", validar_existencia=True)
    assert r.validacao.executada is True
    assert r.validacao.existe is False
    assert "x.py" in r.validacao.mensagem
    assert "main" in r.validacao.mensagem


def test_validar_existencia_github_fora_devolve_mensagem_amigavel():
    fake = ValidadorArquivoGitHubFake()
    fake.fazer_falhar_com(GitHubIndisponivelError("503"))
    s = NavegacaoServiceImpl(validador=fake)
    r = s.gerar_link("o/r", "x.py", validar_existencia=True)
    assert r.validacao.executada is True
    assert r.validacao.existe is None
    assert "nao conseguimos verificar" in r.validacao.mensagem.lower()


def test_link_sempre_abre_em_nova_aba():
    s = NavegacaoServiceImpl()
    r = s.gerar_link("o/r", "x.py")
    assert r.link.abre_em_nova_aba is True
    assert r.to_dict()["abre_em_nova_aba"] is True

from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.cliente_perfis import ClientePerfis


def test_cliente_gerador_exige_gerar_diagrama_branch():
    assert "gerar_diagrama_branch" in ClienteGerador.__abstractmethods__
    assert "verificar_saude" in ClienteGerador.__abstractmethods__


def test_cliente_ia_so_exige_verificar_saude():
    # A IA nao tem endpoint por owner/repo; o resumo estrutural do fluxo
    # unificado vem do "estrutura" do Gerador. O port da IA fica so com saude.
    assert ClienteIAAnalise.__abstractmethods__ == frozenset({"verificar_saude"})


def test_cliente_perfis_exige_obter_ownership():
    assert "obter_ownership" in ClientePerfis.__abstractmethods__
    assert "verificar_saude" in ClientePerfis.__abstractmethods__


def test_metodos_novos_sao_nao_abstratos_para_nao_quebrar_fakes():
    # analisar_qualidade / gerar_apresentacao / gerar_relatorio foram
    # adicionados como NAO-abstratos de proposito: __abstractmethods__
    # intacto -> fakes/adapters existentes seguem instanciaveis.
    assert ClienteIAAnalise.__abstractmethods__ == frozenset(
        {"verificar_saude"})
    assert "gerar_apresentacao" not in ClienteGerador.__abstractmethods__
    assert "gerar_relatorio" not in ClienteGerador.__abstractmethods__
    assert ClienteGerador.__abstractmethods__ == frozenset(
        {"verificar_saude", "gerar_diagrama_branch"})


def test_fonte_codigo_exige_obter_arquivo():
    from app.application.ports.driven.fonte_codigo import FonteCodigo
    assert FonteCodigo.__abstractmethods__ == frozenset({"obter_arquivo"})

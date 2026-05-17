# Fakes dos clientes Gerador/Perfis para testes do fluxo unificado (BFF).
# Implementam os ports reais; permitem injetar sucesso ou simular falha.
# Nao sao usados em producao (composition_root usa os adapters HTTP).

from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.application.ports.driven.fonte_codigo import FonteCodigo
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.domain.excecoes import FalhaNaComunicacaoError


def _saude(nome: str) -> StatusServico:
    return StatusServico(
        nome=nome, estado=EstadoServico.DISPONIVEL, detalhes="fake."
    )


class ClienteGeradorFake(ClienteGerador):
    def __init__(self, diagrama=None, estrutura=None, falha=False,
                 falha_doc=False):
        self._diagrama = diagrama
        self._estrutura = estrutura
        self._falha = falha
        self._falha_doc = falha_doc
        # Guarda o ultimo payload recebido (assert nos testes).
        self.ultima_apresentacao = None
        self.ultimo_relatorio = None

    def verificar_saude(self) -> StatusServico:
        return _saude("gerador_documentacao")

    def gerar_diagrama_branch(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        if self._falha:
            raise FalhaNaComunicacaoError("Gerador indisponivel (fake).")
        return {
            "diagrama_mermaid": self._diagrama,
            "estrutura": self._estrutura,
            "warnings": [],
        }

    def gerar_apresentacao(self, apresentacao: dict) -> dict:
        if self._falha_doc:
            raise FalhaNaComunicacaoError("Gerador doc indisponivel (fake).")
        self.ultima_apresentacao = apresentacao
        return {
            "conteudo": b"PK\x03\x04fake-pptx",
            "nome_arquivo": "apresentacao.pptx",
            "media_type": "application/vnd.openxmlformats-officedocument."
                          "presentationml.presentation",
        }

    def gerar_relatorio(self, relatorio: dict) -> dict:
        if self._falha_doc:
            raise FalhaNaComunicacaoError("Gerador doc indisponivel (fake).")
        self.ultimo_relatorio = relatorio
        fmt = (relatorio.get("formato") or "pdf").lower()
        return {
            "conteudo": b"%PDF-1.4 fake" if fmt == "pdf" else b"# fake md",
            "nome_arquivo": f"relatorio.{ 'pdf' if fmt=='pdf' else 'md' }",
            "media_type": "application/pdf" if fmt == "pdf"
                          else "text/markdown",
        }


class ClienteIAFake(ClienteIAAnalise):
    def __init__(self, qualidade=None, falha=False):
        self._qualidade = qualidade
        self._falha = falha

    def verificar_saude(self) -> StatusServico:
        return _saude("ia_analise_codigo")

    def analisar_qualidade(self, codigo: str):
        if self._falha:
            raise RuntimeError("IA qualidade falhou (fake).")
        return self._qualidade


class FonteCodigoFake(FonteCodigo):
    def __init__(self, codigo=None, falha=False):
        self._codigo = codigo
        self._falha = falha

    def obter_arquivo(self, owner, repo, branch, caminho):
        if self._falha:
            raise RuntimeError("Fonte falhou (fake).")
        return self._codigo


class ClientePerfisFake(ClientePerfis):
    def __init__(self, ownership=None, falha=False):
        self._ownership = ownership
        self._falha = falha

    def verificar_saude(self) -> StatusServico:
        return _saude("perfis_usuarios")

    def obter_ownership(self, owner: str, repo: str, modulo: str):
        if self._falha:
            raise FalhaNaComunicacaoError("Perfis indisponivel (fake).")
        return self._ownership

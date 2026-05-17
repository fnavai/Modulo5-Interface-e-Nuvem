# Porta driving: ProjetoService
# Responsabilidade: contrato do fluxo unificado do portal — dado um
# repo/branch/arquivo, agrega diagrama+estrutura (Gerador, que orquestra
# GitHub->IA) e ownership (Perfis) numa visao unica do projeto.

from abc import ABC, abstractmethod

from app.domain.entidades.projeto_visualizado import ProjetoVisualizado


class ProjetoService(ABC):

    @abstractmethod
    def analisar(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> ProjetoVisualizado:
        """
        Executa o fluxo unificado. O diagrama (via Gerador) e obrigatorio:
        se o Gerador falhar, levanta excecao de dominio. Ownership (Perfis)
        e qualidade (IA) sao best-effort: se cairem, retornam None nessas
        partes (degradacao graciosa — uma falha parcial nao derruba a
        visao).
        """
        pass

    @abstractmethod
    def gerar_documento_pptx(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        """
        Roda analisar() e monta uma apresentacao PPTX via Gerador
        (POST /apresentacao/gerar). Retorna {"conteudo": bytes,
        "nome_arquivo": str, "media_type": str}. Diagrama e obrigatorio
        (sem analise nao ha o que documentar) — propaga excecao se o
        Gerador falhar.
        """
        pass

    @abstractmethod
    def gerar_documento_relatorio(
        self, owner: str, repo: str, branch: str, caminho: str,
        formato: str = "pdf",
    ) -> dict:
        """
        Roda analisar() e monta um relatorio (md/docx/pdf) via Gerador
        (POST /reports). Retorna {"conteudo": bytes, "nome_arquivo": str,
        "media_type": str}.
        """
        pass

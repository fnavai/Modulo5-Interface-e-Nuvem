# Implementacao do ProjetoService: orquestra Gerador (obrigatorio),
# Perfis (best-effort) e IA-qualidade (best-effort) no fluxo unificado,
# e monta documentos (PPTX/relatorio) via Gerador.

from app.application.ports.driving.projeto_service import ProjetoService
from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.application.ports.driven.cliente_perfis import ClientePerfis
from app.application.services.documento_builders import (
    montar_apresentacao,
    montar_relatorio,
)
from app.domain.entidades.projeto_visualizado import (
    ProjetoVisualizado,
    ReferenciaRepo,
)


class ProjetoServiceImpl(ProjetoService):

    def __init__(
        self,
        cliente_gerador: ClienteGerador,
        cliente_perfis: ClientePerfis,
        cliente_ia=None,
        fonte_codigo=None,
    ):
        # cliente_ia e fonte_codigo sao opcionais p/ nao quebrar quem
        # constroi ProjetoServiceImpl(gerador, perfis) (testes/baseline).
        # Sem eles, a qualidade fica None (degradacao graciosa).
        self._gerador = cliente_gerador
        self._perfis = cliente_perfis
        self._ia = cliente_ia
        self._fonte = fonte_codigo

    def analisar(
        self, owner: str, repo: str, branch: str, caminho: str, tipo: str = "classe"
    ) -> ProjetoVisualizado:
        referencia = ReferenciaRepo(
            owner=owner, repo=repo, branch=branch, caminho=caminho
        )

        # Parte obrigatoria: Gerador (pipeline Gerador->GitHub->IA).
        # Se falhar, a excecao de dominio sobe (a tela nao tem o que mostrar).
        diagrama = self._gerador.gerar_diagrama_branch(
            owner, repo, branch, caminho, tipo
        )
        diagrama_mermaid = diagrama.get("diagrama_mermaid")
        resumo_ia = diagrama.get("estrutura")

        # Best-effort: ownership do Perfis.
        try:
            ownership = self._perfis.obter_ownership(owner, repo, caminho)
        except Exception:
            ownership = None

        # Best-effort: qualidade da IA (precisa do codigo cru via GitHub).
        # Qualquer falha -> None; nunca derruba o fluxo unificado.
        qualidade = None
        if self._ia is not None and self._fonte is not None:
            try:
                codigo = self._fonte.obter_arquivo(
                    owner, repo, branch, caminho
                )
                if codigo:
                    qualidade = self._ia.analisar_qualidade(codigo)
            except Exception:
                qualidade = None

        return ProjetoVisualizado(
            referencia=referencia,
            diagrama_mermaid=diagrama_mermaid,
            resumo_ia=resumo_ia,
            ownership=ownership,
            qualidade=qualidade,
        )

    def gerar_documento_pptx(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        projeto = self.analisar(owner, repo, branch, caminho)
        return self._gerador.gerar_apresentacao(montar_apresentacao(projeto))

    def gerar_documento_relatorio(
        self, owner: str, repo: str, branch: str, caminho: str,
        formato: str = "pdf",
    ) -> dict:
        projeto = self.analisar(owner, repo, branch, caminho)
        return self._gerador.gerar_relatorio(
            montar_relatorio(projeto, formato)
        )

    def obter_diagrama_perfis(self):
        return self._perfis.obter_diagrama_perfis()

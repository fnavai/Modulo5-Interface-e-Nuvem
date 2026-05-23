# Porta driven: ClienteGerador
# Responsabilidade: contrato de comunicação com o serviço Gerador-Documentacao.

from abc import ABC, abstractmethod
from app.domain.entidades.status_servico import StatusServico


class ClienteGerador(ABC):

    @abstractmethod
    def verificar_saude(self) -> StatusServico:
        """
        Consulta o health check do Gerador-Documentacao.
        Nunca levanta excecao — retorna StatusServico com estado adequado.
        """
        pass

    @abstractmethod
    def gerar_diagrama_branch(
        self, owner: str, repo: str, branch: str, caminho: str, tipo: str = "classe"
    ) -> dict:
        """
        Pede ao Gerador (POST /diagrama/branch, formato=mermaid) o diagrama
        de um arquivo numa branch — pipeline Gerador->GitHub->IA. Retorna um
        dict normalizado: {"diagrama_mermaid": str, "estrutura": dict|None,
        "warnings": list}. "estrutura" e a analise estrutural que a IA
        produziu (componentes/relacoes/linguagem), surfaceada via Gerador.
        Levanta excecao de dominio se o Gerador falhar (parte obrigatoria
        do fluxo unificado).
        """
        pass

    # Metodos NAO-abstratos de proposito: nao quebrar os fakes/adapters
    # existentes (que so implementam saude + diagrama) nem o contrato
    # __abstractmethods__ testado. So o adapter HTTP real sobrescreve.
    def gerar_apresentacao(self, apresentacao: dict) -> dict:
        """
        POST /apresentacao/gerar — gera o PPTX a partir de um payload ja
        montado ({titulo, subtitulo, autor, slides:[...]}). Retorna
        {"conteudo": bytes, "nome_arquivo": str, "media_type": str}.
        Levanta excecao de dominio se o Gerador falhar (download e acao
        explicita do usuario — erro deve ser visivel, nao silencioso).
        """
        raise NotImplementedError

    def gerar_relatorio(self, relatorio: dict) -> dict:
        """
        POST /reports — gera o relatorio (md/docx/pdf) a partir de um
        payload ja montado ({titulo, formato, secoes:[...]}). Retorna
        {"conteudo": bytes, "nome_arquivo": str, "media_type": str}.
        Levanta excecao de dominio se o Gerador falhar.
        """
        raise NotImplementedError
# Adaptador driven: cliente HTTP para o Gerador-Documentacao

import requests

from app.application.ports.driven.cliente_gerador import ClienteGerador
from app.domain.entidades.status_servico import StatusServico, EstadoServico
from app.domain.excecoes import FalhaNaComunicacaoError, ServicoIndisponivelError
from app.config.settings import (
    GERADOR_URL,
    HTTP_TIMEOUT,
    DIAGRAMA_TIMEOUT_SEGUNDOS,
)


class AdaptadorClienteGerador(ClienteGerador):

    def verificar_saude(self) -> StatusServico:
        try:
            resposta = requests.get(
                f"{GERADOR_URL}/health/ready",
                timeout=HTTP_TIMEOUT
            )
            if resposta.status_code == 200:
                return StatusServico(
                    nome="gerador_documentacao",
                    estado=EstadoServico.DISPONIVEL,
                    detalhes="Respondendo normalmente."
                )
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.DEGRADADO,
                detalhes=f"Status inesperado: {resposta.status_code}"
            )
        except requests.exceptions.Timeout:
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Timeout ao conectar."
            )
        except requests.exceptions.ConnectionError:
            return StatusServico(
                nome="gerador_documentacao",
                estado=EstadoServico.INDISPONIVEL,
                detalhes="Servico inacessivel."
            )

    def gerar_diagrama_branch(
        self, owner: str, repo: str, branch: str, caminho: str, tipo: str = "classe"
    ) -> dict:
        corpo = {
            "repositorio": f"{owner}/{repo}",
            "branch": branch,
            "arquivo": caminho,
            "formato": "mermaid",
            "tipo": tipo,
        }
        try:
            resposta = requests.post(
                f"{GERADOR_URL}/diagrama/branch",
                json=corpo,
                timeout=DIAGRAMA_TIMEOUT_SEGUNDOS,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise ServicoIndisponivelError(
                f"Gerador inacessivel ao gerar diagrama: {e}"
            ) from e

        if resposta.status_code != 200:
            detalhe = self._detalhe_erro(resposta)
            raise FalhaNaComunicacaoError(
                f"Gerador respondeu {resposta.status_code}: {detalhe}"
            )

        dados = resposta.json()
        return {
            "diagrama_mermaid": dados.get("mermaid"),
            "estrutura": dados.get("estrutura"),
            "warnings": dados.get("warnings", []),
        }

    def gerar_apresentacao(self, apresentacao: dict) -> dict:
        # POST /apresentacao/gerar -> PPTX binario (download).
        return self._gerar_documento(
            "/apresentacao/gerar", apresentacao, "apresentacao.pptx",
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation",
        )

    def gerar_relatorio(self, relatorio: dict) -> dict:
        # POST /reports -> md/docx/pdf binario (download).
        return self._gerar_documento(
            "/reports", relatorio, "relatorio.md", "text/markdown",
        )

    def _gerar_documento(
        self, path: str, corpo: dict, nome_padrao: str, media_padrao: str
    ) -> dict:
        try:
            resposta = requests.post(
                f"{GERADOR_URL}{path}",
                json=corpo,
                timeout=DIAGRAMA_TIMEOUT_SEGUNDOS,
            )
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            raise ServicoIndisponivelError(
                f"Gerador inacessivel ao gerar documento: {e}"
            ) from e

        if resposta.status_code != 200:
            detalhe = self._detalhe_erro(resposta)
            raise FalhaNaComunicacaoError(
                f"Gerador respondeu {resposta.status_code}: {detalhe}"
            )

        return {
            "conteudo": resposta.content,
            "nome_arquivo": self._nome_do_header(
                resposta.headers.get("Content-Disposition"), nome_padrao
            ),
            "media_type": (
                resposta.headers.get("Content-Type") or media_padrao
            ).split(";")[0].strip(),
        }

    @staticmethod
    def _nome_do_header(content_disposition: str, padrao: str) -> str:
        # Content-Disposition: attachment; filename="x.pptx"
        if not content_disposition:
            return padrao
        marcador = 'filename="'
        i = content_disposition.find(marcador)
        if i == -1:
            return padrao
        i += len(marcador)
        j = content_disposition.find('"', i)
        nome = content_disposition[i:j] if j != -1 else ""
        return nome.strip() or padrao

    @staticmethod
    def _detalhe_erro(resposta) -> str:
        # Erros do Gerador (FastAPI) vem como {"detail": <str>}.
        try:
            corpo = resposta.json()
            return str(corpo.get("detail", corpo))
        except Exception:
            return (resposta.text or "")[:200]
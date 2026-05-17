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
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> dict:
        corpo = {
            "repositorio": f"{owner}/{repo}",
            "branch": branch,
            "arquivo": caminho,
            "formato": "mermaid",
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

    @staticmethod
    def _detalhe_erro(resposta) -> str:
        # Erros do Gerador (FastAPI) vem como {"detail": <str>}.
        try:
            corpo = resposta.json()
            return str(corpo.get("detail", corpo))
        except Exception:
            return (resposta.text or "")[:200]
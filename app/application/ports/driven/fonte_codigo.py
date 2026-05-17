# Porta driven: FonteCodigo
# Responsabilidade: obter o conteudo cru de um arquivo de um repo/branch
# do GitHub. Necessario porque os endpoints da IA (ex.: /qualidade/analisar)
# recebem {"codigo": <str>} — o Gerador busca o arquivo internamente para o
# diagrama, mas nao devolve o codigo; entao o BFF precisa busca-lo para a
# analise de qualidade.

from abc import ABC, abstractmethod


class FonteCodigo(ABC):

    @abstractmethod
    def obter_arquivo(
        self, owner: str, repo: str, branch: str, caminho: str
    ) -> "str | None":
        """
        Devolve o conteudo do arquivo como string, ou None.
        Best-effort: qualquer falha (rede, 404, rate-limit, binario)
        retorna None — nunca levanta (a qualidade e parte opcional do
        fluxo unificado; o diagrama, obrigatorio, vem do Gerador).
        """
        pass

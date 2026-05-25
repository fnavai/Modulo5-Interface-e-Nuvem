# Porta driven: NotificadorComentarioPR (US IN-09)
# Posta comentarios em PRs do GitHub via Issues API.

from abc import ABC, abstractmethod
from typing import Optional


class NotificadorComentarioPR(ABC):

    @abstractmethod
    def comentar(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        """
        Posta comentario no PR. Retorna id do comentario do GitHub em sucesso.
        Levanta ComentarioPRError em qualquer falha.
        """
        pass

# Exceções de domínio do Interface-e-Nuvem

class ServicoIndisponivelError(Exception):
    """Lançada quando um serviço externo nao responde."""
    pass


class FalhaNaComunicacaoError(Exception):
    """Lançada quando a comunicação com serviço externo falha."""
    pass


class NavegacaoInvalidaError(ValueError):
    """Inputs invalidos para gerar link de navegacao (repo malformado, path traversal, etc)."""
    pass


class GitHubIndisponivelError(RuntimeError):
    """Nao conseguimos alcancar a Contents API do GitHub para validar arquivo."""
    pass
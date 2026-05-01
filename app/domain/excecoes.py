# Exceções de domínio do Interface-e-Nuvem

class ServicoIndisponivelError(Exception):
    """Lançada quando um serviço externo nao responde."""
    pass


class FalhaNaComunicacaoError(Exception):
    """Lançada quando a comunicação com serviço externo falha."""
    pass
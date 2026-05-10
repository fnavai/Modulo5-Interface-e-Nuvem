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


class ADRInvalidaError(ValueError):
    """ADR com campos faltando ou invalidos."""
    pass


class ADRNaoEncontradaError(LookupError):
    """ADR nao existe."""
    pass


class TransicaoStatusInvalidaError(RuntimeError):
    """Tentativa de transicao de status nao permitida pela maquina de estados da ADR."""
    pass


class VinculoDuplicadoError(ValueError):
    """Mesmo (adr, repositorio, modulo) ja vinculado."""
    pass


class RascunhoInvalidoError(ValueError):
    """Rascunho com dados faltando ou invalidos."""
    pass


class RascunhoNaoEncontradoError(LookupError):
    """Rascunho com esse id nao existe."""
    pass


class PublicacaoPRError(RuntimeError):
    """Falha ao criar branch, commitar ou abrir PR no GitHub."""
    pass


class RegraInvalidaError(ValueError):
    """Regra arquitetural com dados invalidos (tipo desconhecido, parametros faltando)."""
    pass


class RegraNaoEncontradaError(LookupError):
    """Regra com esse id nao existe."""
    pass


class ComentarioPRError(RuntimeError):
    """Falha ao postar comentario no PR via Issues API."""
    pass
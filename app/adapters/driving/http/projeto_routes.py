# Rota driving: POST /api/projeto/analisar (fluxo unificado do portal).
# Recebe repositorio/branch/caminho, delega ao ProjetoService e devolve a
# visao agregada (diagrama + estrutura + ownership) com degradacao graciosa.

import re

from flask import Blueprint, jsonify, request

from app.application.ports.driving.projeto_service import ProjetoService
from app.domain.excecoes import (
    FalhaNaComunicacaoError,
    ProjetoInvalidoError,
    ServicoIndisponivelError,
)

_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def criar_projeto_routes(servico: ProjetoService) -> Blueprint:
    # Blueprint criado dentro da factory para suportar create_app() multiplas
    # vezes nos testes (mesma convencao das outras rotas do repo).
    bp = Blueprint("projeto", __name__, url_prefix="/api/projeto")

    @bp.post("/analisar")
    def analisar():
        payload = request.get_json(silent=True) or {}
        repositorio = (payload.get("repositorio") or "").strip()
        branch = (payload.get("branch") or "develop").strip() or "develop"
        caminho = (payload.get("caminho") or "").strip()

        if not _REPO_RE.match(repositorio):
            return jsonify({"erro": "repositorio deve estar no formato 'owner/repo'."}), 400
        if not caminho:
            return jsonify({"erro": "caminho do arquivo e obrigatorio."}), 400
        if ".." in caminho:
            return jsonify({"erro": "caminho invalido (path traversal)."}), 400

        owner, repo = repositorio.split("/", 1)

        try:
            projeto = servico.analisar(owner, repo, branch, caminho)
        except ProjetoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            # Gerador (parte obrigatoria) fora — upstream indisponivel.
            return jsonify({"erro": f"Gerador indisponivel: {e}"}), 502

        return jsonify(projeto.to_dict()), 200

    return bp

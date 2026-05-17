# Rotas driving dos seletores do portal (sem digitar branch/arquivo):
#   GET /api/repo/branches?repositorio=owner/repo
#   GET /api/repo/arquivos?repositorio=owner/repo&branch=b
# Best-effort sobre o GitHub; erro de upstream -> 502 {"erro": ...}.

import re

from flask import Blueprint, jsonify, request

from app.application.ports.driving.repo_service import RepoService
from app.domain.excecoes import (
    FalhaNaComunicacaoError,
    ServicoIndisponivelError,
)

_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def criar_repo_routes(servico: RepoService) -> Blueprint:
    bp = Blueprint("repo", __name__, url_prefix="/api/repo")

    def _owner_repo():
        repositorio = (request.args.get("repositorio") or "").strip()
        if not _REPO_RE.match(repositorio):
            return None, (jsonify(
                {"erro": "repositorio deve estar no formato 'owner/repo'."}),
                400)
        owner, repo = repositorio.split("/", 1)
        return (owner, repo), None

    @bp.get("/branches")
    def branches():
        ref, erro = _owner_repo()
        if erro:
            return erro
        owner, repo = ref
        try:
            nomes = servico.listar_branches(owner, repo)
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            return jsonify({"erro": f"GitHub indisponivel: {e}"}), 502
        return jsonify({"branches": nomes}), 200

    @bp.get("/arquivos")
    def arquivos():
        ref, erro = _owner_repo()
        if erro:
            return erro
        owner, repo = ref
        branch = (request.args.get("branch") or "develop").strip() or "develop"
        try:
            lista = servico.listar_arquivos_codigo(owner, repo, branch)
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            return jsonify({"erro": f"GitHub indisponivel: {e}"}), 502
        return jsonify({"arquivos": lista, "branch": branch}), 200

    return bp

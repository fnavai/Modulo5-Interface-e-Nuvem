# Rotas driving do fluxo unificado do portal:
#   POST /api/projeto/analisar            -> visao agregada (JSON)
#   POST /api/projeto/documento/pptx      -> apresentacao .pptx (download)
#   POST /api/projeto/documento/relatorio -> relatorio md/docx/pdf (download)
# Delegam ao ProjetoService; degradacao graciosa nas partes best-effort.

import re

from flask import Blueprint, Response, jsonify, request

from app.application.ports.driving.projeto_service import ProjetoService
from app.domain.excecoes import (
    FalhaNaComunicacaoError,
    ProjetoInvalidoError,
    ServicoIndisponivelError,
)

_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
_FORMATOS = {"md", "markdown", "docx", "pdf"}


def _ler_referencia(payload: dict):
    """Retorna (owner, repo, branch, caminho) ou (None, resposta_erro)."""
    repositorio = (payload.get("repositorio") or "").strip()
    branch = (payload.get("branch") or "develop").strip() or "develop"
    caminho = (payload.get("caminho") or "").strip()

    if not _REPO_RE.match(repositorio):
        return None, (jsonify(
            {"erro": "repositorio deve estar no formato 'owner/repo'."}), 400)
    if not caminho:
        return None, (jsonify(
            {"erro": "caminho do arquivo e obrigatorio."}), 400)
    if ".." in caminho:
        return None, (jsonify(
            {"erro": "caminho invalido (path traversal)."}), 400)

    owner, repo = repositorio.split("/", 1)
    return (owner, repo, branch, caminho), None


def _download(resultado: dict) -> Response:
    return Response(
        resultado["conteudo"],
        status=200,
        mimetype=resultado.get("media_type") or "application/octet-stream",
        headers={
            "Content-Disposition":
                f'attachment; filename="{resultado["nome_arquivo"]}"'
        },
    )


def criar_projeto_routes(servico: ProjetoService) -> Blueprint:
    # Blueprint criado dentro da factory para suportar create_app()
    # multiplas vezes nos testes (mesma convencao das outras rotas).
    bp = Blueprint("projeto", __name__, url_prefix="/api/projeto")

    @bp.post("/analisar")
    def analisar():
        payload = request.get_json(silent=True) or {}
        ref, erro = _ler_referencia(payload)
        if erro:
            return erro
        owner, repo, branch, caminho = ref
        try:
            projeto = servico.analisar(owner, repo, branch, caminho)
        except ProjetoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            return jsonify({"erro": f"Gerador indisponivel: {e}"}), 502
        return jsonify(projeto.to_dict()), 200

    @bp.post("/documento/pptx")
    def documento_pptx():
        payload = request.get_json(silent=True) or {}
        ref, erro = _ler_referencia(payload)
        if erro:
            return erro
        owner, repo, branch, caminho = ref
        try:
            resultado = servico.gerar_documento_pptx(
                owner, repo, branch, caminho)
        except ProjetoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            return jsonify({"erro": f"Gerador indisponivel: {e}"}), 502
        return _download(resultado)

    @bp.post("/documento/relatorio")
    def documento_relatorio():
        payload = request.get_json(silent=True) or {}
        ref, erro = _ler_referencia(payload)
        if erro:
            return erro
        owner, repo, branch, caminho = ref
        formato = (payload.get("formato") or "pdf").strip().lower()
        if formato not in _FORMATOS:
            return jsonify(
                {"erro": f"formato invalido. Use um de: "
                         f"{', '.join(sorted(_FORMATOS))}."}), 400
        try:
            resultado = servico.gerar_documento_relatorio(
                owner, repo, branch, caminho, formato)
        except ProjetoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        except (ServicoIndisponivelError, FalhaNaComunicacaoError) as e:
            return jsonify({"erro": f"Gerador indisponivel: {e}"}), 502
        return _download(resultado)

    return bp

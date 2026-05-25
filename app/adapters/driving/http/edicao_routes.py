# Rotas Flask para o editor de diagramas (US IN-02).

from flask import Blueprint, jsonify, request

from app.application.ports.driving.edicao_service import RascunhoService
from app.domain.excecoes import (
    PublicacaoPRError,
    RascunhoInvalidoError,
    RascunhoNaoEncontradoError,
)


def criar_edicao_routes(servico: RascunhoService) -> Blueprint:
    bp = Blueprint("edicao", __name__, url_prefix="/api/rascunhos")

    @bp.post("")
    def criar():
        payload = request.get_json(silent=True) or {}
        try:
            rascunho = servico.criar(
                repositorio=payload.get("repositorio", ""),
                branch_base=payload.get("branch_base", ""),
                autor_id=payload.get("autor_id", ""),
                titulo=payload.get("titulo", ""),
                conteudo_mermaid=payload.get("conteudo_mermaid", ""),
                descricao_mudanca=payload.get("descricao_mudanca", ""),
            )
        except RascunhoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(rascunho.to_dict()), 201

    @bp.get("")
    def listar():
        rascunhos = servico.listar(
            autor_id=request.args.get("autor_id"),
            repositorio=request.args.get("repositorio"),
        )
        return jsonify({"rascunhos": [r.to_dict() for r in rascunhos]}), 200

    @bp.get("/<rascunho_id>")
    def obter(rascunho_id):
        try:
            rascunho = servico.obter(rascunho_id)
        except RascunhoNaoEncontradoError as e:
            return jsonify({"erro": str(e)}), 404
        return jsonify(rascunho.to_dict()), 200

    @bp.put("/<rascunho_id>")
    def atualizar(rascunho_id):
        payload = request.get_json(silent=True) or {}
        try:
            rascunho = servico.atualizar(
                rascunho_id=rascunho_id,
                conteudo_mermaid=payload.get("conteudo_mermaid"),
                descricao_mudanca=payload.get("descricao_mudanca"),
                titulo=payload.get("titulo"),
            )
        except RascunhoNaoEncontradoError as e:
            return jsonify({"erro": str(e)}), 404
        except RascunhoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(rascunho.to_dict()), 200

    @bp.delete("/<rascunho_id>")
    def remover(rascunho_id):
        if not servico.remover(rascunho_id):
            return jsonify({"erro": "Rascunho nao encontrado."}), 404
        return ("", 204)

    @bp.post("/<rascunho_id>/publicar")
    def publicar(rascunho_id):
        payload = request.get_json(silent=True) or {}
        caminho = payload.get("caminho_arquivo", "")
        try:
            resultado = servico.publicar_como_pr(
                rascunho_id=rascunho_id,
                caminho_arquivo=caminho,
                mensagem_commit=payload.get("mensagem_commit", ""),
                titulo_pr=payload.get("titulo_pr", ""),
                descricao_pr=payload.get("descricao_pr", ""),
            )
        except RascunhoNaoEncontradoError as e:
            return jsonify({"erro": str(e)}), 404
        except RascunhoInvalidoError as e:
            return jsonify({"erro": str(e)}), 400
        except PublicacaoPRError as e:
            return jsonify({"erro": str(e)}), 502
        return jsonify(resultado.to_dict()), 201

    return bp

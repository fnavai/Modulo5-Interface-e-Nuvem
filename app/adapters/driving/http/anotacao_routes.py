# Rotas Flask para anotacoes colaborativas em diagramas (US IN-03).

from flask import Blueprint, jsonify, request

from app.application.ports.driving.anotacao_service import AnotacaoService
from app.domain.excecoes import (
    AnotacaoInvalidaError,
    AnotacaoNaoEncontradaError,
    PermissaoAnotacaoNegadaError,
)


def _parse_bool_query(valor):
    if valor is None:
        return None
    return valor.lower() in ("1", "true", "yes")


def criar_anotacao_routes(servico: AnotacaoService) -> Blueprint:
    bp = Blueprint("anotacoes", __name__, url_prefix="/api/anotacoes")

    @bp.post("")
    def criar():
        payload = request.get_json(silent=True) or {}
        try:
            anotacao = servico.criar(
                repositorio=payload.get("repositorio", ""),
                modulo=payload.get("modulo", ""),
                componente=payload.get("componente", ""),
                autor_id=payload.get("autor_id", ""),
                conteudo=payload.get("conteudo", ""),
                parent_id=payload.get("parent_id"),
            )
        except AnotacaoNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except AnotacaoInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(anotacao.to_dict()), 201

    @bp.get("")
    def listar():
        anotacoes = servico.listar(
            repositorio=request.args.get("repositorio"),
            modulo=request.args.get("modulo"),
            componente=request.args.get("componente"),
            resolvida=_parse_bool_query(request.args.get("resolvida")),
            autor_id=request.args.get("autor_id"),
        )
        return jsonify({"anotacoes": [a.to_dict() for a in anotacoes]}), 200

    @bp.get("/<anotacao_id>")
    def obter(anotacao_id):
        try:
            return jsonify(servico.obter(anotacao_id).to_dict()), 200
        except AnotacaoNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404

    @bp.put("/<anotacao_id>")
    def atualizar(anotacao_id):
        payload = request.get_json(silent=True) or {}
        try:
            anotacao = servico.atualizar(
                anotacao_id=anotacao_id,
                autor_id=payload.get("autor_id", ""),
                conteudo=payload.get("conteudo", ""),
            )
        except AnotacaoNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except PermissaoAnotacaoNegadaError as e:
            return jsonify({"erro": str(e)}), 403
        except AnotacaoInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(anotacao.to_dict()), 200

    @bp.delete("/<anotacao_id>")
    def remover(anotacao_id):
        autor = request.args.get("autor_id", "")
        try:
            ok = servico.remover(anotacao_id, autor)
        except PermissaoAnotacaoNegadaError as e:
            return jsonify({"erro": str(e)}), 403
        if not ok:
            return jsonify({"erro": "Anotacao nao encontrada."}), 404
        return ("", 204)

    @bp.post("/<anotacao_id>/resolver")
    def resolver(anotacao_id):
        try:
            return jsonify(servico.resolver(anotacao_id).to_dict()), 200
        except AnotacaoNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404

    @bp.post("/<anotacao_id>/reabrir")
    def reabrir(anotacao_id):
        try:
            return jsonify(servico.reabrir(anotacao_id).to_dict()), 200
        except AnotacaoNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404

    @bp.get("/thread/<parent_id>")
    def listar_thread(parent_id):
        respostas = servico.listar_thread(parent_id)
        return jsonify({"respostas": [a.to_dict() for a in respostas]}), 200

    @bp.get("/mencoes")
    def listar_mencoes():
        usuario = request.args.get("usuario_id", "")
        try:
            anotacoes = servico.listar_mencoes_de(usuario)
        except AnotacaoInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify({"anotacoes": [a.to_dict() for a in anotacoes]}), 200

    return bp

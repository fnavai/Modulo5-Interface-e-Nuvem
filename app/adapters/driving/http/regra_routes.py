# Rotas Flask para regras arquiteturais e alertas em PR (US IN-09).

from flask import Blueprint, jsonify, request

from app.application.ports.driving.regra_service import RegraService
from app.domain.entidades.regra_arquitetural import Severidade, TipoRegra
from app.domain.excecoes import RegraInvalidaError, RegraNaoEncontradaError


def _parse_tipo(valor):
    try:
        return TipoRegra(valor)
    except ValueError:
        validos = ", ".join(t.value for t in TipoRegra)
        return ("erro", f"tipo invalido: '{valor}'. Validos: {validos}.")


def _parse_severidade(valor):
    try:
        return Severidade(valor)
    except ValueError:
        validos = ", ".join(s.value for s in Severidade)
        return ("erro", f"severidade invalida: '{valor}'. Validas: {validos}.")


def criar_regra_routes(servico: RegraService) -> Blueprint:
    bp = Blueprint("regras", __name__, url_prefix="/api/regras")

    @bp.post("")
    def criar():
        payload = request.get_json(silent=True) or {}
        tipo = _parse_tipo(payload.get("tipo", ""))
        if isinstance(tipo, tuple):
            return jsonify({"erro": tipo[1]}), 400
        sev = _parse_severidade(payload.get("severidade", ""))
        if isinstance(sev, tuple):
            return jsonify({"erro": sev[1]}), 400
        try:
            regra = servico.criar(
                nome=payload.get("nome", ""),
                tipo=tipo,
                severidade=sev,
                parametros=payload.get("parametros", {}) or {},
                mensagem=payload.get("mensagem", ""),
                criada_por=payload.get("criada_por", ""),
            )
        except RegraInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(regra.to_dict()), 201

    @bp.get("")
    def listar():
        ativa_arg = request.args.get("ativa")
        ativa = None
        if ativa_arg is not None:
            ativa = ativa_arg.lower() in ("1", "true", "yes")
        return jsonify({"regras": [r.to_dict() for r in servico.listar(ativa=ativa)]}), 200

    @bp.get("/<regra_id>")
    def obter(regra_id):
        try:
            return jsonify(servico.obter(regra_id).to_dict()), 200
        except RegraNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404

    @bp.put("/<regra_id>")
    def atualizar(regra_id):
        payload = request.get_json(silent=True) or {}
        kwargs = {}
        if "nome" in payload:
            kwargs["nome"] = payload["nome"]
        if "severidade" in payload:
            sev = _parse_severidade(payload["severidade"])
            if isinstance(sev, tuple):
                return jsonify({"erro": sev[1]}), 400
            kwargs["severidade"] = sev
        if "parametros" in payload:
            kwargs["parametros"] = payload["parametros"]
        if "mensagem" in payload:
            kwargs["mensagem"] = payload["mensagem"]
        if "ativa" in payload:
            kwargs["ativa"] = bool(payload["ativa"])
        try:
            regra = servico.atualizar(regra_id, **kwargs)
        except RegraNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except RegraInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(regra.to_dict()), 200

    @bp.delete("/<regra_id>")
    def remover(regra_id):
        if not servico.remover(regra_id):
            return jsonify({"erro": "Regra nao encontrada."}), 404
        return ("", 204)

    @bp.post("/avaliar")
    def avaliar():
        payload = request.get_json(silent=True) or {}
        try:
            resultado = servico.avaliar(
                repositorio=payload.get("repositorio", ""),
                branch_head=payload.get("branch_head", ""),
                arquivos_modificados=tuple(payload.get("arquivos_modificados", []) or []),
            )
        except RegraInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(resultado.to_dict()), 200

    @bp.post("/avaliar-e-comentar")
    def avaliar_e_comentar():
        payload = request.get_json(silent=True) or {}
        try:
            resultado, comentario_id = servico.avaliar_e_comentar(
                repositorio=payload.get("repositorio", ""),
                pr_numero=int(payload.get("pr_numero", 0)),
                branch_head=payload.get("branch_head", ""),
                arquivos_modificados=tuple(payload.get("arquivos_modificados", []) or []),
            )
        except RegraInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify({
            "resultado": resultado.to_dict(),
            "comentario_id": comentario_id,
            "comentario_postado": comentario_id is not None,
        }), 200

    return bp

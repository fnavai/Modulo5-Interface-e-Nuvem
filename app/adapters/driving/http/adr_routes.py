# Rotas Flask para ADRs e vinculos (US IN-07).

from flask import Blueprint, jsonify, request

from app.application.ports.driving.adr_service import ADRService
from app.domain.entidades.decisao_arquitetural import StatusADR
from app.domain.excecoes import (
    ADRInvalidaError,
    ADRNaoEncontradaError,
    TransicaoStatusInvalidaError,
    VinculoDuplicadoError,
)


def _parse_status(valor):
    if valor is None:
        return None
    try:
        return StatusADR(valor)
    except ValueError:
        validos = ", ".join(s.value for s in StatusADR)
        return ("erro", f"status invalido: '{valor}'. Validos: {validos}.")


def criar_adr_routes(servico: ADRService) -> Blueprint:
    bp = Blueprint("adrs", __name__, url_prefix="/api/adrs")

    # --- Template ---

    @bp.get("/template")
    def get_template():
        return jsonify(servico.template_padrao()), 200

    # --- CRUD ADR ---

    @bp.post("")
    def criar():
        payload = request.get_json(silent=True) or {}
        try:
            adr = servico.criar(
                titulo=payload.get("titulo", ""),
                contexto=payload.get("contexto", ""),
                decisao=payload.get("decisao", ""),
                consequencias=payload.get("consequencias", ""),
                autor_id=payload.get("autor_id", ""),
            )
        except ADRInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(adr.to_dict()), 201

    @bp.get("")
    def listar():
        status_param = request.args.get("status")
        parsed = _parse_status(status_param)
        if isinstance(parsed, tuple):  # erro de parse
            return jsonify({"erro": parsed[1]}), 400
        autor_id = request.args.get("autor_id")
        adrs = servico.listar(status=parsed, autor_id=autor_id)
        return jsonify({"adrs": [a.to_dict() for a in adrs]}), 200

    @bp.get("/<adr_id>")
    def obter(adr_id):
        try:
            adr = servico.obter(adr_id)
        except ADRNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        return jsonify(adr.to_dict()), 200

    @bp.put("/<adr_id>")
    def atualizar(adr_id):
        payload = request.get_json(silent=True) or {}
        try:
            adr = servico.atualizar(
                adr_id=adr_id,
                autor_id=payload.get("autor_id", ""),
                titulo=payload.get("titulo"),
                contexto=payload.get("contexto"),
                decisao=payload.get("decisao"),
                consequencias=payload.get("consequencias"),
            )
        except ADRNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except TransicaoStatusInvalidaError as e:
            return jsonify({"erro": str(e)}), 409
        except ADRInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(adr.to_dict()), 200

    # --- Maquina de estados ---

    def _executar_transicao(func, **kwargs):
        try:
            adr = func(**kwargs)
        except ADRNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except TransicaoStatusInvalidaError as e:
            return jsonify({"erro": str(e)}), 409
        except ADRInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(adr.to_dict()), 200

    @bp.post("/<adr_id>/propor")
    def propor(adr_id):
        p = request.get_json(silent=True) or {}
        return _executar_transicao(
            servico.propor,
            adr_id=adr_id,
            autor_id=p.get("autor_id", ""),
            documento_aprovacao_id=p.get("documento_aprovacao_id"),
        )

    @bp.post("/<adr_id>/aceitar")
    def aceitar(adr_id):
        p = request.get_json(silent=True) or {}
        return _executar_transicao(servico.aceitar, adr_id=adr_id, autor_id=p.get("autor_id", ""))

    @bp.post("/<adr_id>/descartar")
    def descartar(adr_id):
        p = request.get_json(silent=True) or {}
        return _executar_transicao(
            servico.descartar, adr_id=adr_id, autor_id=p.get("autor_id", ""), motivo=p.get("motivo", ""),
        )

    @bp.post("/<adr_id>/deprecar")
    def deprecar(adr_id):
        p = request.get_json(silent=True) or {}
        return _executar_transicao(
            servico.deprecar, adr_id=adr_id, autor_id=p.get("autor_id", ""), motivo=p.get("motivo", ""),
        )

    @bp.post("/<adr_id>/superar")
    def superar(adr_id):
        p = request.get_json(silent=True) or {}
        return _executar_transicao(
            servico.superar,
            adr_id=adr_id,
            nova_adr_id=p.get("nova_adr_id", ""),
            autor_id=p.get("autor_id", ""),
        )

    # --- Vinculos ---

    @bp.post("/<adr_id>/vinculos")
    def vincular(adr_id):
        p = request.get_json(silent=True) or {}
        try:
            v = servico.vincular_componente(
                adr_id=adr_id,
                repositorio=p.get("repositorio", ""),
                modulo=p.get("modulo", ""),
                descricao_componente=p.get("descricao_componente", ""),
            )
        except ADRNaoEncontradaError as e:
            return jsonify({"erro": str(e)}), 404
        except VinculoDuplicadoError as e:
            return jsonify({"erro": str(e)}), 409
        except ADRInvalidaError as e:
            return jsonify({"erro": str(e)}), 400
        return jsonify(v.to_dict()), 201

    @bp.delete("/<adr_id>/vinculos")
    def desvincular(adr_id):
        repositorio = request.args.get("repositorio")
        modulo = request.args.get("modulo")
        if not repositorio or not modulo:
            return jsonify({"erro": "repositorio e modulo sao obrigatorios."}), 400
        ok = servico.desvincular_componente(adr_id, repositorio, modulo)
        if not ok:
            return jsonify({"erro": "Vinculo nao encontrado."}), 404
        return ("", 204)

    @bp.get("/de-componente")
    def adrs_por_componente():
        repositorio = request.args.get("repositorio")
        modulo = request.args.get("modulo")
        if not repositorio or not modulo:
            return jsonify({"erro": "repositorio e modulo sao obrigatorios."}), 400
        adrs = servico.adrs_de_componente(repositorio, modulo)
        return jsonify({"adrs": [a.to_dict() for a in adrs]}), 200

    @bp.post("/marcadores-diagrama")
    def marcadores():
        p = request.get_json(silent=True) or {}
        repositorio = p.get("repositorio", "")
        modulos = p.get("modulos") or []
        if not repositorio or not isinstance(modulos, list):
            return jsonify({"erro": "repositorio e lista de modulos sao obrigatorios."}), 400
        if not all(isinstance(m, str) and m for m in modulos):
            return jsonify({"erro": "modulos deve ser lista de strings nao-vazias."}), 400
        return jsonify({"marcadores": servico.marcadores_de_diagrama(repositorio, modulos)}), 200

    return bp

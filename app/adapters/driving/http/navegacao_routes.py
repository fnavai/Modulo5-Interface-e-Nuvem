# Adaptador driving: rotas Flask de navegacao (US IN-01).

from flask import Blueprint, jsonify, request

from app.application.ports.driving.navegacao_service import NavegacaoService
from app.domain.excecoes import NavegacaoInvalidaError


def criar_navegacao_routes(servico: NavegacaoService) -> Blueprint:
    # Blueprint criado dentro da factory pra suportar create_app() multiplas vezes
    # (testes que reloadam o composition root).
    bp = Blueprint("navegacao", __name__, url_prefix="/api/navegacao")

    @bp.post("/link")
    def gerar_link():
        payload = request.get_json(silent=True) or {}
        repositorio = payload.get("repositorio") or ""
        arquivo = payload.get("arquivo") or ""
        ref = payload.get("ref") or "HEAD"
        linha = payload.get("linha")
        linha_fim = payload.get("linha_fim")
        validar = bool(payload.get("validar_existencia", False))

        if linha is not None and not isinstance(linha, int):
            return jsonify({"erro": "linha deve ser um inteiro."}), 400
        if linha_fim is not None and not isinstance(linha_fim, int):
            return jsonify({"erro": "linha_fim deve ser um inteiro."}), 400

        try:
            resposta = servico.gerar_link(
                repositorio=repositorio,
                arquivo=arquivo,
                ref=ref,
                linha=linha,
                linha_fim=linha_fim,
                validar_existencia=validar,
            )
        except NavegacaoInvalidaError as e:
            return jsonify({"erro": str(e)}), 400

        return jsonify(resposta.to_dict()), 200

    return bp

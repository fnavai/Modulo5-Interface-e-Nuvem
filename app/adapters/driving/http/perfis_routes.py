"""Rota GET /api/projeto/perfis: proxy do diagrama global de Perfis-Usuarios."""
from flask import Blueprint, jsonify

from app.application.ports.driving.projeto_service import ProjetoService


def criar_perfis_routes(servico: ProjetoService) -> Blueprint:
    bp = Blueprint("perfis", __name__, url_prefix="/api/projeto/perfis")

    @bp.get("")
    def obter_diagrama_perfis():
        resultado = servico.obter_diagrama_perfis()
        if resultado is None:
            return jsonify({"erro": "Perfis-Usuarios indisponivel."}), 502
        return jsonify(resultado), 200

    return bp

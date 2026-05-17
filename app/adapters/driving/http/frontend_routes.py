# Rota driving: serve o portal estatico (SPA sem build).
# GET /            -> frontend/index.html
# GET /assets/<x>  -> frontend/<x> (css/js/etc.)
# Sem sombrear /api/* nem /health (esses sao blueprints proprios).

from pathlib import Path

from flask import Blueprint, send_from_directory

# .../app/adapters/driving/http/frontend_routes.py  -> parents[4] = raiz do repo
_RAIZ_REPO = Path(__file__).resolve().parents[4]
_FRONTEND_DIR_PADRAO = _RAIZ_REPO / "frontend"


def criar_frontend_routes(frontend_dir: str = None) -> Blueprint:
    diretorio = str(frontend_dir or _FRONTEND_DIR_PADRAO)
    bp = Blueprint("frontend", __name__, url_prefix="")

    @bp.get("/")
    def index():
        return send_from_directory(diretorio, "index.html")

    @bp.get("/assets/<path:nome>")
    def asset(nome):
        # send_from_directory bloqueia path traversal e devolve 404 se faltar.
        return send_from_directory(diretorio, nome)

    return bp

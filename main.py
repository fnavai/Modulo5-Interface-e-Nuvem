# Ponto de entrada do Interface-e-Nuvem

from app.config.composition_root import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
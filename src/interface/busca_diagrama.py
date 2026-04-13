import streamlit as st
import requests
import base64
import json
from style import aplicar_estilo

aplicar_estilo()

# CONFIGURAÇÃO DA API (Substitua os valores)
USUARIO = "TheoCasella"
REPO = "Modulo5-Perfis-Usuarios"
CAMINHO_ARQUIVO = "src/data/contrato_perfil.json"

# URL da API de Conteúdo
URL_API = f"https://api.github.com/repos/{USUARIO}/{REPO}/contents/{CAMINHO_ARQUIVO}"

st.title("Módulo 5 - Monitor Cloud (GitHub API)")


def buscar_via_api():
    try:
        response = requests.get(URL_API)

        if response.status_code == 200:
            conteudo_json = response.json()

            conteudo_base64 = conteudo_json['content']
            conteudo_decodificado = base64.b64decode(conteudo_base64).decode('utf-8')

            return json.loads(conteudo_decodificado)
        else:
            st.error(f"Erro na API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Falha na conexão: {e}")
        return None


if st.button("🔄 Sincronizar Agora (Via API)"):
    dados = buscar_via_api()
    if dados:
        st.session_state['dados_api'] = dados

# Exibição dos dados
if 'dados_api' in st.session_state:
    dados = st.session_state['dados_api']
    st.success("✅ Dados obtidos em tempo real via GitHub API!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Especialista", dados.get("usuario_nome"))
        st.write(f"**Cargo:** {dados.get('usuario_cargo')}")

    with col2:
        st.info("Conexão direta: API v3 GitHub")

    st.code(dados.get("diretriz_ia"), language="text")
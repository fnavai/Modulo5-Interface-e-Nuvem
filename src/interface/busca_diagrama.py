import streamlit as st
import json
import requests
import time  # Importante para limpar o cache da URL
from style import aplicar_estilo

# 1. Configuração e Estilo
st.set_page_config(page_title="MVP - Integração GitHub", layout="wide")
aplicar_estilo()

st.title("Módulo 5 - Monitor Cloud (GitHub)")

# --- ATENÇÃO: Substitua pelo seu link real abaixo ---
URL_GITHUB = "https://raw.githubusercontent.com/TheoCasella/Modulo5-Perfis-Usuarios/refs/heads/main/src/data/contrato_perfil.json"

st.subheader("Status da Integração Remota:")


def buscar_dados_github(url):
    """
    Busca os dados do GitHub adicionando um timestamp para
    forçar o servidor a ignorar o cache do navegador/GitHub.
    """
    try:
        # Adiciona um parâmetro aleatório no fim da URL para evitar cache
        url_refresh = f"{url}?t={int(time.time())}"
        response = requests.get(url_refresh)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro HTTP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None


# Chamada direta (sem @st.cache_data para facilitar os testes agora)
dados = buscar_dados_github(URL_GITHUB)

if dados:
    st.success("✅ Dados sincronizados via GitHub!")

    st.markdown("---")
    st.markdown("### 📊 Relatório de Integração Cloud")

    col1, col2 = st.columns(2)
    with col1:
        # Verificando se as chaves existem no JSON para não quebrar a tela
        nome = dados.get("usuario_nome", "Não encontrado")
        cargo = dados.get("usuario_cargo", "Não encontrado")

        st.metric("Usuário Remoto", nome)
        st.write(f"**Persona:** {cargo}")

    with col2:
        st.write("**Origem:** Repositório Público")
        st.info("Sincronização: GitHub Raw Content (Real-time)")

    st.write("**Diretriz Técnica Recebida:**")
    diretriz = dados.get("diretriz_ia", "Sem diretriz disponível.")
    st.code(diretriz, language="text")

else:
    st.error("❌ O arquivo não pôde ser lido ou o link está incorreto.")
    st.info(f"Tentando acessar: {URL_GITHUB}")

    if st.button("🔄 Forçar Sincronização"):
        st.rerun()
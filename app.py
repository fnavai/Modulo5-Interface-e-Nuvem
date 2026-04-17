import streamlit as st
import json
import os

def aplicar_estilo():
    # Caminho para o arquivo CSS
    caminho_css = "style.css"
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            # Aqui injetamos o conteúdo do arquivo .css diretamente
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Executa a função
aplicar_estilo()

PASTA_RESUMOS = os.path.join("src", "mvp_data")
ARQUIVO_FINAL = "contrato_atual.json"

if "step" not in st.session_state:
    st.session_state.step = "formulario"

# --- TELA 1: FORMULÁRIO ---
if st.session_state.step == "formulario":
    st.title("👤 Configuração do Especialista")

    with st.form("registro"):
        nome = st.text_input("Nome:")
        cargo = st.selectbox("Cargo:", ["Tech Lead", "Desenvolvedor", "Product Manager"])
        btn = st.form_submit_button("GERAR DIAGRAMA")

    if btn and nome:
        nome_arquivo = f"{cargo.lower().replace(' ', '_')}.txt"
        caminho_resumo = os.path.join(PASTA_RESUMOS, nome_arquivo)

        try:
            with open(caminho_resumo, "r", encoding="utf-8") as f:
                resumo_ia = f.read()
        except FileNotFoundError:
            resumo_ia = "Resumo padrão: Foco em entregas de alta qualidade técnica."

        dados = {"usuario": nome, "cargo": cargo, "resumo": resumo_ia}

        with open(ARQUIVO_FINAL, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

        st.session_state.dados = dados
        st.session_state.step = "visualizacao"
        st.rerun()

# --- TELA 2: VISUALIZAÇÃO ---
elif st.session_state.step == "visualizacao":
    st.title("📊 Diagrama Gerado")

    dados = st.session_state.dados
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Especialista Responsável:** \n### {dados['usuario']}")
    with col2:
        st.markdown(f"**Perfil de Atuação:** \n### {dados['cargo']}")

    st.divider()

    # Lógica de carregamento do conteúdo IA
    mapa_arquivo = {
        "Tech Lead": "src/MVP/resumo_Tech_Lead.py",
        "Desenvolvedor": "src/MVP/resumo_Desenvolvedor.py",
        "Product Manager": "src/MVP/resumo_Product_Manager.py",
    }

    caminho_arquivo = mapa_arquivo.get(dados['cargo'])

    if caminho_arquivo and os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            resumo_bruto = f.read()

        conteudo_ia = resumo_bruto.split('"""')[1].strip() if '"""' in resumo_bruto else resumo_bruto.strip()

        # APLICAÇÃO DA CLASSE CSS .bloco-ia
        st.markdown(f"""
            <div class="bloco-ia">
                {conteudo_ia.replace('\n', '<br>')}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Exibindo resumo padrão (Arquivo específico não encontrado).")
        st.markdown(f'<div class="bloco-ia">{dados["resumo"]}</div>', unsafe_allow_html=True)

    if st.button("⬅️ Novo Cadastro"):
        st.session_state.step = "formulario"
        st.rerun()
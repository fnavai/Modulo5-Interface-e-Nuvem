import streamlit as st


def aplicar_estilo():
    st.markdown(
        """
        <style>
        /* 1. Força a cor preta em todos os textos base e parágrafos */
        html, body, [data-testid="stWidgetLabel"], .stMarkdown {
            color: #1C1C1C !important;
        }

        /* 2. Título Principal (Módulo 5) */
        .stTitle {
            color: #000000 !important;
            font-weight: 700;
            text-align: center;
        }

        /* 3. Subtítulos e Headers */
        h1, h2, h3, p {
            color: #1C1C1C !important;
        }

        /* 4. Estilização específica para os números das métricas (Relatório) */
        [data-testid="stMetricValue"] {
            color: #000000 !important;
        }

        /* 5. Estilização dos rótulos das métricas */
        [data-testid="stMetricLabel"] {
            color: #4F4F4F !important;
        }

        /* 6. Fundo da página (Cinza bem claro para contraste) */
        .stApp {
            background-color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
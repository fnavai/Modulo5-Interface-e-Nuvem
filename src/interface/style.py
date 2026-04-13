import streamlit as st


def aplicar_estilo():
    st.markdown(
        """
        <style>
        /* 1. Fundo da página e texto geral */
        .stApp {
            background-color: #FFFFFF;
        }

        html, body, [data-testid="stWidgetLabel"], .stMarkdown {
            color: #1C1C1C !important;
        }

        /* 2. Títulos e Subtítulos */
        h1, h2, h3, p {
            color: #1C1C1C !important;
        }

        /* 3. CUSTOMIZAÇÃO DO BOTÃO (O seu quadrado preto) */
        /* Mudando para fundo branco/cinza claro com texto preto */
        div.stButton > button {
            background-color: #F0F2F6 !important; /* Cinza bem claro */
            color: #1C1C1C !important;           /* Texto Preto */
            border: 1px solid #d3d3d3 !important; /* Borda cinza clara */
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease;
        }

        /* Efeito ao passar o mouse (Hover) */
        div.stButton > button:hover {
            background-color: #E0E0E0 !important; /* Cinza um pouco mais escuro */
            border-color: #1C1C1C !important;
            color: #000000 !important;
        }

        /* 4. Estilo das métricas (Relatório) */
        [data-testid="stMetricValue"] {
            color: #000000 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #4F4F4F !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
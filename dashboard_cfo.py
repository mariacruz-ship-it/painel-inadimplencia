import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Painel Executivo - Inadimplência",
    page_icon="📊",
    layout="wide"
)

# Estilização CSS para ajustar botões e inputs
st.markdown("""
    <style>
    .stButton>button {
        background-color: #00e5ff;
        color: #0e1e2e;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        height: 48px;
        font-size: 1rem;
        margin-top: 8px;
    }
    .stButton>button:hover {
        background-color: #00b8cc;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Lógica de Autenticação / Login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def verificar_senha():
    if st.session_state.get("senha_input") == "Omie2026":
        st.session_state.autenticado = True
        if "senha_input" in st.session_state:
            del st.session_state["senha_input"]
    else:
        st.error("Senha incorreta. Tente novamente.")

# Tela de Login (Ajustada e 100% Alinhada)
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Bloco do Título e Subtítulo Integrais
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 25px;'>
                <h1 style='margin-bottom: -10px; color: #ffffff; font-size: 2.2rem; font-weight: 700; line-height: 1.1;'>Painel Executivo</h1>
                <h1 style='color: #00e5ff; margin-top: 0px; font-size: 2.2rem; font-weight: 700; line-height: 1.1;'>Inadimplência</h1>
                <p style='color: #a0aab2; font-size: 0.95rem; margin-top: 12px; margin-bottom: 0px;'>Insira sua credencial para acessar.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.text_input(
            "Senha de Acesso", 
            type="password", 
            key="senha_input", 
            placeholder="Sua senha secreta...", 
            on_change=verificar_senha,
            label_visibility="collapsed"
        )
        st.button("Autenticar Acesso", on_click=verificar_senha, use_container_width=True)
    st.stop()

# --- ÁREA LOGADA DO DASHBOARD ---

def tratar_valor_inteligente(df_base, col_nome, deve_calcular_media=False):
    if col_nome not in df_base.columns:
        return 0
    serie = pd.to_numeric(df_base[col_nome], errors='coerce').dropna()
    if len(serie) == 0:
        return 0
    if deve_calcular_media and len(serie) > 1:
        return serie.mean()
    return serie.iloc[0]

@st.cache_data(ttl=0)
def carregar_dados():
    caminho_planilha = "Inadimplência_faixa_fat.xlsx"
    df = pd.read_excel(caminho_planilha, sheet_name="Resumo", header=0)
    return df

try:
    df_resumo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha 'Inadimplência_faixa_fat.xlsx': {e}")
    st.stop()

# Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("### Menu Executivo")
    st.write("Conectado como: **CFO / Diretoria**")
    st.markdown("---")
    if st.button("Encerrar Sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# Cabeçalho Principal do Dashboard
st.title("📊 Painel Executivo - Inadimplência")
st.caption("Acompanhamento de Indicadores Financeiros em Tempo Real")
st.markdown("---")

# Exibição da Tabela de Resumo
st.subheader("Resumo Consolidado")
st.dataframe(df_resumo, use_container_width=True)
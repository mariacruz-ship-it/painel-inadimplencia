import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import glob

# Configuração da página
st.set_page_config(
    page_title="Painel Executivo - Inadimplência",
    page_icon="📊",
    layout="wide"
)

# Estilização CSS para cartões, botões e tabela
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
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #00e5ff;
        font-weight: bold;
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

# Tela de Login
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
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

# --- TRATAMENTO E CARREGAMENTO INTELIGENTE DA PLANILHA ---

def limpar_e_promover_cabecalho(df):
    """Remove linhas/colunas vazias do topo e ajusta o cabeçalho correto"""
    df = df.dropna(how='all').dropna(how='all', axis=1)
    
    # Verifica se os cabeçalhos atuais são genéricos (ex: Unnamed: 0)
    if any("unnamed" in str(col).lower() for col in df.columns):
        for idx in range(min(5, len(df))):
            linha = df.iloc[idx]
            # Se a linha contiver textos relevantes, transforma em novo cabeçalho
            textos = [str(val).strip() for val in linha if pd.notna(val) and str(val) != 'None']
            if len(textos) >= 2:
                novas_colunas = []
                for i, val in enumerate(linha):
                    if pd.notna(val) and str(val) != 'None':
                        novas_colunas.append(str(val).strip())
                    else:
                        novas_colunas.append(f"Coluna_{i+1}")
                df.columns = novas_colunas
                df = df.iloc[idx + 1:].reset_index(drop=True)
                break
    return df

@st.cache_data(ttl=0)
def carregar_dados():
    arquivos_excel = glob.glob("*.xlsx")
    if not arquivos_excel:
        st.error("Nenhum arquivo .xlsx foi encontrado na pasta do projeto.")
        st.stop()
    
    caminho = arquivos_excel[0]
    xls = pd.ExcelFile(caminho)
    aba_alvo = "Resumo" if "Resumo" in xls.sheet_names else xls.sheet_names[0]
    
    df_raw = pd.read_excel(caminho, sheet_name=aba_alvo)
    df_limpo = limpar_e_promover_cabecalho(df_raw)
    return df_limpo

try:
    df_resumo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### Menu Executivo")
    st.write("Conectado como: **CFO / Diretoria**")
    st.markdown("---")
    st.info("💡 Dados vinculados ao consolidado executivo.")
    st.markdown("---")
    if st.button("Encerrar Sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# --- PAINEL PRINCIPAL ---
st.title("📊 Painel Executivo - Inadimplência")
st.caption("Acompanhamento Estratégico em Tempo Real")
st.markdown("---")

# Estrutura em Abas
tab_kpis, tab_graficos, tab_tabela = st.tabs([
    "📊 Visão Geral / KPIs", 
    "📈 Análise Visual", 
    "📋 Tabela Consolidada"
])

# --- ABA 1: KPIS ---
with tab_kpis:
    st.subheader("Indicadores de Desempenho")
    
    # Conversão de dados para valores numéricos
    cols_numericas = []
    for col in df_resumo.columns:
        converted = pd.to_numeric(df_resumo[col], errors='coerce')
        if converted.notna().sum() > 0:
            df_resumo[col] = converted
            cols_numericas.append(col)

    kpi1, kpi2, kpi3 = st.columns(3)
    
    # Busca inteligente por valores de faturamento e inadimplência
    val_fat = df_resumo[cols_numericas[0]].sum() if len(cols_numericas) > 0 else 0
    val_inad = df_resumo[cols_numericas[1]].sum() if len(cols_numericas) > 1 else 0
    pct_taxa = (val_inad / val_fat * 100) if val_fat > 0 else 0

    with kpi1:
        st.metric(label="Volume Monitorado", value=f"R$ {val_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with kpi2:
        st.metric(label="Inadimplência Identificada", value=f"R$ {val_inad:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with kpi3:
        st.metric(label="Taxa Representativa", value=f"{pct_taxa:.2f}%")
        
    st.markdown("---")
    st.subheader("Resumo Executivo")
    st.dataframe(df_resumo, use_container_width=True)

# --- ABA 2: GRÁFICOS ---
with tab_graficos:
    st.subheader("Análise Gráfica dos Dados")
    
    if len(cols_numericas) > 0:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_bar = px.bar(
                df_resumo, 
                y=cols_numericas[0],
                title=f"Distribuição - {cols_numericas[0]}",
                template="plotly_dark",
                color_discrete_sequence=["#00e5ff"]
            )
            fig_bar.update_layout(paper_bgcolor="#0e1e2e", plot_bgcolor="#0e1e2e")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            if len(cols_numericas) > 1:
                fig_line = px.line(
                    df_resumo, 
                    y=cols_numericas[1],
                    title=f"Tendência - {cols_numericas[1]}",
                    template="plotly_dark",
                    color_discrete_sequence=["#ff4b4b"]
                )
                fig_line.update_layout(paper_bgcolor="#0e1e2e", plot_bgcolor="#0e1e2e")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Adicione mais colunas numéricas para visualizar a comparação.")
    else:
        st.info("Aguardando colunas numéricas para renderização dos gráficos.")

# --- ABA 3: TABELA COMPLETA ---
with tab_tabela:
    st.subheader("Base de Dados Completa")
    st.dataframe(df_resumo, use_container_width=True)

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

# Estilização CSS para cartões, botões e indicadores
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
    arquivos_excel = glob.glob("*.xlsx")
    if not arquivos_excel:
        st.error("Nenhum arquivo .xlsx foi encontrado na pasta do projeto.")
        st.stop()
    
    caminho = arquivos_excel[0]
    xls = pd.ExcelFile(caminho)
    
    aba_alvo = "Resumo" if "Resumo" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(caminho, sheet_name=aba_alvo)
    return df

try:
    df_resumo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()

# Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("### Menu Executivo")
    st.write("Conectado como: **CFO / Diretoria**")
    st.markdown("---")
    st.info("💡 Dados sincronizados com a planilha de controle.")
    st.markdown("---")
    if st.button("Encerrar Sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# Cabeçalho Principal
st.title("📊 Painel Executivo - Inadimplência")
st.caption("Acompanhamento Estratégico de Indicadores Financeiros")
st.markdown("---")

# Estrutura de Abas do Dashboard
tab_kpis, tab_graficos, tab_tabela = st.tabs([
    "📊 Visão Geral / KPIs", 
    "📈 Análise Visual & Gráficos", 
    "📋 Base de Dados Consolidada"
])

# --- ABA 1: KPIS E INDICADORES ---
with tab_kpis:
    st.subheader("Indicadores Chave de Desempenho (KPIs)")
    
    # Extração e Cálculo dos Métricas principais
    col_fat = [c for c in df_resumo.columns if 'fat' in str(c).lower() or 'fatur' in str(c).lower()]
    col_inad = [c for c in df_resumo.columns if 'inad' in str(c).lower() or 'vencid' in str(c).lower()]
    
    val_faturamento = tratar_valor_inteligente(df_resumo, col_fat[0]) if col_fat else 0
    val_inadimplencia = tratar_valor_inteligente(df_resumo, col_inad[0]) if col_inad else 0
    
    pct_inadimplencia = (val_inadimplencia / val_faturamento * 100) if val_faturamento > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(
            label="Faturamento Total", 
            value=f"R$ {val_faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    with kpi2:
        st.metric(
            label="Inadimplência Total", 
            value=f"R$ {val_inadimplencia:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    with kpi3:
        st.metric(
            label="Taxa de Inadimplência", 
            value=f"{pct_inadimplencia:.2f}%"
        )
        
    st.markdown("---")
    st.subheader("Resumo Executivo das Faixas")
    
    # Exibição limpa das primeiras linhas de indicadores
    st.dataframe(df_resumo.head(10), use_container_width=True)

# --- ABA 2: GRÁFICOS INTERATIVOS ---
with tab_graficos:
    st.subheader("Análise Gráfica de Inadimplência e Faturamento")
    
    col_g1, col_g2 = st.columns(2)
    
    # Preparação de dados numéricos para gráficos Plotly
    df_numerico = df_resumo.select_dtypes(include=[np.number]).fillna(0)
    
    with col_g1:
        if not df_numerico.empty and len(df_numerico.columns) > 0:
            fig_bar = px.bar(
                df_numerico, 
                title="Distribuição por Faixa / Categoria",
                labels={"value": "Valor (R$)", "index": "Registro"},
                template="plotly_dark",
                color_discrete_sequence=["#00e5ff", "#00b8cc", "#ffffff"]
            )
            fig_bar.update_layout(paper_bgcolor="#0e1e2e", plot_bgcolor="#0e1e2e")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aguardando mais colunas numéricas para renderizar o gráfico de barras.")

    with col_g2:
        if not df_numerico.empty and len(df_numerico.columns) > 1:
            fig_line = px.line(
                df_numerico, 
                title="Evolução dos Indicadores",
                template="plotly_dark",
                color_discrete_sequence=["#00e5ff", "#ff4b4b"]
            )
            fig_line.update_layout(paper_bgcolor="#0e1e2e", plot_bgcolor="#0e1e2e")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Aguardando colunas temporárias/numéricas para o gráfico de evolução.")

# --- ABA 3: TABELA DETALHADA ---
with tab_tabela:
    st.subheader("Visão Completa dos Dados")
    st.dataframe(df_resumo, use_container_width=True)

import io
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel Executivo CFO",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# --- CSS CUSTOMIZADO PARA O LAYOUT EXECUTIVO ESCURO ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #080f18;
        color: #ffffff;
    }
    div[data-testid="stSidebar"] {
        background-color: #050a10;
        border-right: 1px solid #1a2638;
    }
    
    /* Estilização dos Cards Customizados */
    .metric-card {
        background-color: #0e1826;
        border: 1px solid #1a2b42;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-card-top {
        border-top: 3px solid #1d4ed8;
    }
    .metric-card-cyan {
        border-left: 4px solid #06b6d4;
    }
    .metric-card-blue {
        border-left: 4px solid #3b82f6;
    }
    .metric-card-green {
        border-left: 4px solid #10b981;
    }
    .metric-card-orange {
        border-left: 4px solid #f97316;
    }

    .metric-title {
        font-size: 14px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 4px;
    }
    .metric-subtitle {
        font-size: 11px;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1a2638;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #0e1826;
        border-radius: 4px 4px 0px 0px;
        color: #94a3b8;
        padding-left: 16px;
        padding-right: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- AUXILIARES DE FORMATAÇÃO MOEDA E VALORES ---
def fmt_brl(val):
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def fmt_pct(val):
    try:
        return f"{float(val):.2f}%".replace(".", ",")
    except:
        return "0,00%"


# --- CARREGAMENTO DE DADOS DO GOOGLE DRIVE ---
@st.cache_data(ttl=600)
def carregar_dados():
    creds_json = json.loads(st.secrets["google_credentials"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    service = build("drive", "v3", credentials=creds)
    file_id = "1pZUGLPLb9I17QZiYm4AzZHhWrkUe351f"

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    df_raw = pd.read_excel(fh, sheet_name="Resumo", header=1)

    seen = {}
    new_cols = []
    for c in df_raw.columns:
        c_str = str(c).strip()
        if "Unnamed" in c_str or not c_str:
            c_str = "Coluna"
        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)

    df_raw.columns = new_cols
    df = df_raw.dropna(how="all").reset_index(drop=True)

    for col in df.columns:
        if "mês" not in col.lower() and "mes" not in col.lower():
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# --- APLICAÇÃO PRINCIPAL ---
def main():
    try:
        df = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Drive: {e}")
        return

    # --- BARRA LATERAL (FILTROS EXECUTIVOS) ---
    st.sidebar.title("Filtros Executivos")

    col_mes = [c for c in df.columns if "mês" in c.lower() or "mes" in c.lower()]
    opcoes_mes = (
        df[col_mes[0]].astype(str).unique().tolist()
        if col_mes
        else ["Jul/2026"]
    )

    mes_sel = st.sidebar.selectbox("1. Selecione o Mês:", opcoes_mes)
    st.sidebar.radio(
        "2. Visão do Período:",
        ["Mês Completo (Média/Consolidado)", "Dia Específico"],
    )

    # --- CABEÇALHO DA PÁGINA ---
    st.markdown(
        f"**Acompanhamento Estratégico — Consolidado/Média do Mês — {mes_sel}**"
    )
    st.divider()

    # --- ABAS PRINCIPAIS ---
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 Resumo",
            "📁 Visão Geral",
            "📋 Tabela de Dados Completa",
            "📈 Gráficos Históricos",
        ]
    )

    # --- ABA 1: RESUMO ---
    with tab1:
        st.markdown("## Visão Executiva Consolidada")

        # Linha 1: Percentuais de Inadimplência
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - Omie</div>
                    <div class="metric-value">3,76%</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - G-Click</div>
                    <div class="metric-value">4,89%</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - Grupo</div>
                    <div class="metric-value">3,76%</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Linha 2: Faturamento
        f1, f2, f3 = st.columns(3)
        fat_gclick = 1145248.80
        fat_omie = 57639036.73
        fat_total = fat_gclick + fat_omie

        with f1:
            st.markdown(
                f"""<div class="metric-card metric-card-cyan">
                    <div class="metric-title">💻 G-Click — Faturamento</div>
                    <div class="metric-subtitle">Fat. Total Mês Anterior</div>
                    <div class="metric-value">{fmt_brl(fat_gclick)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                f"""<div class="metric-card metric-card-blue">
                    <div class="metric-title">🏢 Omie — Faturamento</div>
                    <div class="metric-subtitle">Fat. Total Mês Anterior</div>
                    <div class="metric-value">{fmt_brl(fat_omie)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                f"""<div class="metric-card metric-card-green">
                    <div class="metric-title">📈 Faturamento Consolidado</div>
                    <div class="metric-subtitle">Total Geral</div>
                    <div class="metric-value">{fmt_brl(fat_total)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ⚠️ Inadimplência & Atrasos por Empresa")

        # Linha 3: Atrasos
        a1, a2, a3 = st.columns(3)
        atraso_gclick = 55986.57
        atraso_omie = 2167452.01
        atraso_total = atraso_gclick + atraso_omie

        with a1:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">G-Click — Atraso</div>
                    <div class="metric-subtitle">Montante Médio</div>
                    <div class="metric-value">{fmt_brl(atraso_gclick)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with a2:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">Omie — Atraso</div>
                    <div class="metric-subtitle">Montante Médio</div>
                    <div class="metric-value">{fmt_brl(atraso_omie)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with a3:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">Total Consolidado</div>
                    <div class="metric-subtitle">Montante Médio</div>
                    <div class="metric-value">{fmt_brl(atraso_total)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # --- ABA 2: VISÃO GERAL ---
    with tab2:
        st.markdown("### 📁 Detalhamento de Visão Geral")
        st.dataframe(df, use_container_width=True)

    # --- ABA 3: TABELA DE DADOS COMPLETA ---
    with tab3:
        st.markdown("### 📋 Tabela de Dados Completa")
        st.dataframe(df, use_container_width=True)

    # --- ABA 4: GRÁFICOS HISTÓRICOS ---
    with tab4:
        st.markdown("### 📈 Gráficos Históricos")
        if col_mes:
            fig = px.bar(
                df, x=col_mes[0], y=df.columns[1], template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

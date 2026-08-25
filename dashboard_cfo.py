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

# --- CSS ESTILIZAÇÃO MODO ESCURO EXECUTIVO ---
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
    .metric-card {
        background-color: #0e1826;
        border: 1px solid #1a2b42;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-card-top { border-top: 3px solid #1d4ed8; }
    .metric-card-cyan { border-left: 4px solid #06b6d4; }
    .metric-card-blue { border-left: 4px solid #3b82f6; }
    .metric-card-green { border-left: 4px solid #10b981; }
    .metric-card-orange { border-left: 4px solid #f97316; }

    .metric-title { font-size: 14px; font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }
    .metric-subtitle { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
    .metric-value { font-size: 22px; font-weight: 700; color: #ffffff; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #1a2638; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; background-color: #0e1826; border-radius: 4px 4px 0px 0px;
        color: #94a3b8; padding-left: 16px; padding-right: 16px;
    }
    .stTabs [aria-selected="true"] { background-color: #0284c7 !important; color: #ffffff !important; }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNÇÕES DE LIMPEZA E TRATAMENTO DE DADOS ---
def converter_valor(val):
    """Converte valores em texto/vírgula brasileira para float."""
    if pd.isna(val) or val == "None" or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace("R$", "").strip()
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    try:
        return float(val_str)
    except:
        return 0.0


def converter_data_excel(val):
    """Converte o número serial do Excel (ex: 44470) para formato Mês/Ano."""
    if pd.isna(val) or val == "None" or val == "":
        return "N/D"
    try:
        val_num = float(val)
        dt = pd.to_datetime(val_num, unit="D", origin="1899-12-30")
        meses = [
            "Jan",
            "Fev",
            "Mar",
            "Abr",
            "Mai",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Out",
            "Nov",
            "Dez",
        ]
        return f"{meses[dt.month - 1]}/{dt.year}"
    except:
        return str(val).strip()


def fmt_brl(val):
    return (
        f"R$ {float(val):,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# --- CARREGAMENTO DO DRIVE ---
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

    # Lê na linha do cabeçalho real (Linha 3 da planilha = header=2)
    df_raw = pd.read_excel(fh, sheet_name="Resumo", header=2)
    df_raw = df_raw.dropna(how="all").reset_index(drop=True)

    # Trata nomes de colunas
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # Tratamento de formato de dados em todas as colunas
    for col in df_raw.columns:
        if "mês" in col.lower() or "mes" in col.lower():
            df_raw[col] = df_raw[col].apply(converter_data_excel)
        else:
            df_raw[col] = df_raw[col].apply(converter_valor)

    return df_raw


# --- APLICAÇÃO PRINCIPAL ---
def main():
    try:
        df = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Drive: {e}")
        return

    # Identificação de colunas do DataFrame
    col_mes = [c for c in df.columns if "mês" in c.lower() or "mes" in c.lower()][0]

    # --- BARRA LATERAL (FILTROS EXECUTIVOS) ---
    st.sidebar.title("Filtros Executivos")
    opcoes_mes = [m for m in df[col_mes].unique() if m != "N/D"]
    mes_sel = st.sidebar.selectbox("1. Selecione o Mês:", opcoes_mes)

    st.sidebar.radio(
        "2. Visão do Período:",
        ["Mês Completo (Média/Consolidado)", "Dia Específico"],
    )

    # Filtrar dados pelo mês selecionado
    df_filtrado = df[df[col_mes] == mes_sel]
    if df_filtrado.empty:
        df_filtrado = df.iloc[[0]]

    linha = df_filtrado.iloc[0]

    # --- CÁLCULO DINÂMICO DE MÉTRICAS DA PLANILHA ---
    fat_total_anterior = linha.get("Fat. Total Mês Anterior", 0.0)
    fat_gclick = linha.get("G-Click total mês anterior", 0.0)
    fat_omie = linha.get("Omie", 0.0)

    if fat_gclick == 0 and fat_total_anterior > 0 and fat_omie > 0:
        fat_gclick = max(0.0, fat_total_anterior - fat_omie)

    trein_omie = linha.get("Treinamento Omie", 0.0)
    trein_gclick = linha.get("Treinamento G-Click", 0.0)
    mens_omie = linha.get("Mensalidade Omie", 0.0)
    mens_gclick = linha.get("Mensalidade G-Click", 0.0)

    faixa_300 = linha.get("Até 300", 0.0)
    faixa_600 = linha.get("De 300,01 até 600", 0.0)
    faixa_acima = linha.get("Acima de 600,01", 0.0)
    total_inadimplencia = faixa_300 + faixa_600 + faixa_acima

    pct_inad_omie = (
        (total_inadimplencia / fat_omie * 100) if fat_omie > 0 else 0.0
    )
    pct_inad_gclick = (
        (total_inadimplencia / fat_gclick * 100) if fat_gclick > 0 else 0.0
    )
    pct_inad_grupo = (
        (total_inadimplencia / fat_total_anterior * 100)
        if fat_total_anterior > 0
        else 0.0
    )

    # --- CABEÇALHO ---
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

        # Percentuais
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - Omie</div>
                    <div class="metric-value">{pct_inad_omie:.2f}%</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - G-Click</div>
                    <div class="metric-value">{pct_inad_gclick:.2f}%</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div class="metric-card metric-card-top">
                    <div class="metric-subtitle">Inadimplência - Grupo</div>
                    <div class="metric-value">{pct_inad_grupo:.2f}%</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Faturamentos
        f1, f2, f3 = st.columns(3)
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
                    <div class="metric-value">{fmt_brl(fat_total_anterior)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ⚠️ Inadimplência & Faixas de Valor")

        # Faixas de Inadimplência
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">Até R$ 300,00</div>
                    <div class="metric-subtitle">Montante Acumulado</div>
                    <div class="metric-value">{fmt_brl(faixa_300)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with a2:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">De R$ 300,01 até R$ 600,00</div>
                    <div class="metric-subtitle">Montante Acumulado</div>
                    <div class="metric-value">{fmt_brl(faixa_600)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with a3:
            st.markdown(
                f"""<div class="metric-card metric-card-orange">
                    <div class="metric-title">Acima de R$ 600,01</div>
                    <div class="metric-subtitle">Montante Acumulado</div>
                    <div class="metric-value">{fmt_brl(faixa_acima)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # --- ABA 2: VISÃO GERAL (PRODUTOS E SERVIÇOS) ---
    with tab2:
        st.markdown("### 💰 Detalhamento por Produtos & Serviços")

        df_produtos = pd.DataFrame(
            {
                "Categoria": [
                    "Treinamento Omie",
                    "Treinamento G-Click",
                    "Mensalidade Omie",
                    "Mensalidade G-Click",
                ],
                "Valor (R$)": [
                    trein_omie,
                    trein_gclick,
                    mens_omie,
                    mens_gclick,
                ],
            }
        )

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            fig_pie = px.pie(
                df_produtos,
                names="Categoria",
                values="Valor (R$)",
                title="Distribuição por Produto / Serviço",
                hole=0.4,
                template="plotly_dark",
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_p2:
            st.dataframe(df_produtos, hide_index=True, use_container_width=True)

    # --- ABA 3: TABELA DE DADOS COMPLETA ---
    with tab3:
        st.markdown("### 📋 Tabela Trata e Convertida")
        st.dataframe(df, use_container_width=True)

    # --- ABA 4: GRÁFICOS HISTÓRICOS ---
    with tab4:
        st.markdown("### 📈 Evolução Histórica de Faturamento")
        fig_hist = px.bar(
            df,
            x=col_mes,
            y="Fat. Total Mês Anterior",
            title="Faturamento Total por Mês",
            template="plotly_dark",
        )
        st.plotly_chart(fig_hist, use_container_width=True)


if __name__ == "__main__":
    main()

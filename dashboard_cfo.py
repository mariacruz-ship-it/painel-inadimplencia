import io
import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel Executivo - Inadimplência", page_icon="📊", layout="wide"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #080f18;
        color: #ffffff;
    }
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
    div[data-testid="stSidebar"] {
        background-color: #050a10;
        border-right: 1px solid #1a2638;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- LÓGICA DE AUTENTICAÇÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False


def verificar_senha():
    if st.session_state.get("senha_input") == "Omie2026":
        st.session_state.autenticado = True
        if "senha_input" in st.session_state:
            del st.session_state["senha_input"]
    else:
        st.error("Senha incorreta. Tente novamente.")


# --- TELA DE LOGIN ---
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
            unsafe_allow_html=True,
        )

        st.text_input(
            "Senha de Acesso",
            type="password",
            key="senha_input",
            placeholder="Sua senha secreta...",
            on_change=verificar_senha,
            label_visibility="collapsed",
        )
        st.button(
            "Autenticar Acesso",
            on_click=verificar_senha,
            use_container_width=True,
        )
    st.stop()


# --- ÁREA LOGADA: CARREGAMENTO DE DADOS DO GOOGLE DRIVE ---
@st.cache_data(ttl=300)
def carregar_dados():
    # 1. Autenticação via Secrets do Streamlit Cloud
    creds_json = json.loads(st.secrets["google_credentials"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    service = build("drive", "v3", credentials=creds)
    file_id = "1pZUGLPLb9I17QZiYm4AzZHhWrkUe351f"  # Planilha no Drive

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)

    # 2. Leitura com o cabeçalho na linha correta
    df_raw = pd.read_excel(fh, sheet_name="Resumo", header=2)
    df_raw = df_raw.dropna(how="all").reset_index(drop=True)

    # Ajusta nomes de colunas
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # Trata datas (converte números como 44470 para formato Mês/Ano)
    for col in df_raw.columns:
        if "mês" in col.lower() or "mes" in col.lower():

            def conv_date(val):
                try:
                    dt = pd.to_datetime(
                        float(val), unit="D", origin="1899-12-30"
                    )
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

            df_raw[col] = df_raw[col].apply(conv_date)
        else:

            def conv_num(val):
                if pd.isna(val) or val == "None" or val == "":
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val)
                v_str = str(val).replace("R$", "").strip()
                if "," in v_str and "." in v_str:
                    v_str = v_str.replace(".", "").replace(",", ".")
                elif "," in v_str:
                    v_str = v_str.replace(",", ".")
                try:
                    return float(v_str)
                except:
                    return 0.0

            df_raw[col] = df_raw[col].apply(conv_num)

    return df_raw


try:
    df_resumo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao conectar e carregar dados do Google Drive: {e}")
    st.stop()


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("### Menu Executivo")
    st.write("Conectado como: **CFO / Diretoria**")
    st.markdown("---")

    if st.button("Encerrar Sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()


# --- CORPO PRINCIPAL DO DASHBOARD ---
st.title("📊 Painel Executivo - Inadimplência")
st.caption("Acompanhamento de Indicadores Financeiros em Tempo Real")
st.markdown("---")

st.subheader("Resumo Consolidado")
st.dataframe(df_resumo, use_container_width=True)

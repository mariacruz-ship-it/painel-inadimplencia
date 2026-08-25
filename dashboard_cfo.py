import io
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# --- CONFIGURAÇÃO E CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    # 1. Autenticação via Secrets
    creds_json = json.loads(st.secrets["google_credentials"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    # 2. Conexão Drive
    service = build("drive", "v3", credentials=creds)
    file_id = "1pZUGLPLb9I17QZiYm4AzZHhWrkUe351f"  # ID atualizado da planilha da TI

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)

    # 3. Leitura e ajuste de cabeçalho (Linha 3 do Excel = header=2)
    df_raw = pd.read_excel(fh, sheet_name="Resumo", header=2)

    # 4. Trata colunas duplicadas ou sem nome
    seen = {}
    new_cols = []
    for c in df_raw.columns:
        c_str = str(c).strip()
        if "Unnamed" in c_str or not c_str:
            c_str = "Coluna_Sem_Nome"

        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)

    df_raw.columns = new_cols
    df = df_raw.dropna(how="all").reset_index(drop=True)

    return df


# --- APLICAÇÃO PRINCIPAL ---
def main():
    st.set_page_config(
        page_title="Painel Executivo CFO", layout="wide", page_icon="📊"
    )

    st.title("📊 Painel Executivo CFO")
    st.subheader(
        "Análise Estratégica de Inadimplência e Faturamento | Atualização Automática"
    )

    # Carrega dados
    try:
        df = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Drive: {e}")
        return

    # --- CRIAÇÃO DAS ABAS ---
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 Visão Geral",
            "💰 Produtos & Serviços",
            "🎯 Faixas de Valor",
            "📋 Tabela Completa",
        ]
    )

    # --- ABA 1: VISÃO GERAL ---
    with tab1:
        st.markdown("### 📈 Resumo do Perfil de Inadimplência")

        col1, col2, col3 = st.columns(3)
        fat_total = (
            df["Fat. Total Mês Anterior"].sum()
            if "Fat. Total Mês Anterior" in df.columns
            else 0
        )
        omie_total = df["Omie"].sum() if "Omie" in df.columns else 0

        col1.metric(
            "Faturamento Total Mês Ant.", f"R$ {fat_total:,.2f}"
        )
        col2.metric("Total Omie", f"R$ {omie_total:,.2f}")
        col3.metric("Total de Registros", len(df))

        st.divider()

        if (
            "Mês" in df.columns
            and "Fat. Total Mês Anterior" in df.columns
        ):
            fig_evolucao = px.bar(
                df,
                x="Mês",
                y="Fat. Total Mês Anterior",
                title="Evolução do Faturamento Mensal",
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)

    # --- ABA 2: PRODUTOS & SERVIÇOS ---
    with tab2:
        st.markdown("### 💰 Análise por Produto e Serviço")
        cols_prod = [
            c
            for c in [
                "Omie",
                "Treinamento Omie",
                "Treinamento G-Click",
                "Mensalidade Omie",
                "Mensalidade G-Click",
            ]
            if c in df.columns
        ]

        if cols_prod:
            df_prod = df[cols_prod].sum().reset_index()
            df_prod.columns = ["Produto/Serviço", "Valor Total"]

            fig_prod = px.pie(
                df_prod,
                names="Produto/Serviço",
                values="Valor Total",
                title="Distribuição por Produto/Serviço",
            )
            st.plotly_chart(fig_prod, use_container_width=True)

    # --- ABA 3: FAIXAS DE VALOR ---
    with tab3:
        st.markdown("### 🎯 Inadimplência por Faixa de Valor")
        cols_faixas = [
            c
            for c in ["Até 300", "De 300,01 até 600", "Acima de 600,01"]
            if c in df.columns
        ]

        if cols_faixas:
            df_faixas = df[cols_faixas].sum().reset_index()
            df_faixas.columns = ["Faixa de Valor", "Total"]

            fig_faixas = px.bar(
                df_faixas,
                x="Faixa de Valor",
                y="Total",
                color="Faixa de Valor",
                title="Valores Inadimplentes por Faixa",
            )
            st.plotly_chart(fig_faixas, use_container_width=True)

    # --- ABA 4: TABELA DETALHADA ---
    with tab4:
        st.markdown("### 📋 Visão Geral dos Dados Brutos")
        st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()

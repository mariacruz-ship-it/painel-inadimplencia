import os
import re
import sys
import time
import json
import io
import numpy as np
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# Carrega as variáveis do arquivo .env
load_dotenv()


def sincronizar_com_google_drive(caminho_planilha_local):
  """Sincroniza a planilha local com a pasta do Google Drive."""
  json_path = os.getenv("GOOGLE_CREDENTIALS_2")
  folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

  if not json_path or not os.path.exists(json_path):
    return

  try:
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file(
        json_path, scopes=scopes
    )
    service = build("drive", "v3", credentials=creds)

    nome_arquivo = os.path.basename(caminho_planilha_local)
    query = f"'{folder_id}' in parents and name = '{nome_arquivo}' and trashed = false"
    results = (
        service.files().list(q=query, fields="files(id, name)").execute()
    )
    arquivos = results.get("files", [])

    media = MediaFileUpload(
        caminho_planilha_local,
        mimetype=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )

    if arquivos:
      file_id = arquivos[0]["id"]
      service.files().update(fileId=file_id, media_body=media).execute()
    else:
      file_metadata = {"name": nome_arquivo, "parents": [folder_id]}
      service.files().create(
          body=file_metadata, media_body=media, fields="id"
      ).execute()
  except Exception as e:
    print(f"⚠️ Erro ao sincronizar com Google Drive: {e}")


@st.cache_data(ttl=300)
def carregar_dados():
    # 1. Credenciais do Streamlit Secrets
    creds_json = json.loads(st.secrets["google_credentials"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive_service = build('drive', 'v3', credentials=creds)

    # 2. ID da planilha no Google Drive
    # 2. ID da planilha no Google Drive
    file_id = "1pZUGLPLb9I17QZiYm4AzZHhWrkUe351f"

    # 3. Baixa o arquivo do Drive direto na memória
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)

    # 4. Lê a aba Resumo com o cabeçalho na linha correta
df_raw = pd.read_excel(fh, sheet_name="Resumo", header=1)

# Garante que não existam colunas com nomes duplicados
seen = {}
new_cols = []
for c in df_raw.columns:
    c_str = str(c).strip()
    if c_str in seen:
        seen[c_str] += 1
        new_cols.append(f"{c_str}_{seen[c_str]}")
    else:
        seen[c_str] = 0
        new_cols.append(c_str)
df_raw.columns = new_cols

    # 5. Trata e ajusta os nomes das colunas
    novos_nomes = []
    ultimo_grupo = ""
    for col in df_raw.columns:
        grupo = str(col[0]).strip()
        subgrupo = str(col[1]).strip()
        if not grupo.startswith("Unnamed"): ultimo_grupo = grupo
        else: grupo = ultimo_grupo
        if subgrupo.startswith("Unnamed"): subgrupo = ""
        
        nome_final = f"{grupo} - {subgrupo}" if (grupo and subgrupo and grupo != subgrupo) else (subgrupo or grupo)
        novos_nomes.append(nome_final)

    df_raw.columns = novos_nomes
    return df_raw


def main():
  # 1. Configuração da Página
  st.set_page_config(
      page_title="Painel Executivo CFO",
      layout="wide",
      initial_sidebar_state="expanded",
  )

  # 2. Sincronização automática
  caminho_planilha = "Inadimplência_faixa_fat.xlsx"
  if os.path.exists(caminho_planilha):
    sincronizar_com_google_drive(caminho_planilha)

  # 3. Estilização CSS Dark/Ciano
  st.markdown(
      """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
            header[data-testid="stHeader"] { visibility: hidden; }
            #MainMenu, footer { visibility: hidden !important; }
            html, body, [class*="css"], .stApp {
                font-family: 'Poppins', sans-serif !important;
                background-color: #041C2B !important;
                color: #FFFFFF !important;
            }
            div[data-testid="stMetricValue"] { color: #00E5FF !important; }
        </style>
        """,
      unsafe_allow_html=True,
  )

  # 4. Cabeçalho
  st.title("📊 Painel Executivo CFO")
  st.caption(
      "Análise Estratégica de Inadimplência e Faturamento | Atualização"
      " Automática"
  )

  # 5. Carregamento e exibição
  df = carregar_dados()

  if df is None or df.empty:
    st.error(
        f"A planilha '{caminho_planilha}' não foi encontrada ou está vazia."
    )
    return

  st.sidebar.header("🔍 Filtros de Análise")
  st.subheader("📋 Resumo do Perfil de Inadimplência")
  st.dataframe(df, use_container_width=True)


# 6. GATILHO AUTOMÁTICO E REFRESH A CADA 2 MINUTOS
if __name__ == "__main__":
  if st.runtime.exists():
    main()
    time.sleep(120)  # Aguarda 120 segundos
    st.rerun()  # Força o recarregamento do painel
  else:
    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

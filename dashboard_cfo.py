import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import re
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Painel Executivo CFO", layout="wide")

# 2. Estilização CSS 
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], .stApp, header, [data-testid="stHeader"] {
            font-family: 'Poppins', sans-serif !important;
            background-color: #041C2B !important;
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
            background-color: #041C2B !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        div[data-baseweb="select"] > div {
            background-color: #041C2B !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] span { color: #FFFFFF !important; }

        .stTabs [data-baseweb="tab-list"] { background-color: #041C2B !important; gap: 12px; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            padding: 10px 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
            color: #FFFFFF !important; font-weight: 500 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #00E2F4 !important; border-color: #00E2F4 !important;
        }
        .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
            color: #041C2B !important; font-weight: 700 !important;
        }

        .metric-card {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: 5px solid #00E2F4;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            height: 140px !important;
            display: flex; flex-direction: column; justify-content: space-between;
        }
        
        .metric-card-small {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid #00E2F4;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            height: 110px !important;
            display: flex; flex-direction: column; justify-content: space-between;
        }

        .metric-card-mini {
            background-color: rgba(94, 22, 255, 0.1) !important;
            border: 1px solid rgba(94, 22, 255, 0.3);
            border-left: 4px solid #5E16FF;
            border-radius: 8px;
            padding: 8px 15px;
            display: flex; flex-direction: column; justify-content: center;
        }
        .card-label-mini { font-size: 0.75rem; color: rgba(255, 255, 255, 0.7); margin-bottom: 2px; text-transform: none !important;}
        .card-value-mini { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin: 0; }

        .metric-card-orange { border-left-color: #FF601F !important; }
        .metric-card-lime { border-left-color: #D8FE00 !important; }
        .metric-card-purple { border-left-color: #5E16FF !important; }

        .card-header {
            font-size: 1rem; font-weight: 600; color: #FFFFFF !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            padding-bottom: 4px; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        
        .card-label { 
            font-size: 0.8rem; 
            color: rgba(255, 255, 255, 0.7) !important; 
            margin-top: 4px; 
            font-weight: 600; 
            text-transform: none !important; 
        }
        
        .card-value { font-size: 1.4rem; font-weight: 700; color: #FFFFFF !important; margin: 0; }
        .card-value-small { font-size: 1.2rem; font-weight: 700; color: #FFFFFF !important; margin: 0; }

        [data-testid="stDataFrame"] { background-color: #041C2B !important; border-radius: 8px; padding: 5px; }
        button, svg, [data-testid="stHeader"] * { color: #FFFFFF !important; fill: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# 3. Funções Auxiliares 
def padronizar_nome(texto):
    t = str(texto).strip()
    t = re.sub(r'\.\d+$', '', t).strip()
    t = re.sub(r'(?i)clique.{0,2}g\b', 'G-Click', t)
    t = re.sub(r'(?i)g.{0,2}click\b', 'G-Click', t)
    t = t.replace('CLIQUE G', 'G-Click')
    t = t.replace('CLIQUEG', 'G-Click')
    t = t.replace('Clique G', 'G-Click')
    t = t.replace('clique g', 'G-Click')
    return t.strip()

def letra_para_indice(letra):
    num = 0
    for c in letra.upper(): num = num * 26 + (ord(c) - ord('A') + 1)
    return num - 1 

def formatar_valor(valor, tipo):
    if pd.isna(valor): return "-"
    try:
        val = float(valor)
        if tipo == 'moeda': return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elif tipo == 'perc': return f"{val * 100:,.2f}%".replace('.', ',')
        elif tipo == 'num': return f"{val:,.0f}".replace(',', '.')
        else: return str(valor)
    except:
        return str(valor)

def extrair_valor_inteligente(df_base, col_nome, deve_calcular_media=False):
    if col_nome not in df_base.columns:
        return 0
    
    serie = pd.to_numeric(df_base[col_nome], errors='coerce').dropna()
    if len(serie) == 0:
        return 0
        
    if deve_calcular_media and len(serie) > 1:
        return serie.mean()
    else:
        return serie.iloc[0]

# 4. Leitura dos Dados
@st.cache_data(ttl=0)
def carregar_dados():
    caminho_planilha = r"G:\Drives compartilhados\Financeiro\Perfil_Inadimplência\Inadimplência_faixa_fat.xlsx"
    df_raw = pd.read_excel(caminho_planilha, sheet_name="Resumo", header=[1, 2])
    
    novos_nomes = []
    ultimo_grupo = ""
    for col in df_raw.columns:
        grupo = str(col[0]).strip()
        subgrupo = str(col[1]).strip()
        if not grupo.startswith('Unnamed'): ultimo_grupo = grupo
        else: grupo = ultimo_grupo
        if subgrupo.startswith('Unnamed'): subgrupo = ""
        
        nome_final = f"{grupo} - {subgrupo}" if (grupo and subgrupo and grupo != subgrupo) else (subgrupo or grupo)
        novos_nomes.append(nome_final)
        
    seen = {}
    unique_cols = []
    for col in novos_nomes:
        if col in seen:
            seen[col] += 1
            unique_cols.append(f"{col}.{seen[col]}")
        else:
            seen[col] = 0
            unique_cols.append(col)
    
    df_raw.columns = unique_cols
    return df_raw

try:
    st.cache_data.clear()
    df_raw = carregar_dados()
    
    cols_moeda = ['C','E','F','G','H','I','J','K','L','N','O','P','Q','R','S','T','U','V','X','Y','AA','AB','AC','AD']
    cols_perc = ['AF','AG','AI','AJ','AK','AL','AR','AS','AT','AU','AW','AX','AY','AZ','BB','BC','BD','BE']
    cols_num = ['AM','AN','AO','AP']
    
    valid_moeda = [df_raw.columns[letra_para_indice(l)] for l in cols_moeda if letra_para_indice(l) < len(df_raw.columns)]
    valid_perc = [df_raw.columns[letra_para_indice(l)] for l in cols_perc if letra_para_indice(l) < len(df_raw.columns)]
    valid_num = [df_raw.columns[letra_para_indice(l)] for l in cols_num if letra_para_indice(l) < len(df_raw.columns)]
    
    col_mes = df_raw.columns[letra_para_indice('B')]
    df = df_raw.rename(columns={col_mes: 'Mês'}).dropna(subset=['Mês']).copy()
    
    df['Data_Real'] = pd.to_datetime(df['Mês'], errors='coerce')
    df = df.sort_values(by='Data_Real')
    
    df['Mês_Formatado'] = df['Data_Real'].dt.strftime('%b/%Y')
    df['Mês_Formatado'] = df['Mês_Formatado'].fillna(df['Mês'].astype(str))
    df['Dia_Formatado'] = df['Data_Real'].dt.strftime('%d/%m/%Y')

    idx_col_s = letra_para_indice('S')

    # --- FILTROS NA BARRA LATERAL ---
    st.sidebar.title("Filtros Executivos")
    
    lista_meses = [m for m in df['Mês_Formatado'].unique().tolist() if str(m).strip() != 'nan']
    mes_selecionado = st.sidebar.selectbox("1. Selecione o Mês:", lista_meses, index=len(lista_meses)-1 if lista_meses else 0)
    
    modo_visao = st.sidebar.radio("2. Visão do Período:", ["Mês Completo (Média/Consolidado)", "Dia Específico"])
    
    df_mes = df[df['Mês_Formatado'] == mes_selecionado]
    
    if modo_visao == "Dia Específico":
        lista_dias = [d for m, d in zip(df_mes['Mês_Formatado'], df_mes['Dia_Formatado']) if str(d).strip() != 'nan']
        lista_dias_unicos = list(dict.fromkeys(lista_dias))
        
        dia_selecionado = st.sidebar.selectbox("3. Escolha o Dia:", lista_dias_unicos, index=0)
        df_filtrado = df_mes[df_mes['Dia_Formatado'] == dia_selecionado]
        subtitulo_periodo = f"Dia **{dia_selecionado}**"
        modo_media = False 
    else:
        df_filtrado = df_mes
        subtitulo_periodo = f"Consolidado/Média do Mês — **{mes_selecionado}**"
        modo_media = True 

    st.title("📊 Painel de Controle de Inadimplência")
    
    col_titulo, col_dica = st.columns([5, 1])
    with col_titulo:
        st.markdown(f"Acompanhamento Estratégico — {subtitulo_periodo}")
    with col_dica:
        components.html(
            """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
                body { margin: 0; background-color: #041C2B; display: flex; justify-content: flex-end; align-items: center; height: 100vh; overflow: hidden; }
                .btn-fullscreen {
                    background-color: transparent;
                    color: #00E2F4;
                    border: 1px solid #00E2F4;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    font-family: 'Poppins', sans-serif;
                    font-size: 0.85rem;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .btn-fullscreen:hover {
                    background-color: #00E2F4;
                    color: #041C2B;
                }
            </style>
            <button class="btn-fullscreen" onclick="toggleFullScreen()" title="Expandir painel para tela inteira">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                </svg>
                Tela Cheia
            </button>
            <script>
            function toggleFullScreen() {
                try {
                    var doc = window.parent.document;
                    var docEl = doc.documentElement;
                    var requestFullScreen = docEl.requestFullscreen || docEl.webkitRequestFullScreen || docEl.mozRequestFullScreen || docEl.msRequestFullscreen;
                    var cancelFullScreen = doc.exitFullscreen || doc.webkitExitFullscreen || doc.mozCancelFullScreen || doc.msExitFullscreen;
                    
                    if(!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
                        requestFullScreen.call(docEl);
                    } else {
                        cancelFullScreen.call(doc);
                    }
                } catch (e) {
                    alert("Por motivos de segurança corporativa, o seu navegador exige que você aperte a tecla F11 para entrar em tela cheia.");
                }
            }
            </script>
            """,
            height=45
        )
        
    st.divider()

    aba1, aba2, aba3, aba4 = st.tabs(["📊 Resumo", "🗂️ Visão Geral", "📋 Tabela de Dados Completa", "📈 Gráficos Históricos"])

    # --- ABA 1: RESUMO ---
    with aba1:
        col_tit, col_mini1, col_mini2 = st.columns([5, 2, 2])
        
        with col_tit:
            st.subheader(f"Visão Executiva Consolidada")
            
        try:
            col_af = df.columns[letra_para_indice('AF')]
            col_ag = df.columns[letra_para_indice('AG')]
            
            val_af = extrair_valor_inteligente(df_filtrado, col_af, deve_calcular_media=modo_media)
            val_ag = extrair_valor_inteligente(df_filtrado, col_ag, deve_calcular_media=modo_media)
            
            if "omie" in padronizar_nome(col_ag).lower():
                val_omie_perc = val_ag
                val_gclick_perc = val_af
            else:
                val_omie_perc = val_af
                val_gclick_perc = val_ag
        except Exception:
            val_omie_perc = 0
            val_gclick_perc = 0

        with col_mini1:
            st.markdown(f'<div class="metric-card-mini"><div><div class="card-label-mini">Inadimplência - Omie</div><div class="card-value-mini">{formatar_valor(val_omie_perc, "perc")}</div></div></div>', unsafe_allow_html=True)
        with col_mini2:
            st.markdown(f'<div class="metric-card-mini"><div><div class="card-label-mini">Inadimplência - G-Click</div><div class="card-value-mini">{formatar_valor(val_gclick_perc, "perc")}</div></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns(3)
        
        fat_gclick_col = [c for c in df.columns if "G-Click total mês anterior" in padronizar_nome(c)]
        fat_omie_col = [c for c in df.columns if "Valor faturado - Omie" in padronizar_nome(c)]
        fat_total_col = [c for c in df.columns if "Fat. Total Mês Anterior" in padronizar_nome(c)]
        
        fat_gclick_val = extrair_valor_inteligente(df_filtrado, fat_gclick_col[0], deve_calcular_media=False) if fat_gclick_col else 0
        fat_omie_val = extrair_valor_inteligente(df_filtrado, fat_omie_col[0], deve_calcular_media=False) if fat_omie_col else 0
        fat_total_val = extrair_valor_inteligente(df_filtrado, fat_total_col[0], deve_calcular_media=False) if fat_total_col else 0
        
        with col_c1:
            st.markdown(f'<div class="metric-card"><div><div class="card-header">🏢 G-Click — Faturamento</div><div class="card-label">Fat. Total Mês Anterior</div></div><div class="card-value">{formatar_valor(fat_gclick_val, "moeda")}</div></div>', unsafe_allow_html=True)
        with col_c2:
            st.markdown(f'<div class="metric-card"><div><div class="card-header">🏢 Omie — Faturamento</div><div class="card-label">Fat. Total Mês Anterior</div></div><div class="card-value">{formatar_valor(fat_omie_val, "moeda")}</div></div>', unsafe_allow_html=True)
        with col_c3:
            st.markdown(f'<div class="metric-card metric-card-lime"><div><div class="card-header">📈 Faturamento Consolidado</div><div class="card-label">Total Geral</div></div><div class="card-value">{formatar_valor(fat_total_val, "moeda")}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("⚠️ Inadimplência & Atrasos por Empresa")
        col_a1, col_a2, col_a3 = st.columns(3)
        
        atraso_gclick_col = [c for c in df.columns if "Valor em atraso por empresa" in padronizar_nome(c) and "G-Click" in padronizar_nome(c)]
        atraso_omie_col = [c for c in df.columns if "Valor em atraso por empresa" in padronizar_nome(c) and "Omie" in padronizar_nome(c)]
        atraso_total_col = [c for c in df.columns if "Valor em Atraso - TOTAL" in padronizar_nome(c)]
        
        atraso_gclick_val = extrair_valor_inteligente(df_filtrado, atraso_gclick_col[0], deve_calcular_media=modo_media) if atraso_gclick_col else 0
        atraso_omie_val = extrair_valor_inteligente(df_filtrado, atraso_omie_col[0], deve_calcular_media=modo_media) if atraso_omie_col else 0
        atraso_total_val = extrair_valor_inteligente(df_filtrado, atraso_total_col[0], deve_calcular_media=modo_media) if atraso_total_col else 0

        txt_rotulo = "Montante Médio" if modo_media else "Montante do Dia"
        with col_a1:
            st.markdown(f'<div class="metric-card metric-card-orange"><div><div class="card-header">G-Click — Atraso</div><div class="card-label">{txt_rotulo}</div></div><div class="card-value">{formatar_valor(atraso_gclick_val, "moeda")}</div></div>', unsafe_allow_html=True)
        with col_a2:
            st.markdown(f'<div class="metric-card metric-card-orange"><div><div class="card-header">Omie — Atraso</div><div class="card-label">{txt_rotulo}</div></div><div class="card-value">{formatar_valor(atraso_omie_val, "moeda")}</div></div>', unsafe_allow_html=True)
        with col_a3:
            st.markdown(f'<div class="metric-card metric-card-orange"><div><div class="card-header">Total Consolidado</div><div class="card-label">{txt_rotulo}</div></div><div class="card-value">{formatar_valor(atraso_total_val, "moeda")}</div></div>', unsafe_allow_html=True)


    # --- ABA 2: VISÃO GERAL EM CARTÕES ---
    with aba2:
        st.subheader("Painel Completo de Indicadores")
        colunas_para_cartoes = valid_moeda + valid_perc + valid_num
        grupos_dict = {}
        for col in colunas_para_cartoes:
            if col not in df_filtrado.columns: continue
            
            grupo_raw = col.split(" - ")[0] if " - " in col else "Indicadores Gerais"
            sub_raw = " - ".join(col.split(" - ")[1:]) if " - " in col else col
            
            grupo_display = padronizar_nome(grupo_raw)
            sub_display = padronizar_nome(sub_raw)
            if grupo_display not in grupos_dict: grupos_dict[grupo_display] = []
            grupos_dict[grupo_display].append((col, sub_display))

        st.markdown(f"<h4 style='color: #00E2F4; margin-top: 20px; padding-bottom: 5px;'>Valor Faturado</h4>", unsafe_allow_html=True)
        
        layout_vf = [
            [("Fat. Total Mês Anterior", "Valor Faturado Total Mês Anterior"), ("Omie", "Omie"), ("Treinamento Omie", "Treinamento Omie")],
            [("Treinamento G-Click", "Treinamento GClick"), ("Mensalidade Omie", "Mensalidade Omie"), ("Mensalidade G-Click", "Mensalidade GClick")],
            [("Até 300", "Até 300"), ("De 300,01 até 600", "De 300,01 até 600"), ("Acima de 600,01", "Acima de 600,01")]
        ]
        
        for linha in layout_vf:
            cols = st.columns(3)
            for i, (busca, titulo_exibicao) in enumerate(linha):
                col_nome = None
                for c in df_filtrado.columns:
                    c_padrao = padronizar_nome(c).lower()
                    if "valor faturado" in c_padrao:
                        if busca == "Omie":
                            if c_padrao.endswith("omie") and "treinamento" not in c_padrao and "mensalidade" not in c_padrao:
                                col_nome = c
                                break
                        elif busca.lower() in c_padrao:
                            col_nome = c
                            break
                
                if col_nome and col_nome in df_filtrado.columns:
                    val = extrair_valor_inteligente(df_filtrado, col_nome, deve_calcular_media=False)
                    tipo_formato = 'texto'
                    if col_nome in valid_moeda: tipo_formato = 'moeda'
                    elif col_nome in valid_perc: tipo_formato = 'perc'
                    elif col_nome in valid_num: tipo_formato = 'num'
                    val_formatado = formatar_valor(val, tipo_formato)
                    
                    cor_borda = "metric-card-small"
                    if tipo_formato == 'perc': cor_borda = "metric-card-small metric-card-purple"
                    elif tipo_formato == 'num': cor_borda = "metric-card-small metric-card-lime"
                    
                    with cols[i]:
                        st.markdown(f"""
                            <div class="{cor_borda}">
                                <div class="card-label">{titulo_exibicao}</div>
                                <div class="card-value-small">{val_formatado}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    with cols[i]:
                        st.write("") 
        
        grupo_vf_key = next((k for k in grupos_dict.keys() if "valor faturado" in k.lower()), None)
        if grupo_vf_key:
            del grupos_dict[grupo_vf_key]
        
        grupos_faturamento = {}
        grupos_atraso = {}
        
        for grupo, itens in grupos_dict.items():
            g_lower = grupo.lower()
            if "atraso" in g_lower or "inadimpl" in g_lower:
                grupos_atraso[grupo] = itens
            else:
                grupos_faturamento[grupo] = itens

        def renderizar_cartoes(dicionario_de_grupos):
            for grupo, itens in dicionario_de_grupos.items():
                st.markdown(f"<h4 style='color: #00E2F4; margin-top: 20px; padding-bottom: 5px;'>{grupo}</h4>", unsafe_allow_html=True)
                
                itens_unicos = {}
                for col_nome, sub_display in itens:
                    idx_col = df_raw.columns.get_loc(col_nome) if col_nome in df_raw.columns else 0
                    calcular_media = (idx_col >= idx_col_s) and modo_media
                    
                    val = extrair_valor_inteligente(df_filtrado, col_nome, deve_calcular_media=calcular_media)
                    
                    if sub_display in itens_unicos:
                        val_antigo = itens_unicos[sub_display]['val']
                        if (pd.isna(val_antigo) or val_antigo == 0) and not (pd.isna(val) or val == 0):
                            itens_unicos[sub_display] = {'col': col_nome, 'val': val}
                    else:
                        itens_unicos[sub_display] = {'col': col_nome, 'val': val}
                
                cols = st.columns(4) 
                for i, (sub_display, dados) in enumerate(itens_unicos.items()):
                    col_nome = dados['col']
                    val = dados['val']
                    tipo_formato = 'texto'
                    if col_nome in valid_moeda: tipo_formato = 'moeda'
                    elif col_nome in valid_perc: tipo_formato = 'perc'
                    elif col_nome in valid_num: tipo_formato = 'num'
                    val_formatado = formatar_valor(val, tipo_formato)
                    
                    cor_borda = "metric-card-small"
                    if tipo_formato == 'perc': cor_borda = "metric-card-small metric-card-purple"
                    elif tipo_formato == 'num': cor_borda = "metric-card-small metric-card-lime"
                    
                    with cols[i % 4]:
                        st.markdown(f"""
                            <div class="{cor_borda}">
                                <div class="card-label">{sub_display}</div>
                                <div class="card-value-small">{val_formatado}</div>
                            </div>
                        """, unsafe_allow_html=True)

        renderizar_cartoes(grupos_faturamento)
        st.markdown("---")
        tit_atraso = "⚠️ Indicadores de Inadimplência e Atrasos (Média do Mês)" if modo_media else "⚠️ Indicadores de Inadimplência e Atrasos (Foto do Dia)"
        st.markdown(f"<h3 style='color: #FF601F; margin-top: 10px; padding-bottom: 5px;'>{tit_atraso}</h3>", unsafe_allow_html=True)
        renderizar_cartoes(grupos_atraso)


    # --- ABA 3: TABELA DE DADOS COMPLETA ---
    with aba3:
        st.subheader("Visão em Tabela Formatada (Registros Diários)")
        
        colunas_tabela = ['Mês'] + valid_moeda + valid_perc + valid_num
        colunas_tabela_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
        
        df_exibicao = df_filtrado[colunas_tabela_existentes].copy()
        
        for col in valid_moeda:
            if col in df_exibicao.columns: df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_valor(x, 'moeda'))
        for col in valid_perc:
            if col in df_exibicao.columns: df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_valor(x, 'perc'))
        for col in valid_num:
            if col in df_exibicao.columns: df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_valor(x, 'num'))
            
        nomes_padronizados = [padronizar_nome(c) for c in df_exibicao.columns]
        
        nomes_finais_unicos = []
        contador = {}
        for nome in nomes_padronizados:
            if nome in contador:
                contador[nome] += 1
                nomes_finais_unicos.append(nome + "\u200B" * contador[nome]) 
            else:
                contador[nome] = 0
                nomes_finais_unicos.append(nome)
                
        df_exibicao.columns = nomes_finais_unicos
            
        st.dataframe(df_exibicao, use_container_width=True)

    # --- ABA 4: GRÁFICOS HISTÓRICOS (TEMA DARK AZUL-ESCURO INTEGRADO) ---
    with aba4:
        filtro_grafico = st.selectbox("📅 Selecione o Período para Análise Gráfica:", ["Todos os meses e anos"] + lista_meses)
        
        if filtro_grafico == "Todos os meses e anos":
            df_graf = df.copy()
        else:
            df_graf = df[df['Mês_Formatado'] == filtro_grafico].copy()
            
        df_graf = df_graf.set_index('Mês_Formatado')

        # Tema escuro em harmonia com o fundo #041C2B
        def aplicar_tema_dark(fig, title_text):
            fig.update_layout(
                title=dict(
                    text=f"<u><b>{title_text}</b></u>", 
                    x=0.5, 
                    font=dict(size=20, color='#FFFFFF', family='Arial')
                ),
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font_color='#FFFFFF', 
                legend=dict(
                    title_text='', 
                    orientation="h", 
                    yanchor="top", 
                    y=-0.35, 
                    xanchor="center", 
                    x=0.5,
                    bordercolor="rgba(255,255,255,0.3)", 
                    borderwidth=1,
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#FFFFFF", size=12) 
                ),
                xaxis=dict(showgrid=False, title="", showline=True, linecolor='rgba(255,255,255,0.3)', tickfont=dict(color='#FFFFFF')),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', ticksuffix="%", title="", zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', tickfont=dict(color='#FFFFFF')),
                hovermode="x unified",
                margin=dict(l=40, r=20, t=70, b=150), 
            )
            fig.update_traces(hovertemplate='Média: %{y:.2f}%')
            return fig

        graf_col1, graf_col2 = st.columns(2)
        
        with graf_col1:
            cols_company = [c for c in df_graf.columns if "% do faturado por empresa" in padronizar_nome(c) and ("Omie" in padronizar_nome(c) or "G-Click" in padronizar_nome(c))]
            if cols_company:
                rename_dict = {c: "Omie" if "Omie" in padronizar_nome(c) else "G-Click" for c in cols_company}
                df_c1 = df_graf[cols_company].rename(columns=rename_dict).apply(pd.to_numeric, errors='coerce') * 100
                df_c1 = df_c1.loc[:, ~df_c1.columns.duplicated()] 
                cores_c1 = ['#00E2F4', '#FF601F'] # Ciano e Laranja
                st.plotly_chart(aplicar_tema_dark(px.line(df_c1, color_discrete_sequence=cores_c1), "Delinquency - Per Company (%)"), use_container_width=True)

            cols_delinq = [c for c in df_graf.columns if "Taxa da inadimplência - Na Faixa" in padronizar_nome(c) and "TOTAL" not in padronizar_nome(c).upper()]
            if cols_delinq:
                rename_dict3 = {c: padronizar_nome(c).split("-")[-1].strip() for c in cols_delinq}
                df_c3 = df_graf[cols_delinq].rename(columns=rename_dict3).apply(pd.to_numeric, errors='coerce') * 100
                df_c3 = df_c3.loc[:, ~df_c3.columns.duplicated()]
                cores_c3 = ['#00E2F4', '#A5A5A5', '#FF601F'] 
                st.plotly_chart(aplicar_tema_dark(px.area(df_c3, color_discrete_sequence=cores_c3), "Delinquency (%)"), use_container_width=True)

        with graf_col2:
            cols_aging = [c for c in df_graf.columns if "Distribuição da inadimplência" in padronizar_nome(c) and "TOTAL" not in padronizar_nome(c).upper()]
            if cols_aging:
                rename_dict2 = {c: padronizar_nome(c).split("-")[-1].strip() for c in cols_aging}
                df_c2 = df_graf[cols_aging].rename(columns=rename_dict2).apply(pd.to_numeric, errors='coerce') * 100
                df_c2 = df_c2.loc[:, ~df_c2.columns.duplicated()]
                cores_c2 = ['#00E2F4', '#FF601F', '#A5A5A5'] 
                st.plotly_chart(aplicar_tema_dark(px.area(df_c2, color_discrete_sequence=cores_c2), "Delinquency Aging"), use_container_width=True)

            cols_prod = [c for c in df_graf.columns if "% do faturado por produto" in padronizar_nome(c)]
            if cols_prod:
                rename_dict4 = {c: padronizar_nome(c).split("-")[-1].strip() for c in cols_prod}
                df_c4 = df_graf[cols_prod].rename(columns=rename_dict4).apply(pd.to_numeric, errors='coerce') * 100
                df_c4 = df_c4.loc[:, ~df_c4.columns.duplicated()]
                cores_c4 = ['#00E2F4', '#FF601F', '#A5A5A5', '#D8FE00'] 
                st.plotly_chart(aplicar_tema_dark(px.line(df_c4, color_discrete_sequence=cores_c4), "Delinquency - Product (%)"), use_container_width=True)

except Exception as e:
    st.error(f"Erro no processamento dos dados ou formatação: {e}")

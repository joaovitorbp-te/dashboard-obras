import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
import os

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO VISUAL
# ---------------------------------------------------------
st.markdown("""
<style>
    /* FORÇAR ALINHAMENTO NO TOPO */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Remove a margem extra do título */
    h1 {
        padding-top: 0rem !important;
        margin-top: -1rem !important;
    }

    /* --- LAYOUT DOS KPIS (CABEÇALHO) --- */
    .kpi-card {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 20px 15px;
        height: 100%;
        display: flex; flex-direction: column; justify-content: space-between; align-items: center;
        text-align: center;
        min-height: 130px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .kpi-title { 
        color: #8b949e; font-size: 0.8rem; text-transform: uppercase; 
        letter-spacing: 1px; font-weight: 600; margin-bottom: 8px;
    }
    
    .kpi-val { 
        font-size: 1.8rem; font-weight: 800; color: white; 
        font-family: "Source Sans Pro", sans-serif; margin-bottom: 8px;
    }
    
    .kpi-sub { 
        font-size: 0.75rem; color: #8b949e; width: 100%;
        border-top: 1px solid #21262d;
        padding-top: 8px; margin-top: auto;
        display: flex; justify-content: space-around;
    }
    
    .txt-green { color: #3fb950; font-weight: bold; }
    .txt-red { color: #da3633; font-weight: bold; }
    .txt-blue { color: #58a6ff; font-weight: bold; }
    .txt-purple { color: #a371f7; font-weight: bold; }
    .txt-orange { color: #d29922; font-weight: bold; }

    /* --- CSS DOS CARDS DE PROJETO --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 0px !important; transition: transform 0.2s;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #58a6ff; transform: translateY(-2px);
    }
    .tile-header { padding: 15px 15px 10px 15px; }
    .tile-title { color: white; font-weight: 700; font-size: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
    .tile-sub { color: #8b949e; font-size: 0.75rem; }
    .data-strip { background-color: #0d1117; border-top: 1px solid #21262d; border-bottom: 1px solid #21262d; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
    .data-col { display: flex; flex-direction: column; align-items: center; width: 25%; }
    .data-col:not(:last-child) { border-right: 1px solid #30363d; }
    .data-lbl { font-size: 0.6rem; color: #8b949e; text-transform: uppercase; margin-bottom: 2px; }
    .data-val { font-size: 0.85rem; font-weight: 700; color: #e6edf3; }
    
    .tile-footer { padding: 10px 15px; }
    
    /* Alinhamento da linha de rodapé (Status --- %) */
    .footer-row { display: flex; justify-content: space-between; align-items: center; }
    
    .progress-track { background-color: #21262d; height: 4px; border-radius: 2px; width: 100%; margin-bottom: 10px; overflow: hidden; }
    .badge-status { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; }
    .footer-pct { font-size: 0.8rem; font-weight: 700; }
    
    div[data-testid="stVerticalBlockBorderWrapper"] button {
        background-color: transparent; color: #58a6ff; border: 1px solid #30363d; border-radius: 4px;
        font-size: 0.65rem !important; padding: 0px 0px !important; height: 24px !important; min-height: 24px !important; line-height: 1 !important; margin: 0; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DADOS E TRATAMENTO (GOOGLE DRIVE .XLSX)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        # Autenticação via Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        # Procura o arquivo pelo nome
        results = service.files().list(
            q="name='dados_dashboard_obras.xlsx' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            st.error("Arquivo 'dados_dashboard_obras.xlsx' não encontrado no Google Drive.")
            return None
            
        file_id = files[0]['id']
        
        # Baixa o arquivo para a memória
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        file_io.seek(0)
        
        # Lê como Excel
        df = pd.read_excel(file_io)
        return df

    except Exception as e:
        st.error(f"Erro na conexão com o Google Drive: {e}")
        return None

df_raw = load_data()

if df_raw is None:
    st.stop()

# --- LIMPEZA DE DADOS ---
# Forçamos a conversão de IDs para String para evitar erro de comparação
df_raw['Projeto'] = df_raw['Projeto'].astype(str)

def clean_google_number(x):
    if isinstance(x, (int, float)):
        return float(x)
    if x is None:
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
    try:
        s = s.replace('R$', '').replace('%', '').replace(' ', '')
        s = s.replace('.', '').replace(',', '.')
        return float(s)
    except:
        return 0.0

cols_numericas = [
    'Vendido', 'Faturado', 'Mat_Real', 'Desp_Real', 'HH_Real_Vlr', 'Impostos', 'Mat_Orc',
    'HH_Orc_Qtd', 'HH_Real_Qtd', 'Conclusao_%' 
]

for col in cols_numericas:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].apply(clean_google_number)
    else:
        df_raw[col] = 0.0

# --- FORMATAÇÃO ---
def format_brl_full(valor):
    if pd.isna(valor): return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_brl_short(valor):
    if pd.isna(valor): return "R$ 0"
    if valor >= 1_000_000: return f"R$ {valor/1_000_000:.1f}M".replace(".", ",")
    elif valor >= 1_000: return f"R$ {valor/1_000:.1f}k".replace(".", ",")
    else: return f"R$ {valor:,.0f}".replace(",", ".")

# ---------------------------------------------------------
# 3. LÓGICA DE NEGÓCIO (AJUSTADA - PREFIXO 4 DÍGITOS)
# ---------------------------------------------------------

# IDs de Custo Interno (Busca qualquer coisa que comece com...)
PREFIXOS_ADM = ("5009", "5010", "5011")

# Separação dos DataFrames usando startswith (tupla)
mask_adm = df_raw['Projeto'].str.startswith(PREFIXOS_ADM)
df_adm = df_raw[mask_adm].copy()
df_obras = df_raw[~mask_adm].copy()

# ========================================================
# CÁLCULO CUSTOS INTERNOS (Duplicado de Dados & Insights)
# ========================================================
# 1. Garantir que as colunas são numéricas e sem vazios
cols_soma = ['Mat_Real', 'Desp_Real', 'HH_Real_Vlr']
for col in cols_soma:
    if col in df_adm.columns:
        df_adm[col] = pd.to_numeric(df_adm[col], errors='coerce').fillna(0)

# 2. Fórmula exata: Mat + Desp + HH (Sem Impostos)
custo_adm_total = (df_adm['Mat_Real'] + df_adm['Desp_Real'] + df_adm['HH_Real_Vlr']).sum()
# ========================================================

# Função auxiliar para o resto das obras (mantida com impostos para obras de venda)
def get_custo_total_row_obras(row):
    return row['Mat_Real'] + row['Desp_Real'] + row['HH_Real_Vlr'] + row['Impostos']

# Cálculos Macro
status_venda = ['Não iniciado', 'Em andamento', 'Finalizado', 'Apresentado']
df_carteira_total = df_obras[df_obras['Status'].isin(status_venda)]
valor_vendido_total = df_carteira_total['Vendido'].sum()

df_concluido = df_obras[df_obras['Status'].isin(['Finalizado', 'Apresentado'])]
valor_concluido = df_concluido['Vendido'].sum()
valor_faturado_total = df_obras['Faturado'].sum()

overhead_pct = (custo_adm_total / valor_vendido_total * 100) if valor_vendido_total > 0 else 0

# Cálculos de Margem
def get_margem_ponderada(df_in):
    if df_in.empty: return 0.0
    venda = df_in['Vendido'].sum()
    custo = df_in.apply(get_custo_total_row_obras, axis=1).sum()
    return ((venda - custo) / venda * 100) if venda > 0 else 0

mg_geral = get_margem_ponderada(df_obras)
mg_concluida = get_margem_ponderada(df_concluido)

custo_obras_total = df_obras.apply(get_custo_total_row_obras, axis=1).sum()
lucro_bruto_total = valor_vendido_total - custo_obras_total
lucro_liquido_final = lucro_bruto_total - custo_adm_total
mg_liquida_pos_adm = (lucro_liquido_final / valor_vendido_total * 100) if valor_vendido_total > 0 else 0

df_aberto = df_obras[df_obras['Status'].isin(['Em andamento', 'Não iniciado'])]
qtd_aberto = len(df_aberto)
qtd_total = len(df_obras) 

# --- CARREGAR METAS (CONFIG) ---
def load_config():
    default_data = {"meta_vendas": 5000000.0, "meta_margem": 25.0, "meta_custo_adm": 5.0}
    if not os.path.exists("config.json"):
        with open("config.json", "w") as f:
            json.dump(default_data, f)
        return default_data
    
    with open("config.json", "r") as f:
        data = json.load(f)
        if "meta_custo_adm" not in data: data["meta_custo_adm"] = 5.0
        return data

config = load_config()
META_VENDAS = float(config["meta_vendas"])
META_MARGEM_BRUTA = float(config["meta_margem"])
META_CUSTO_ADM = float(config["meta_custo_adm"])
META_MARGEM_LIQUIDA = META_MARGEM_BRUTA - META_CUSTO_ADM

# ---------------------------------------------------------
# 4. INTERFACE
# ---------------------------------------------------------
st.title("Gestão da Carteira")

# LINHA 1 (3 Colunas) - KPIS GRANDES (Formatação COMPLETA)
row1_c1, row1_c2, row1_c3 = st.columns(3)

pct_meta_venda = (valor_vendido_total / META_VENDAS * 100)
with row1_c1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #58a6ff;">
        <div class="kpi-title">Valor Vendido</div>
        <div class="kpi-val">{format_brl_full(valor_vendido_total)}</div>
        <div class="kpi-sub">
            <span>Meta: {pct_meta_venda:.0f}%</span>
            <span class="txt-blue">{format_brl_full(valor_faturado_total)} faturados</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

pct_concluido_carteira = (valor_concluido / valor_vendido_total * 100) if valor_vendido_total > 0 else 0
pct_meta_concluido = (valor_concluido / META_VENDAS * 100)
with row1_c2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #3fb950;">
        <div class="kpi-title">Valor Concluído</div>
        <div class="kpi-val">{format_brl_full(valor_concluido)}</div>
        <div class="kpi-sub">
            <span>Meta: {pct_meta_concluido:.0f}%</span>
            <span class="txt-green">{pct_concluido_carteira:.0f}% do total</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

cor_adm = "txt-red" if overhead_pct > META_CUSTO_ADM else "txt-orange"
with row1_c3:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #d29922;">
        <div class="kpi-title">Custos internos</div>
        <div class="kpi-val">{format_brl_full(custo_adm_total)}</div>
        <div class="kpi-sub">
            <span class="{cor_adm}" style="font-weight:bold">{overhead_pct:.1f}% do valor vendido</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# LINHA 2 (4 Colunas) - MARGENS
row2_c1, row2_c2, row2_c3, row2_c4 = st.columns(4)

cor_m_geral = "txt-green" if mg_geral >= META_MARGEM_BRUTA else "txt-red"
with row2_c1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #8b949e;">
        <div class="kpi-title">Margem total</div>
        <div class="kpi-val {cor_m_geral}">{mg_geral:.1f}%</div>
        <div class="kpi-sub">
            <span>Obras vendidas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

cor_m_conc = "txt-green" if mg_concluida >= META_MARGEM_BRUTA else "txt-red"
with row2_c2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #8b949e;">
        <div class="kpi-title">Margem concluída</div>
        <div class="kpi-val {cor_m_conc}">{mg_concluida:.1f}%</div>
        <div class="kpi-sub">
            <span>Obras concluidas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

cor_m_liq = "txt-green" if mg_liquida_pos_adm >= META_MARGEM_LIQUIDA else "txt-red"
with row2_c3:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #8b949e;">
        <div class="kpi-title">Margem líquida</div>
        <div class="kpi-val {cor_m_liq}">{mg_liquida_pos_adm:.1f}%</div>
        <div class="kpi-sub">
            <span>Descontado custos internos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with row2_c4:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #8b949e;">
        <div class="kpi-title">Orçamentos</div>
        <div class="kpi-val">{qtd_aberto} <span style='font-size:1.2rem; color:#8b949e'>/ {qtd_total}</span></div>
        <div class="kpi-sub">
            <span>Quantidade em aberto/total</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------
# 5. CARDS DE PROJETOS (TILES)
# ---------------------------------------------------------

def calcular_dados_extras(row):
    vendido = row['Vendido']
    custo = row['Mat_Real'] + row['Desp_Real'] + row['HH_Real_Vlr'] + row['Impostos']
    lucro = vendido - custo
    margem = (lucro / vendido * 100) if vendido > 0 else 0
    hh_orc, hh_real = row['HH_Orc_Qtd'], row['HH_Real_Qtd']
    hh_perc = (hh_real / hh_orc * 100) if hh_orc > 0 else 0
    fisico = row['Conclusao_%']
    critico = False
    
    if (margem < META_MARGEM_BRUTA and row['Status'] != 'Apresentado') or (hh_perc > fisico + 10):
        critico = True
    return pd.Series([margem, critico, hh_perc])

cols_extras = df_obras.apply(calcular_dados_extras, axis=1)
df_obras['Margem_%'] = cols_extras[0]
df_obras['E_Critico'] = cols_extras[1]
df_obras['HH_Progresso'] = cols_extras[2]

# --- BARRA DE FILTROS ---
col_filtro, col_sort_criterio, col_sort_ordem = st.columns([3, 1, 1])

with col_filtro:
    status_options = ["Não iniciado", "Em andamento", "Finalizado", "Apresentado"]
    status_selecionados = st.multiselect("Filtrar por:", options=status_options, default=status_options)

with col_sort_criterio:
    criterio_sort = st.selectbox("Ordenar por:", ["Projeto", "Valor Vendido", "Margem", "Andamento"])

with col_sort_ordem:
    direcao_sort = st.selectbox("Ordem:", ["Decrescente", "Crescente"])

if not status_selecionados:
    st.info("Selecione pelo menos um status acima.")
    st.stop() 

df_show = df_obras[df_obras['Status'].isin(status_selecionados)].copy()
eh_crescente = True if direcao_sort == "Crescente" else False
mapa_sort = {"Projeto": "Projeto", "Valor Vendido": "Vendido", "Margem": "Margem_%", "Andamento": "Conclusao_%"}
df_show = df_show.sort_values(by=mapa_sort[criterio_sort], ascending=eh_crescente)

st.write(f"**{len(df_show)}** projetos encontrados")
st.write("")

cols = st.columns(3)

for i, (index, row) in enumerate(df_show.iterrows()):
    with cols[i % 3]:
        pct = int(row['Conclusao_%'])
        status_raw = str(row['Status']).strip()
        
        if status_raw == "Finalizado": cor_t, bg_b, cl_b = "#3fb950", "rgba(63,185,80,0.2)", "#3fb950"
        elif status_raw == "Apresentado": cor_t, bg_b, cl_b = "#a371f7", "rgba(163,113,247,0.2)", "#a371f7"
        elif status_raw == "Em andamento": cor_t, bg_b, cl_b = "#d29922", "rgba(210,153,34,0.2)", "#e3b341"
        else: cor_t, bg_b, cl_b = "#da3633", "rgba(218,54,51,0.2)", "#f85149"

        cor_margem = "#da3633" if row['Margem_%'] < META_MARGEM_BRUTA else "#3fb950"
        
        hh_orc, hh_real = row['HH_Orc_Qtd'], row['HH_Real_Qtd']
        pct_horas = (hh_real / hh_orc * 100) if hh_orc > 0 else 0
        cor_horas = "#da3633" if pct_horas > 100 else "#e6edf3"
        
        mat_orc, mat_real = row['Mat_Orc'], row['Mat_Real']
        pct_mat = (mat_real / mat_orc * 100) if mat_orc > 0 else 0
        cor_mat = "#da3633" if pct_mat > 100 else "#e6edf3"
        
        # Formatação Abreviada (Short)
        valor_formatado = format_brl_short(row['Vendido'])
        
        with st.container(border=True):
            st.markdown(f"""
            <div class="tile-header" style="border-left: 3px solid {cor_t}">
                <div class="tile-title" title="{row['Projeto']}">{row['Projeto']} - {row['Descricao']}</div>
                <div class="tile-sub">{row['Cliente']} | {row['Cidade']}</div>
            </div>
            <div class="data-strip">
                <div class="data-col"><span class="data-lbl">Valor</span><span class="data-val">{valor_formatado}</span></div>
                <div class="data-col"><span class="data-lbl">Margem</span><span class="data-val" style="color: {cor_margem}">{row['Margem_%']:.0f}%</span></div>
                <div class="data-col"><span class="data-lbl">Horas</span><span class="data-val" style="color: {cor_horas}">{pct_horas:.0f}%</span></div>
                <div class="data-col"><span class="data-lbl">Mat</span><span class="data-val" style="color: {cor_mat}">{pct_mat:.0f}%</span></div>
            </div>
            <div class="tile-footer">
                <div class="progress-track"><div class="progress-fill" style="width: {pct}%; background-color: {cor_t};"></div></div>
                <div class="footer-row">
                    <span class="badge-status" style="background-color: {bg_b}; color: {cl_b}">{status_raw}</span>
                    <span class="footer-pct" style="color: {cl_b}">{pct}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_sp, col_btn = st.columns([2, 1])
            with col_btn:
                if st.button("Abrir ↗", key=f"btn_{row['Projeto']}", use_container_width=True):
                    st.session_state["projeto_foco"] = row['Projeto']
                    st.switch_page("painel_obra.py")

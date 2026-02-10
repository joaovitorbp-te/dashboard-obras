import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
import os

# ---------------------------------------------------------
# 1. ESTILO CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    
    /* --- ALINHAMENTO NO TOPO --- */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    h1 {
        padding-top: 0rem !important;
        margin-top: -1rem !important;
    }

    .js-plotly-plot .plotly .modebar {display: none !important;}

    /* --- LAYOUT DOS CARDS (KPIs) --- */
    .kpi-card {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 20px 15px;
        height: 100%;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        text-align: center;
        min-height: 120px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .kpi-title { 
        color: #8b949e; font-size: 0.8rem; text-transform: uppercase; 
        letter-spacing: 1px; font-weight: 600; margin-bottom: 10px;
    }
    
    .kpi-val { 
        font-size: 1.8rem; font-weight: 800; color: white; 
        font-family: "Source Sans Pro", sans-serif; margin: 0;
    }

    /* --- CABEÇALHO DO PROJETO --- */
    .header-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 20px;
        margin-top: 10px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .header-title { color: white; font-size: 1.5rem; font-weight: 700; margin: 0; line-height: 1.2; }
    .header-subtitle { color: #8b949e; font-size: 0.9rem; margin-top: 8px; }
    .header-status { 
        font-weight: 700; padding: 6px 14px; border-radius: 6px; 
        color: white; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;
    }

    /* Cores Auxiliares */
    .txt-green { color: #3fb950; font-weight: bold; }
    .txt-red { color: #da3633; font-weight: bold; }
    .txt-blue { color: #58a6ff; font-weight: bold; }
    .txt-orange { color: #d29922; font-weight: bold; }
    .txt-purple { color: #a371f7; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FUNÇÕES E DADOS (GOOGLE DRIVE .XLSX)
# ---------------------------------------------------------
def format_currency(value):
    if pd.isna(value): return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(value):
    if pd.isna(value): return "0,0%"
    return f"{value:.1f}%".replace(".", ",")

@st.cache_data(ttl=30)
def load_data():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            q="name='dados_dashboard_obras.xlsx' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            return None
            
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        file_io.seek(0)
        df = pd.read_excel(file_io)
        return df
    except Exception as e:
        return None

df_raw = load_data()

if df_raw is None:
    st.error("⚠️ Erro ao conectar com o Google Sheets.")
    st.stop()

# --- LIMPEZA DE DADOS (CRÍTICO) ---
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
    'Desp_Orc', 'HH_Orc_Vlr', 'HH_Orc_Qtd', 'HH_Real_Qtd', 'Conclusao_%'
]

for col in cols_numericas:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].apply(clean_google_number)
    else:
        df_raw[col] = 0.0

# --- CORREÇÃO DE ESCALA DE PORCENTAGEM (ITEM 1) ---
# Se o valor vier como decimal (ex: 0.5 para 50%), multiplica por 100
def fix_percentage_scale(x):
    if 0 < x <= 1.5:
        return x * 100
    return x

if 'Conclusao_%' in df_raw.columns:
    df_raw['Conclusao_%'] = df_raw['Conclusao_%'].apply(fix_percentage_scale)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("### Seleção de Projeto:") 

lista_projetos = sorted(df_raw['Projeto'].astype(str).unique())

index_padrao = 0
if "projeto_foco" in st.session_state:
    try:
        index_padrao = lista_projetos.index(str(st.session_state["projeto_foco"]))
    except ValueError:
        index_padrao = 0

id_projeto = st.sidebar.selectbox("Projeto:", lista_projetos, index=index_padrao, label_visibility="collapsed")

# Converter a coluna projeto para string para garantir o match
df_raw['Projeto'] = df_raw['Projeto'].astype(str)
dados = df_raw[df_raw['Projeto'] == id_projeto].iloc[0]

# ---------------------------------------------------------
# TÍTULO DA PÁGINA
# ---------------------------------------------------------
st.title("Painel de Obra")

# ---------------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------------
custo_total = dados['Mat_Real'] + dados['Desp_Real'] + dados['HH_Real_Vlr'] + dados['Impostos']
lucro_liquido = dados['Vendido'] - custo_total
margem_real_pct = (lucro_liquido / dados['Vendido']) * 100 if dados['Vendido'] > 0 else 0

# --- CARREGAR META (CONFIG) ---
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
META_MARGEM_BRUTA = float(config["meta_margem"])

# Definição de Cores Padronizadas
status = dados['Status']
if status == "Finalizado":
    cor_status, bg_status = "#3fb950", "rgba(63, 185, 80, 0.2)"
elif status == "Apresentado":
    cor_status, bg_status = "#a371f7", "rgba(163, 113, 247, 0.2)"
elif status == "Em andamento":
    cor_status, bg_status = "#d29922", "rgba(210, 153, 34, 0.2)"
else:
    cor_status, bg_status = "#da3633", "rgba(218, 54, 51, 0.2)"

# ---------------------------------------------------------
# CABEÇALHO DO PROJETO
# ---------------------------------------------------------
st.markdown(f"""
<div class="header-box" style="border-top: 5px solid {cor_status};">
    <div>
        <div class="header-title">{dados['Projeto']} - {dados['Descricao']}</div>
        <div class="header-subtitle">
            {dados['Cliente']} | {dados['Cidade']}
        </div>
    </div>
    <div class="header-status" style="background-color: {bg_status}; color: {cor_status}; border: 1px solid {cor_status};">
        {dados['Status']}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

# Card 1: Vendido
with k1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #58a6ff;">
        <div class="kpi-title">Valor Vendido</div>
        <div class="kpi-val">{format_currency(dados['Vendido'])}</div>
    </div>
    """, unsafe_allow_html=True)

# Card 2: Faturado
with k2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid #3fb950;">
        <div class="kpi-title">Valor Faturado</div>
        <div class="kpi-val">{format_currency(dados['Faturado'])}</div>
    </div>
    """, unsafe_allow_html=True)

# Card 3: Lucro
cor_lucro = "txt-green" if lucro_liquido > 0 else "txt-red"
border_lucro = "#3fb950" if lucro_liquido > 0 else "#da3633"
with k3:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid {border_lucro};">
        <div class="kpi-title">Lucro Líquido</div>
        <div class="kpi-val {cor_lucro}">{format_currency(lucro_liquido)}</div>
    </div>
    """, unsafe_allow_html=True)

# Card 4: Margem
cor_margem = "txt-green" if margem_real_pct >= META_MARGEM_BRUTA else "txt-red"
border_margem = "#3fb950" if margem_real_pct >= META_MARGEM_BRUTA else "#da3633"
with k4:
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 4px solid {border_margem};">
        <div class="kpi-title">Margem %</div>
        <div class="kpi-val {cor_margem}">{format_percent(margem_real_pct)}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.divider()

# ---------------------------------------------------------
# SEÇÃO 1: EFICIÊNCIA OPERACIONAL
# ---------------------------------------------------------
st.subheader("⚙️ Eficiência Operacional")

with st.container(border=True):
    col_gauges, col_spacer, col_diag = st.columns([5, 0.2, 3], vertical_alignment="center")
    
    with col_gauges:
        fig_gauge = go.Figure()

        # Gauge 1: Físico
        fig_gauge.add_trace(go.Indicator(
            mode = "gauge+number", value = dados['Conclusao_%'],
            title = {'text': "Avanço Físico", 'font': {'size': 14, 'color': '#8b949e'}},
            domain = {'x': [0, 0.45], 'y': [0, 1]},
            number = {'suffix': "%", 'font': {'color': 'white'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': "#30363d"},
                'bar': {'color': "#3fb950"}, 
                'bgcolor': "#0d1117", 'borderwidth': 2, 'bordercolor': "#30363d"
            }
        ))

        # ---------------------------------------------------------------------------------
        # CORREÇÃO ITEM 2 e 3: INVERSÃO DE VARIÁVEIS CONFORME SOLICITADO
        # Quantidade Real = coluna HH_Orc_Qtd
        # Quantidade Orçada = coluna HH_Real_Qtd
        # ---------------------------------------------------------------------------------
        hh_real = dados['HH_Orc_Qtd'] # Agora puxa de Orc_Qtd
        hh_orc = dados['HH_Real_Qtd'] # Agora puxa de Real_Qtd

        perc_hh = (hh_real / hh_orc * 100) if hh_orc > 0 else 0
        cor_hh = "#da3633" if perc_hh > (dados['Conclusao_%'] + 10) else "#58a6ff"

        fig_gauge.add_trace(go.Indicator(
            mode = "gauge+number", value = perc_hh,
            title = {'text': "Consumo Horas", 'font': {'size': 14, 'color': '#8b949e'}},
            domain = {'x': [0.55, 1], 'y': [0, 1]},
            number = {'suffix': "%", 'valueformat': ".1f", 'font': {'color': 'white'}},
            gauge = {
                'axis': {'range': [0, max(100, perc_hh)], 'tickcolor': "#30363d"},
                'bar': {'color': cor_hh},
                'bgcolor': "#0d1117", 'borderwidth': 2, 'bordercolor': "#30363d",
                'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.75, 'value': dados['Conclusao_%']}
            }
        ))
        
        fig_gauge.update_layout(
            height=220, margin=dict(t=40, b=20, l=30, r=30), 
            paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"},
            xaxis={'fixedrange': True}, yaxis={'fixedrange': True}
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with col_diag:
        # ---------------------------------------------------------------------------------
        # CORREÇÃO ITEM 3: SALDO = ORÇADO - REAL (com variáveis invertidas)
        # ---------------------------------------------------------------------------------
        saldo_hh = hh_orc - hh_real
        
        try:
            saldo_hh_int = int(saldo_hh)
        except:
            saldo_hh_int = 0
        
        if perc_hh > (dados['Conclusao_%'] + 10):
            border_c = "#da3633" 
            titulo = "Baixa Eficiência"
            texto = "O consumo de horas está desproporcional ao avanço físico."
            saldo_txt = f"Excedente: {abs(saldo_hh_int)}h"
        elif perc_hh < dados['Conclusao_%']:
            border_c = "#3fb950"
            titulo = "Alta Eficiência"
            texto = "A obra está avançada economizando horas."
            saldo_txt = f"Saldo Positivo: {saldo_hh_int}h"
        else:
            border_c = "#58a6ff"
            titulo = "Equilibrado"
            texto = "O ritmo segue conforme o planejado."
            saldo_txt = f"Saldo: {saldo_hh_int}h"

        st.markdown(f"""
        <div style="background-color: #161b22; border-left: 4px solid {border_c}; padding: 15px; border-radius: 4px;">
            <strong style="color: {border_c}; font-size: 1.1rem;">{titulo}</strong><br>
            <span style="color: #8b949e; font-size: 0.9rem;">{texto}</span><br><br>
            <strong style="color: white;">{saldo_txt}</strong>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.divider()

# ---------------------------------------------------------
# SEÇÃO 2: COMPOSIÇÃO DE RESULTADO
# ---------------------------------------------------------
st.subheader("📊 Composição do Lucro")

with st.container(border=True):
    modo_vis = st.radio("Unidade de Medida:", ["Percentual (%)", "Valores (R$)"], horizontal=True, label_visibility="collapsed")
    
    labels = ["Vendido", "Impostos", "Materiais", "Despesas", "Mão de Obra", "Lucro"]
    
    if modo_vis == "Valores (R$)":
        vals = [dados['Vendido'], -dados['Impostos'], -dados['Mat_Real'], -dados['Desp_Real'], -dados['HH_Real_Vlr'], lucro_liquido]
        text_vals = [format_currency(v).replace("R$ ", "") for v in vals]
    else:
        base = dados['Vendido'] if dados['Vendido'] > 0 else 1
        vals = [100, -(dados['Impostos']/base)*100, -(dados['Mat_Real']/base)*100, -(dados['Desp_Real']/base)*100, -(dados['HH_Real_Vlr']/base)*100, (lucro_liquido/base)*100]
        text_vals = [format_percent(v) for v in vals]

    fig_water = go.Figure(go.Waterfall(
        orientation = "v", measure = ["relative"]*5 + ["total"],
        x = labels, y = vals, text = text_vals, textposition = "outside",
        connector = {"line":{"color":"#30363d"}},
        decreasing = {"marker":{"color":"#da3633"}}, 
        increasing = {"marker":{"color":"#3fb950"}}, 
        totals = {"marker":{"color":"#58a6ff"}},        
        cliponaxis = False
    ))
    
    fig_water.update_layout(
        height=320, margin=dict(t=50, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False, fixedrange=True),
        xaxis=dict(tickfont=dict(color='white'), fixedrange=True),
        font=dict(color='white')
    )
    st.plotly_chart(fig_water, use_container_width=True, config={'displayModeBar': False})

st.write("")
st.divider()

# ---------------------------------------------------------
# SEÇÃO 3: DETALHAMENTO DE CUSTOS
# ---------------------------------------------------------
st.subheader("🔎 Detalhamento de Custos")

def plot_row_fixed(titulo, orcado, real):
    pct = (real / orcado * 100) if orcado > 0 else 0
    cor_real = "#da3633" if real > orcado else "#58a6ff"
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=[titulo], x=[orcado], name='Orçado', orientation='h', 
        marker_color='#30363d', 
        text=[format_currency(orcado)], textposition='outside',
        cliponaxis=False
    ))
    
    fig.add_trace(go.Bar(
        y=[titulo], x=[real], name='Realizado', orientation='h', 
        marker_color=cor_real, 
        text=[format_currency(real)], textposition='outside',
        cliponaxis=False 
    ))

    max_val = max(orcado, real) * 1.35 
    
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b> <span style='color:#8b949e; font-size:14px'>- Consumo: {format_percent(pct)}</span>", x=0),
        barmode='group',
        height=140,
        margin=dict(l=0, r=20, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#262730', showticklabels=False, range=[0, max_val], fixedrange=True),
        yaxis=dict(showticklabels=False, fixedrange=True),
        font=dict(color='white'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=12, color="#8b949e"),
            bgcolor="rgba(0,0,0,0)"
        )
    )
    return fig

with st.container(border=True):
    st.plotly_chart(plot_row_fixed("Materiais", dados['Mat_Orc'], dados['Mat_Real']), use_container_width=True, config={'displayModeBar': False})

with st.container(border=True):
    st.plotly_chart(plot_row_fixed("Despesas", dados['Desp_Orc'], dados['Desp_Real']), use_container_width=True, config={'displayModeBar': False})

with st.container(border=True):
    st.plotly_chart(plot_row_fixed("Mão de Obra (R$)", dados['HH_Orc_Vlr'], dados['HH_Real_Vlr']), use_container_width=True, config={'displayModeBar': False})

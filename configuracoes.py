import streamlit as st
import pandas as pd
import json
import os
import gspread

# ---------------------------------------------------------
# ESTILO CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {background-color: #0e1117;}
    
    /* --- ALINHAMENTO NO TOPO (PADRONIZADO) --- */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    h1 {
        padding-top: 0rem !important;
        margin-top: -1rem !important;
    }
    
    /* --- Estilização dos Botões (BLINDADO - SÓ AREA PRINCIPAL) --- */
    section[data-testid="stMain"] div.stButton > button {
        background-color: #58a6ff;
        color: #ffffff; 
        border: none;
        font-weight: 700;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    section[data-testid="stMain"] div.stButton > button:hover {
        background-color: #79c0ff;
        color: #ffffff;
        box-shadow: 0 4px 8px rgba(88, 166, 255, 0.3);
    }
    section[data-testid="stMain"] div.stButton > button:active {
        background-color: #58a6ff;
        transform: translateY(2px);
    }

    /* --- Tipografia --- */
    h3 {color: #ffffff !important; font-size: 1.3rem; font-weight: 600;}
    p, .stMarkdown, .stNumberInput label {color: #e6edf3 !important;}
    
</style>
""", unsafe_allow_html=True)

st.title("Configurações")

# ARQUIVOS
CONFIG_FILE = "config.json"

# ---------------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------------
def load_config():
    default_data = {"meta_vendas": 5000000.0, "meta_margem": 25.0, "meta_custo_adm": 5.0}
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_data, f)
        return default_data
    
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        if "meta_custo_adm" not in data: data["meta_custo_adm"] = 5.0
        return data

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

config_atual = load_config()

# ---------------------------------------------------------
# 1. PARÂMETROS DE GESTÃO
# ---------------------------------------------------------
with st.container(border=True):
    st.subheader("Parâmetros de Metas")
    st.write("") 
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nova_meta_vendas = st.number_input(
            "Meta Anual de Vendas (R$)",
            min_value=0.0,
            value=float(config_atual["meta_vendas"]),
            step=100000.0,
            format="%.2f"
        )
        
    with col2:
        nova_meta_margem = st.number_input(
            "Meta de Margem Bruta (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(config_atual["meta_margem"]),
            step=0.5,
            format="%.1f"
        )

    with col3:
        nova_meta_adm = st.number_input(
            "Custo Adm. Esperado (%)",
            min_value=0.0,
            max_value=50.0,
            value=float(config_atual["meta_custo_adm"]),
            step=0.5,
            format="%.1f"
        )
    
    st.write("")
    st.write("") 

    if st.button("Salvar Novos Parâmetros"):
        novos_dados = {
            "meta_vendas": nova_meta_vendas,
            "meta_margem": nova_meta_margem,
            "meta_custo_adm": nova_meta_adm
        }
        save_config(novos_dados)
        st.success("✅ Parâmetros atualizados! Os indicadores foram recalculados.")

# ---------------------------------------------------------
# 2. STATUS DA BASE DE DADOS (GOOGLE SHEETS)
# ---------------------------------------------------------
st.write("")
with st.container(border=True):
    st.subheader("Status da Conexão")
    st.write("")
    
    # Substituído st.info por st.markdown direto para evitar bugs visuais
    st.markdown("""
    **☁️ Sistema conectado ao Google Sheets**
    
    Os dados são atualizados automaticamente a cada 60 segundos.
    
    **Para atualizar os dados:**
    1. Abra a planilha **'dados_dashboard_obras'** no Google Drive.
    2. Edite ou cole os novos dados.
    3. As alterações aparecerão aqui automaticamente.
    """)
    
    st.write("")
    
    # --- BOTÃO DE ATUALIZAÇÃO MANUAL (Configuração Padrão) ---
    if st.button("Atualizar Dados Agora"):
        st.cache_data.clear()
        st.success("✅ Cache limpo! Os dados estão sendo recarregados...")
        st.rerun()
    # ---------------------------------------------------------
    
    st.write("")
    
    # Check de conexão para o usuário ver se está tudo ok
    with st.expander("Verificar dados carregados da nuvem"):
        try:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
            sh = gc.open("dados_dashboard_obras")
            worksheet = sh.sheet1
            dados = worksheet.get_all_records()
            df_check = pd.DataFrame(dados)
            st.dataframe(df_check, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

import streamlit as st
import pandas as pd
import gspread
import time

# ---------------------------------------------------------
# ESTILO CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    .block-container {padding-top: 1rem !important; padding-bottom: 2rem !important;}
    h1 {padding-top: 0rem !important; margin-top: -1rem !important;}
    
    section[data-testid="stMain"] div.stButton > button {
        background-color: #58a6ff; color: #ffffff; border: none; font-weight: 700; padding: 0.5rem 1rem; transition: all 0.2s ease-in-out;
    }
    section[data-testid="stMain"] div.stButton > button:hover {
        background-color: #79c0ff; color: #ffffff; box-shadow: 0 4px 8px rgba(88, 166, 255, 0.3);
    }
    h3 {color: #ffffff !important; font-size: 1.3rem; font-weight: 600;}
    p, .stMarkdown, .stNumberInput label {color: #e6edf3 !important;}
</style>
""", unsafe_allow_html=True)

st.title("Configurações")

# ---------------------------------------------------------
# FUNÇÃO: CARREGAR METAS DA PLANILHA (Sheet2)
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def load_config_from_sheet():
    default_data = {"meta_vendas": 5000000.0, "meta_margem": 25.0, "meta_custo_adm": 5.0}
    try:
        # Conexão via Gspread
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open("dados_dashboard_obras")
        
        # Tenta acessar Sheet2
        try:
            worksheet = sh.worksheet("Sheet2")
        except:
            # Se não existir, tenta criar ou avisa (aqui retornamos default para não quebrar)
            return default_data

        # Pega os valores da segunda linha (assumindo cabeçalho na linha 1)
        # Ordem esperada: A=Vendas, B=Margem, C=Adm
        vals = worksheet.row_values(2)
        
        if len(vals) >= 3:
            # Tratamento básico de string para float
            def parse_float(x):
                if isinstance(x, (int, float)): return float(x)
                clean = str(x).replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()
                return float(clean) if clean else 0.0

            return {
                "meta_vendas": parse_float(vals[0]),
                "meta_margem": parse_float(vals[1]),
                "meta_custo_adm": parse_float(vals[2])
            }
        return default_data
    except Exception as e:
        st.error(f"Erro ao ler configurações da Sheet2: {e}")
        return default_data

config_atual = load_config_from_sheet()

# ---------------------------------------------------------
# 1. VISUALIZAÇÃO DAS METAS (LEITURA)
# ---------------------------------------------------------
with st.container(border=True):
    st.subheader("Parâmetros de Metas (Lido do Excel)")
    st.info("ℹ️ Para alterar estas metas, edite a aba **'Sheet2'** na sua planilha.")
    st.write("") 
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Meta Anual de Vendas", f"R$ {config_atual['meta_vendas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
    with col2:
        st.metric("Meta Margem Bruta", f"{config_atual['meta_margem']:.1f}%".replace(".", ","))

    with col3:
        st.metric("Meta Custo Adm.", f"{config_atual['meta_custo_adm']:.1f}%".replace(".", ","))
    
    st.write("")

# ---------------------------------------------------------
# 2. STATUS DA BASE DE DADOS
# ---------------------------------------------------------
st.write("")
with st.container(border=True):
    st.subheader("Status da Conexão")
    st.write("")
    
    st.markdown("""
    **☁️ Sistema conectado ao Google Sheets**
    
    Os dados (Obras e Metas) são atualizados automaticamente a cada **30 segundos**.
    
    **Para atualizar:**
    1. Abra a planilha **'dados_dashboard_obras'**.
    2. Edite os dados na aba principal ou as metas na aba **'Sheet2'**.
    3. As alterações aparecerão aqui automaticamente.
    """)
    
    st.write("")
    
    with st.expander("Verificar dados carregados da nuvem"):
        try:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
            sh = gc.open("dados_dashboard_obras")
            
            st.markdown("**Aba 1 (Dados):**")
            ws1 = sh.sheet1
            st.dataframe(pd.DataFrame(ws1.get_all_records()).head(3), use_container_width=True)
            
            st.markdown("**Aba 2 (Metas - Sheet2):**")
            try:
                ws2 = sh.worksheet("Sheet2")
                st.dataframe(pd.DataFrame(ws2.get_all_records()), use_container_width=True)
            except:
                st.warning("Aba 'Sheet2' não encontrada.")
                
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

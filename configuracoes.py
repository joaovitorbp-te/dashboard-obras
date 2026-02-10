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
    # Zeros para garantir que não haja "cache falso" no código
    zeros = {"meta_vendas": 0.0, "meta_margem": 0.0, "meta_custo_adm": 0.0}
    
    try:
        # Define escopos explícitos para evitar erro de permissão/Response 200
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Conexão
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"], scopes=scopes)
        sh = gc.open("dados_dashboard_obras")
        
        # Tenta acessar Sheet2
        worksheet = sh.worksheet("Sheet2")

        # Pega a Linha 2 (onde estão os valores)
        # Formato esperado: [R$ 1.000.000,00 | 25,00% | 5,00%]
        vals = worksheet.row_values(2)
        
        if len(vals) >= 3:
            def parse_pt_br(x):
                if isinstance(x, (int, float)): return float(x)
                # Remove R$, %, espaços e troca pontuação brasileira para float python
                clean = str(x).replace("R$", "").replace("%", "").strip()
                clean = clean.replace(".", "") # Remove separador de milhar
                clean = clean.replace(",", ".") # Troca vírgula decimal por ponto
                try:
                    return float(clean)
                except:
                    return 0.0

            return {
                "meta_vendas": parse_pt_br(vals[0]),
                "meta_margem": parse_pt_br(vals[1]),
                "meta_custo_adm": parse_pt_br(vals[2])
            }
        return zeros
        
    except Exception as e:
        # Retorna o erro dentro do dicionário para exibir na tela de forma controlada
        return {"error": str(e), **zeros}

config_atual = load_config_from_sheet()

# ---------------------------------------------------------
# 1. VISUALIZAÇÃO DAS METAS
# ---------------------------------------------------------
with st.container(border=True):
    st.subheader("Parâmetros de Metas (Sheet2)")
    
    # Se houver erro de conexão, exibe aqui
    if "error" in config_atual and config_atual["error"]:
        st.error(f"Erro ao ler 'Sheet2': {config_atual['error']}")
    else:
        st.info("ℹ️ Dados puxados diretamente da aba **'Sheet2'** da planilha.")

    st.write("") 
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Meta Anual de Vendas", f"R$ {config_atual['meta_vendas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
    with col2:
        st.metric("Meta Margem Bruta", f"{config_atual['meta_margem']:.2f}%".replace(".", ","))

    with col3:
        st.metric("Meta Custo Adm.", f"{config_atual['meta_custo_adm']:.2f}%".replace(".", ","))
    
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
    
    # Check manual de conexão para debug
    with st.expander("Verificar dados carregados da nuvem"):
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"], scopes=scopes)
            sh = gc.open("dados_dashboard_obras")
            
            st.markdown("**Aba 1 (Dados Obras):**")
            ws1 = sh.sheet1
            st.dataframe(pd.DataFrame(ws1.get_all_records()).head(3), use_container_width=True)
            
            st.markdown("**Aba 2 (Metas - Sheet2):**")
            ws2 = sh.worksheet("Sheet2")
            st.dataframe(pd.DataFrame(ws2.get_all_records()), use_container_width=True)
                
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
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
# FUNÇÃO: CARREGAR METAS DA PLANILHA EXCEL (Sheet2)
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def load_config_from_sheet():
    zeros = {"meta_vendas": 0.0, "meta_margem": 0.0, "meta_custo_adm": 0.0}
    try:
        # 1. Autenticação
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        # 2. Buscar o arquivo Excel
        results = service.files().list(
            q="name='dados_dashboard_obras.xlsx' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            return {"error": "Arquivo .xlsx não encontrado", **zeros}
            
        file_id = files[0]['id']
        
        # 3. Baixar para memória
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file_io.seek(0)
        
        # 4. Ler a aba 'Sheet2' com Pandas
        df_config = pd.read_excel(file_io, sheet_name='Sheet2')
        
        if not df_config.empty:
            # Pega a primeira linha de dados (índice 0)
            row = df_config.iloc[0]
            
            # Função de limpeza
            def parse_val(val):
                if isinstance(val, (int, float)): return float(val)
                s = str(val).replace('R$', '').replace('%', '').strip()
                s = s.replace('.', '').replace(',', '.') # Formato BR para US
                try: return float(s)
                except: return 0.0

            # Assume ordem das colunas: Vendas | Margem | Adm
            return {
                "meta_vendas": parse_val(row.iloc[0]),
                "meta_margem": parse_val(row.iloc[1]),
                "meta_custo_adm": parse_val(row.iloc[2])
            }
            
        return zeros
        
    except Exception as e:
        return {"error": str(e), **zeros}

config_atual = load_config_from_sheet()

# ---------------------------------------------------------
# 1. VISUALIZAÇÃO DAS METAS
# ---------------------------------------------------------
with st.container(border=True):
    st.subheader("Parâmetros de Metas")
    
    if "error" in config_atual and config_atual["error"]:
        st.error(f"Erro ao ler Sheet2: {config_atual['error']}")
    
    st.write("") 
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Meta Anual de Vendas", f"R$ {config_atual['meta_vendas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
    with col2:
        val_margem = config_atual['meta_margem']
        if val_margem <= 1.0: val_margem *= 100
        st.metric("Meta Margem Bruta", f"{val_margem:.2f}%".replace(".", ","))

    with col3:
        val_adm = config_atual['meta_custo_adm']
        if val_adm <= 1.0: val_adm *= 100
        st.metric("Meta Custo Adm.", f"{val_adm:.2f}%".replace(".", ","))
    
    st.write("")

# ---------------------------------------------------------
# 2. STATUS DA BASE DE DADOS
# ---------------------------------------------------------
st.write("")
with st.container(border=True):
    st.subheader("Status da Conexão")
    st.write("")
    
    st.markdown("""
    **☁️ Sistema conectado ao Google Sheets (Excel)**
    
    Os dados são atualizados automaticamente a cada **30 segundos**.
    
    **Para atualizar:**
    1. Abra o arquivo **'dados_dashboard_obras.xlsx'** no Drive.
    2. Edite a aba **Sheet1** para orçamentos ou a aba **Sheet2** para metas.
    3. As alterações aparecerão aqui automaticamente.
    """)
    
    st.write("")

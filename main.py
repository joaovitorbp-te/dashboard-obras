import streamlit as st
import streamlit_authenticator as stauth
import yaml

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO VISUAL
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard Obras", layout="wide", page_icon="📊")

st.markdown("""
<style>
    /* Fundo geral */
    .stApp {background-color: #0e1117;}
    
    /* --- 0. ALINHAMENTO GLOBAL (PUXA TUDO PARA O TOPO) --- */
    .block-container {
        padding-top: 1rem !important; /* Reduz a margem superior padrão */
        padding-bottom: 2rem !important;
    }
    
    /* --- ESTILO DO CARD DE LOGIN --- */
    [data-testid="stForm"] {
        background-color: #161b22;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #30363d;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        max-width: 350px !important;
        margin: 0 auto !important;
        position: relative;
        top: 50px; 
    }

    /* Inputs do Login */
    .stTextInput input {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: white !important;
    }
    
    /* --- BOTÕES --- */
    
    /* 1. Botão "Entrar" (Azul e destacado) */
    div[data-testid="stForm"] .stButton button {
        background-color: #58a6ff !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        margin-top: 10px;
        transition: all 0.2s ease;
    }
    div[data-testid="stForm"] .stButton button:hover {
        background-color: #79c0ff !important;
    }

    /* 2. Botão da Sidebar (TRAVADO para não mudar de tamanho) */
    section[data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        border: 1px solid #4a4a4a !important;
        color: #fafafa !important;
        width: 100% !important; /* Garante largura total sempre */
        box-sizing: border-box !important;
    }
    
    section[data-testid="stSidebar"] .stButton button:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
        background-color: rgba(255, 75, 75, 0.1) !important;
    }
    
    /* Centraliza mensagens de erro */
    .stAlert {
        max-width: 350px;
        margin: 0 auto;
        position: relative;
        top: 60px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. PREPARAÇÃO DOS DADOS
# ---------------------------------------------------------
secrets = st.secrets

config_dict = {
    "credentials": {
        "usernames": {
            username: dict(user_data) 
            for username, user_data in secrets['credentials']['usernames'].items()
        }
    },
    "cookie": dict(secrets['cookie']),
    "preauthorized": list(secrets['preauthorized']['emails'])
}

# ---------------------------------------------------------
# 3. AUTENTICAÇÃO
# ---------------------------------------------------------
try:
    authenticator = stauth.Authenticate(
        config_dict['credentials'],
        config_dict['cookie']['name'],
        config_dict['cookie']['key'],
        config_dict['cookie']['expiry_days'],
        config_dict['preauthorized']
    )
except TypeError:
    authenticator = stauth.Authenticate(
        config_dict['credentials'],
        config_dict['cookie']['name'],
        config_dict['cookie']['key'],
        config_dict['cookie']['expiry_days']
    )

authenticator.login(location='main')

# ---------------------------------------------------------
# 4. LÓGICA DO SISTEMA
# ---------------------------------------------------------

if st.session_state.get("authentication_status"):
    
    # === USUÁRIO LOGADO ===
    
    # 1. Menu de Navegação (ATUALIZADO COM NOVOS NOMES DE ARQUIVO)
    pg = st.navigation([
        st.Page("gestao_carteira.py", title="Gestão da Carteira", icon="🏢"),
        st.Page("painel_obra.py", title="Painel de Obra", icon="📝"),
        st.Page("dados_insights.py", title="Dados & Insights", icon="📈"), 
        st.Page("configuracoes.py", title="Configurações", icon="⚙️"),
    ])
    
    # 2. Executa a Página
    pg.run()

    # 3. Botão de Desconectar (Rodapé)
    with st.sidebar:
        st.divider()
        authenticator.logout('Desconectar', 'sidebar') 

elif st.session_state.get("authentication_status") is False:
    st.error('Usuário ou senha incorretos.')

elif st.session_state.get("authentication_status") is None:
    st.markdown('<style>header {visibility: hidden;}</style>', unsafe_allow_html=True)
    pass

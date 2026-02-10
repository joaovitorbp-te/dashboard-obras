import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(
    page_title="Configurações",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Configurações e Status")
st.markdown("---")

# Caminho do arquivo (ajuste conforme sua estrutura de pastas)
# Se estiver na raiz, use apenas o nome do arquivo. Se estiver em uma pasta 'data', use 'data/nome.xlsx'
FILE_PATH = "dados_dashboard_obras.xlsx"

# --- SEÇÃO DE STATUS DA CONEXÃO ---
st.subheader("📡 Status da Conexão de Dados")

col1, col2 = st.columns(2)

# Variáveis de controle
status_obras = False
status_metas = False
msg_erro = ""

# Verificação do arquivo e das abas
if os.path.exists(FILE_PATH):
    try:
        # Teste de conexão com a aba de Obras/Orçamentos (Geralmente Sheet1)
        df_test_obras = pd.read_excel(FILE_PATH, sheet_name='Sheet1', nrows=1)
        status_obras = True
    except Exception as e:
        status_obras = False
        msg_erro += f"Erro na aba 'Sheet1' (Obras): {e}\n"

    try:
        # Teste de conexão com a aba de Metas (Sheet2)
        df_test_metas = pd.read_excel(FILE_PATH, sheet_name='Sheet2', nrows=1)
        status_metas = True
    except Exception as e:
        status_metas = False
        msg_erro += f"Erro na aba 'Sheet2' (Metas): {e}\n"
else:
    st.error(f"Arquivo não encontrado: {FILE_PATH}")


# --- EXIBIÇÃO DOS INDICADORES ---

with col1:
    st.markdown("### Orçamentos e Obras")
    if status_obras:
        st.success("✅ Conectado (Sheet1)")
    else:
        st.error("❌ Falha na conexão (Sheet1)")

with col2:
    st.markdown("### Parâmetros de Metas")
    if status_metas:
        st.success("✅ Conectado (Sheet2)")
    else:
        st.error("❌ Falha na conexão (Sheet2)")

# Exibe detalhes do erro se houver
if msg_erro:
    st.warning(f"Detalhes do erro:\n{msg_erro}")

st.markdown("---")

# --- INFORMAÇÕES GERAIS (Sem Popup/Sobreposição) ---
st.subheader("ℹ️ Fonte de Dados")

st.markdown(
    f"""
    O painel está consumindo dados do arquivo local: **`{FILE_PATH}`**.
    
    * **Orçamentos/Obras:** Carregados da aba `Sheet1`.
    * **Metas Financeiras:** Carregadas da aba `Sheet2`.
    """
)

st.caption("Para atualizar os dados, edite o arquivo Excel e recarregue a página (F5).")

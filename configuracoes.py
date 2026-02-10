import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Configurações", layout="wide")

st.title("Configurações")

# Caminho do arquivo
file_path = "dados_dashboard_obras.xlsx"

st.subheader("Status da Conexão")

# Verifica se o arquivo existe
if os.path.exists(file_path):
    col1, col2 = st.columns(2)
    
    # Verificação da Sheet1 (Orçamentos/Obras)
    with col1:
        try:
            pd.read_excel(file_path, sheet_name='Sheet1', nrows=1)
            st.success("✅ Conexão com Orçamentos (Sheet1): OK")
        except Exception as e:
            st.error(f"❌ Erro ao ler Sheet1: {e}")

    # Verificação da Sheet2 (Metas/Configurações)
    with col2:
        try:
            pd.read_excel(file_path, sheet_name='Sheet2', nrows=1)
            st.success("✅ Conexão com Metas (Sheet2): OK")
        except Exception as e:
            st.error(f"❌ Erro ao ler Sheet2: {e}")

    # Mensagem informativa (agora fixa na tela, sem sobrepor nada)
    st.markdown("---")
    st.info(f"ℹ️ Dados puxados do arquivo **'{file_path}'** (Abas 'Sheet1' e 'Sheet2').")

else:
    st.error(f"❌ O arquivo '{file_path}' não foi encontrado no diretório.")

# Botão para recarregar (opcional, ajuda a forçar a leitura)
if st.button("🔄 Verificar Novamente"):
    st.rerun()

from pathlib import Path
import streamlit as st
import pandas as pd

def leitura_de_dados():
    """Carrega os dados do Excel e armazena no session_state."""
    if 'dados' not in st.session_state:
        # Define o caminho para a pasta 'planilhas'
        pasta_datasets = Path(__file__).resolve().parent / 'planilhas'  # Ajuste aqui
        
        # Verifica se o arquivo existe
        if not (pasta_datasets / '2024.xlsx').exists():
            st.error("Arquivo '2024.xlsx' não encontrado na pasta 'planilhas'.")
            return
        
        try:
            # Carrega os DataFrames
            df_contratos = pd.read_excel(pasta_datasets / '2024.xlsx', sheet_name='Contratos')
            df_historico = pd.read_excel(pasta_datasets / '2024.xlsx', sheet_name='Históricos')
        except Exception as e:
            st.error(f"Erro ao carregar os dados: {e}")
            return
        
        # Armazena os dados no session_state
        dados = {
            'df_contratos': df_contratos,
            'df_historico': df_historico
        }
        
        st.session_state['caminho_datasets'] = pasta_datasets
        st.session_state['dados'] = dados

def save_to_excel(df, file_path, sheet_name='Contratos'):
    """Salva o DataFrame no arquivo Excel."""
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

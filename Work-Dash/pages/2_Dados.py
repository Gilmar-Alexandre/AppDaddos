import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from carregar_dados import leitura_de_dados

# Configurar o layout da página para wide
st.set_page_config(layout="wide")

# Carrega os dados
leitura_de_dados()

# Acesso aos dados carregados
dados = st.session_state.get('dados', {})
df_contratos = dados.get('df_contratos', pd.DataFrame())
df_historico = dados.get('df_historico', pd.DataFrame())

# Define o caminho do arquivo
pasta_datasets = Path(__file__).resolve().parent.parent / 'planilhas'
file_path = pasta_datasets / '2024.xlsx'

# Verifica se o diretório existe, se não, cria
if not pasta_datasets.exists():
    pasta_datasets.mkdir(parents=True, exist_ok=True)

# Função para salvar o DataFrame no Excel
def save_to_excel(df, file_path, sheet_name='Contratos'):
    """Salva o DataFrame no arquivo Excel."""
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")

# Função para registrar histórico
def log_change(contract_num, action):
    """Registra uma mudança no histórico."""
    new_log = pd.DataFrame({
        'CONTRATO Nº': [contract_num],
        'AÇÃO': [action],
        'DATA': [datetime.now()]
    })
    # Atualiza o DataFrame do histórico no session_state
    st.session_state['dados']['df_historico'] = pd.concat(
        [st.session_state['dados']['df_historico'], new_log], ignore_index=True
    )
    save_to_excel(st.session_state['dados']['df_historico'], file_path, sheet_name='Históricos')

# Exibir a tabela de contratos
st.title('Gerenciamento de Contratos')

# Filtros inteligentes
st.sidebar.header('Filtros')
filter_contract_num = st.sidebar.text_input('Filtrar por Número do Contrato')
filtered_df = df_contratos[df_contratos['CONTRATO Nº'].astype(str).str.contains(filter_contract_num)] if filter_contract_num else df_contratos
st.dataframe(filtered_df)

# Barra lateral para ações
st.sidebar.header('Ações')

# Campos para adicionar um novo contrato
st.sidebar.subheader('Adicionar Novo Contrato')
new_row_data = {}
status_options = ['Concluído', 'Cancelado', 'Em Processo']  # Exemplo de opções de status

for col in df_contratos.columns:
    if col == 'STATUS':  # Supondo que você tenha uma coluna de status
        new_row_data[col] = st.sidebar.selectbox(f'Status', status_options)
    else:
        new_row_data[col] = st.sidebar.text_input(f'{col}')

# Botão para adicionar a nova linha
if st.sidebar.button('Adicionar Novo Contrato'):
    # Verifica quais campos estão vazios
    missing_fields = [col for col, value in new_row_data.items() if not value]
    
    if missing_fields:  # Se houver campos faltando
        st.sidebar.error(f'Por favor, preencha os seguintes campos: {", ".join(missing_fields)}.')
    else:
        # Adiciona a nova linha sem verificar se o contrato já existe
        new_row = pd.DataFrame([new_row_data])  # Cria um DataFrame a partir da nova linha
        df_contratos = pd.concat([df_contratos, new_row], ignore_index=True)
        st.session_state['dados']['df_contratos'] = df_contratos  # Atualiza o DataFrame no session_state
        log_change(new_row_data['CONTRATO Nº'], 'Adicionado')  # Atualiza o histórico
        save_to_excel(df_contratos, file_path)  # Salva o DataFrame atualizado
        st.success('Novo contrato adicionado com sucesso!')

# Campos para excluir uma linha
st.sidebar.subheader('Excluir Contrato')
contrato_excluir = st.sidebar.text_input('Número do Contrato para Excluir')
sistema_excluir = st.sidebar.text_input('Sistema do Contrato para Excluir')

if st.sidebar.button('Excluir Contrato'):
    if contrato_excluir and sistema_excluir:
        # Filtra o DataFrame para encontrar a linha correspondente
        mask = (df_contratos['CONTRATO Nº'] == contrato_excluir) & (df_contratos['SISTEMA'] == sistema_excluir)
        if mask.any():
            df_contratos = df_contratos[~mask]  # Remove a linha correspondente
            st.session_state['dados']['df_contratos'] = df_contratos  # Atualiza o DataFrame no session_state
            log_change(contrato_excluir, 'Excluído')  # Atualiza o histórico
            save_to_excel(df_contratos, file_path)  # Salva o DataFrame atualizado
            st.success('Contrato excluído com sucesso!')
        else:
            st.sidebar.error('Contrato ou sistema não encontrado!')
    else:
        st.sidebar.error('Por favor, preencha ambos os campos: Número do Contrato e Sistema.')

# Opção para exibir histórico
if st.sidebar.checkbox('Mostrar Histórico de Alterações'):
    st.subheader('Histórico de Alterações')
    st.dataframe(st.session_state['dados']['df_historico'])

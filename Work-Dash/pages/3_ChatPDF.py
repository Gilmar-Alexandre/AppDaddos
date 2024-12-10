import streamlit as st
import streamlit.components.v1 as components
import os
from pathlib import Path
from utils import cria_chain_conversa, PASTA_ARQUIVOS

import os
import streamlit as st

def load_particles_animation():
    """Carrega a animação de partículas a partir do arquivo HTML"""
    try:
        # Caminho do script atual
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Diretório do script: {script_dir}")

        # Possíveis localizações
        possible_paths = [
            os.path.join(script_dir, 'graph.html'),
            os.path.join(script_dir, 'Work-Dash', 'graph.html'),
            os.path.join(os.path.dirname(script_dir), 'graph.html'),
            r'C:\Users\Gasc\Downloads\Projetos\Streamlit\AppDaddos\Work-Dash\pages\Work-Dash\graph.html'
        ]

        for path in possible_paths:
            print(f"Verificando caminho: {path}")
            if os.path.exists(path):
                print(f"Arquivo encontrado em: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"Arquivo não encontrado em: {path}")
        
        st.error("Não foi possível encontrar o arquivo graph.html")
        return ""

    except Exception as e:
        st.error(f"Erro ao carregar animação: {e}")
        return ""

def sidebar():
    """Função para a barra lateral onde os usuários podem fazer upload de PDFs."""
    # Garante que a pasta de arquivos exista
    PASTA_ARQUIVOS.mkdir(parents=True, exist_ok=True)

    uploaded_pdfs = st.sidebar.file_uploader(
        'Adicione seus arquivos PDF', 
        type=['pdf'], 
        accept_multiple_files=True
    )
    
    # Limpa arquivos antigos e salva novos PDFs
    if uploaded_pdfs:
        # Remove arquivos PDF antigos
        for arquivo in PASTA_ARQUIVOS.glob('*.pdf'):
            arquivo.unlink()
        
        # Salva novos PDFs
        for pdf in uploaded_pdfs:
            caminho_pdf = PASTA_ARQUIVOS / pdf.name
            with open(caminho_pdf, 'wb') as f:
                f.write(pdf.read())
    
    # Botão para inicializar ou atualizar o ChatBot
    label_botao = 'Inicializar Chatbot' if 'chain' not in st.session_state else 'Atualizar Chatbot'
    if st.sidebar.button(label_botao, use_container_width=True):
        if len(list(PASTA_ARQUIVOS.glob('*.pdf'))) == 0:
            st.sidebar.error('Adicione arquivos .pdf para inicializar o chatbot')
        else:
            st.sidebar.success('Inicializando o Chatbot...')
            cria_chain_conversa()
            st.rerun()

def chat_window():
    """Função para a janela de chat onde os usuários interagem com o ChatBot."""
    st.header('🤖 Bem-vindo ao Chatbot', divider=True)

    # Verifica se o chain foi criado
    if 'chain' not in st.session_state:
        st.error('Faça o upload de PDFs para começar!')
        return

    chain = st.session_state['chain']
    memory = chain.memory

    # Carrega mensagens anteriores
    container = st.container()
    
    # Exibe histórico de mensagens
    mensagens = memory.load_memory_variables({})['chat_history']
    for mensagem in mensagens:
        chat = container.chat_message(mensagem.type)
        chat.markdown(mensagem.content)

    # Entrada para nova mensagem
    nova_mensagem = st.chat_input('Converse com seus documentos...')
    if nova_mensagem:
        # Exibe mensagem do usuário
        container.chat_message('human').markdown(nova_mensagem)
        
        # Indica que está gerando resposta
        with container.chat_message('ai'):
            placeholder = st.empty()
            placeholder.markdown('Gerando resposta...')
            
            # Gera resposta
            try:
                resposta = chain.invoke({'question': nova_mensagem})
                placeholder.markdown(resposta)
            except Exception as e:
                placeholder.error(f"Erro ao gerar resposta: {e}")

def main():
    """Função principal que configura e executa a aplicação Streamlit."""
    # Configurações de página
    st.set_page_config(
        page_title="Chatbot de Documentos", 
        page_icon="🤖",
        layout="wide"
    )

    # Adiciona animação de partículas
    particles_html = load_particles_animation()
    if particles_html:
        components.html(particles_html, height=400, scrolling=False)

    # Layout principal
    sidebar()
    chat_window()

if __name__ == '__main__':
    main()

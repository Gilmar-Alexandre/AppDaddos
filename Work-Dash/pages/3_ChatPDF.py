import os
import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components
from utils import PASTA_ARQUIVOS, cria_chain_conversa

st.set_page_config(layout="wide")

from utils import configurar_ambiente_openai

# No início do seu main() ou antes de usar funções que precisam da chave
def main():
    # Configura o ambiente OpenAI
    if not configurar_ambiente_openai():
        st.stop()  # Interrompe a execução se não tiver chave


def sidebar():
    """Função para a barra lateral onde os usuários podem fazer upload de PDFs."""
    # Garante que a pasta de arquivos exista
    PASTA_ARQUIVOS.mkdir(parents=True, exist_ok=True)

    # Inicializa o histórico de mensagens se não existir
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    with st.sidebar.container():
        st.markdown("## 📄 Upload de Documentos")
        
        # Upload de PDFs com validações
        uploaded_pdfs = st.file_uploader(
            'Adicione seus arquivos PDF', 
            type=['pdf'], 
            accept_multiple_files=True,
            help="Faça upload de documentos PDF para iniciar o chat"
        )
        
        # Processamento dos PDFs enviados
        if uploaded_pdfs:
            # Limpa PDFs antigos
            try:
                for arquivo in PASTA_ARQUIVOS.glob('*.pdf'):
                    arquivo.unlink()
                
                # Limpa o histórico de mensagens
                st.session_state.messages = []
            except Exception as e:
                st.sidebar.warning(f"Erro ao limpar arquivos antigos: {e}")
            
            # Salva novos PDFs
            pdf_salvos = 0
            for pdf in uploaded_pdfs:
                try:
                    caminho_pdf = PASTA_ARQUIVOS / pdf.name
                    with open(caminho_pdf, 'wb') as f:
                        f.write(pdf.read())
                    pdf_salvos += 1
                except Exception as e:
                    st.sidebar.error(f"Erro ao salvar {pdf.name}: {e}")
            
            # Feedback sobre PDFs salvos
            if pdf_salvos > 0:
                st.sidebar.success(f"{pdf_salvos} PDF(s) carregados com sucesso!")

        # Botão para inicializar/atualizar ChatBot
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            iniciar_bot = st.button(
                'Iniciar Chatbot', 
                use_container_width=True,
                help="Inicialize o chatbot após fazer upload dos PDFs"
            )
        
        with col2:
            limpar_docs = st.button(
                'Limpar Documentos', 
                use_container_width=True,
                help="Remove todos os documentos carregados"
            )
        
        # Lógica de inicialização do chatbot
        if iniciar_bot:
            pdfs_carregados = list(PASTA_ARQUIVOS.glob('*.pdf'))
            
            if not pdfs_carregados:
                st.sidebar.error('Adicione arquivos .pdf para inicializar o chatbot')
            else:
                try:
                    with st.spinner('Inicializando Chatbot...'):
                        chain = cria_chain_conversa()
                    
                    if chain:
                        st.sidebar.success(f'Chatbot inicializado com {len(pdfs_carregados)} documento(s)!')
                        # Limpa mensagens anteriores
                        st.session_state.messages = []
                    else:
                        st.sidebar.error('Falha ao inicializar o chatbot')
                    
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Erro ao inicializar chatbot: {e}")
        
        # Lógica de limpeza de documentos
        if limpar_docs:
            try:
                for arquivo in PASTA_ARQUIVOS.glob('*.pdf'):
                    arquivo.unlink()
                st.sidebar.success("Todos os documentos foram removidos.")
                
                # Limpa o estado da sessão
                if 'chain' in st.session_state:
                    del st.session_state['chain']
                
                # Limpa o histórico de mensagens
                st.session_state.messages = []
                
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Erro ao limpar documentos: {e}")

def chat_window():
    """Função para a janela de chat onde os usuários interagem com o ChatBot."""
    st.header('🤖 Bem-vindo ao Chatbot de Documentos', divider=True)

    # Inicializa o histórico de mensagens se não existir
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Verifica se o chain foi criado
    if 'chain' not in st.session_state:
        st.info('Faça o upload de PDFs e inicialize o Chatbot para começar!')
        return

    chain = st.session_state['chain']

    # Exibe histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada para nova mensagem
    if prompt := st.chat_input('Converse com seus documentos...'):
        # Adiciona mensagem do usuário ao histórico
        st.session_state.messages.append({
            "role": "human", 
            "content": prompt
        })

        # Exibe a mensagem do usuário
        with st.chat_message("human"):
            st.markdown(prompt)

        # Área de resposta da IA
        with st.chat_message('ai'):
            # Placeholder para mostrar progresso
            message_placeholder = st.empty()
            message_placeholder.markdown("Gerando resposta...")

            try:
                # Gera resposta usando o chain
                full_response = ""
                
                # Invoca a cadeia de conversação
                response = chain.invoke({'question': prompt})
                
                # Se a resposta for um dicionário, tenta pegar o texto
                if isinstance(response, dict):
                    full_response = response.get('answer', str(response))
                else:
                    full_response = str(response)

                # Limpa o placeholder e mostra a resposta
                message_placeholder.markdown(full_response)

                # Adiciona resposta da IA ao histórico
                st.session_state.messages.append({
                    "role": "ai", 
                    "content": full_response
                })

            except Exception as e:
                # Tratamento de erro detalhado
                error_message = f"Erro ao gerar resposta: {str(e)}"
                message_placeholder.error(error_message)
                
                # Log opcional do erro
                st.error(error_message)

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

def main():
    """Função principal que configura e executa a aplicação Streamlit."""
    # Adiciona animação de partículas
    particles_html = load_particles_animation()
    if particles_html:
        components.html(particles_html, height=400, scrolling=False)

    # Layout principal
    sidebar()
    chat_window()

if __name__ == '__main__':
    main()

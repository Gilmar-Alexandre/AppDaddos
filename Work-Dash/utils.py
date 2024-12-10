import os
import streamlit as st
from pathlib import Path
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from configs import *
import openai

def configurar_pasta_documentos():
    """
    Configura o caminho da pasta de documentos de forma flexível.
    """
    # Caminho base do script atual
    base_dir = Path(__file__).parent

    # Lista de possíveis localizações
    possiveis_caminhos = [
        base_dir / 'pdfs',
        base_dir.parent / 'pdfs',
        base_dir.parent / 'Work-Dash' / 'pdfs',
        Path(os.path.expanduser('~/Documents/pdfs')),
        Path(os.path.expanduser('~/Downloads/pdfs')),
    ]

    # Tenta criar a primeira pasta válida
    for caminho in possiveis_caminhos:
        try:
            caminho.mkdir(parents=True, exist_ok=True)
            return caminho
        except Exception:
            continue
    
    # Se nenhum caminho funcionar, usa uma pasta temporária
    import tempfile
    pasta_temp = Path(tempfile.gettempdir()) / 'chat_pdfs'
    pasta_temp.mkdir(parents=True, exist_ok=True)
    return pasta_temp

# Define a pasta de arquivos globalmente
PASTA_ARQUIVOS = configurar_pasta_documentos()

import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

load_dotenv()

def validar_openai_key():
    """Valida e obtém a chave da OpenAI"""
    # Fontes potenciais da chave
    sources = [
        # Primeiro, tenta do .env
        lambda: os.getenv("OPENAI_API_KEY"),
        
        # Depois, tenta das secrets do Streamlit
        lambda: st.secrets.get("OPENAI_API_KEY") if hasattr(st, 'secrets') else None,
    ]
    
    # Itera pelas fontes de chave
    for get_key in sources:
        key = get_key()
        if key and key.strip():  # Verifica se a chave não está vazia
            try:
                # Validação da chave
                client = openai.OpenAI(api_key=key)
                # Tenta fazer uma chamada simples para verificar
                client.models.list()
                
                # Define a chave no ambiente
                os.environ["OPENAI_API_KEY"] = key
                
                return key
            except Exception as e:
                st.error(f"Chave inválida: {e}")
                continue
    
    # Se nenhuma chave for válida
    st.error("Não foi possível validar a chave OpenAI")
    return None

# Função auxiliar para debug
def mostrar_status_chave():
    """
    Verifica e mostra o status da chave OpenAI
    """
    st.sidebar.markdown("### Verificação da Chave OpenAI")
    
    # Tenta obter a chave
    key = os.getenv("OPENAI_API_KEY")
    
    if key:
        # Verifica se a chave parece válida (tem um comprimento mínimo)
        if len(key) > 20:
            # Mostra os últimos 4 caracteres
            st.sidebar.success(f"Chave OpenAI configurada (****{key[-4:]})")
        else:
            st.sidebar.warning("Chave OpenAI parece incompleta")
    else:
        st.sidebar.error("Nenhuma chave OpenAI encontrada")

# Pode ser chamado no início do seu script principal ou página
def configurar_ambiente_openai():
    """
    Configura o ambiente e valida a chave OpenAI
    """
    # Mostra o status da chave
    mostrar_status_chave()
    
    # Tenta validar a chave
    chave = validar_openai_key()
    
    if not chave:
        st.warning("Por favor, configure sua chave OpenAI")
        return False
    
    return True

def importacao_documentos(pasta=PASTA_ARQUIVOS) -> list:
    """Importa documentos PDF da pasta especificada."""
    documentos = []
    pdfs = list(pasta.glob('*.pdf'))
    
    if not pdfs:
        st.warning(f"Nenhum documento PDF encontrado em {pasta}")
        return documentos
    
    for arquivo in pdfs:
        try:
            loader = PyPDFLoader(str(arquivo))
            documentos_arquivo = loader.load()
            documentos.extend(documentos_arquivo)
        except Exception as e:
            st.warning(f"Erro ao carregar {arquivo}: {e}")
    
    return documentos

def split_de_documentos(documentos: list) -> list:
    """Divide documentos em partes menores."""
    if not documentos:
        st.warning("Nenhum documento para dividir.")
        return []
    
    try:
        recur_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Reduzido para melhor processamento
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        documentos_divididos = recur_splitter.split_documents(documentos)

        # Adiciona metadados a cada documento
        for i, doc in enumerate(documentos_divididos):
            doc.metadata['source'] = str(doc.metadata.get('source', f'documento_{i}'))
            doc.metadata['doc_id'] = i

        return documentos_divididos
    except Exception as e:
        st.error(f"Erro ao dividir documentos: {e}")
        return []

def cria_vector_store(documentos: list):
    """Cria um vetor de armazenamento a partir dos documentos."""
    try:
        # Valida a chave OpenAI
        openai_api_key = validar_openai_key()
        
        if not openai_api_key:
            st.error("Não foi possível obter chave OpenAI válida.")
            return None

        # Configura variáveis de ambiente
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Cria embeddings
        embedding_model = OpenAIEmbeddings(api_key=openai_api_key)
        
        # Cria vetor de armazenamento
        vector_store = FAISS.from_documents(
            documents=documentos,
            embedding=embedding_model
        )
        
        return vector_store
    
    except Exception as e:
        st.error(f"Erro ao criar vector store: {e}")
        return None

def cria_chain_conversa():
    """
    Cria a cadeia de conversa para o chatbot.
    """
    try:
        # Carrega documentos
        documentos = importacao_documentos()
        
        # Verifica se há documentos
        if not documentos:
            st.error("Nenhum documento carregado.")
            return None
        
        # Divide documentos
        documentos_divididos = split_de_documentos(documentos)
        
        if not documentos_divididos:
            st.error("Falha ao dividir documentos.")
            return None
        
        # Cria vector store
        vector_store = cria_vector_store(documentos_divididos)
        
        if not vector_store:
            st.error("Falha ao criar vector store.")
            return None
        
        # Obtém chave OpenAI
        openai_api_key = validar_openai_key()
        if not openai_api_key:
            st.error("Chave OpenAI não configurada.")
            return None
        
        # Configurações do modelo
        chat = ChatOpenAI(
            model=get_config('model_name', 'gpt-3.5-turbo'),
            api_key=openai_api_key,
            temperature=0.3
        )
        
        # Configura memória
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key='chat_history',
            output_key='answer'
        )
        
        # Configura recuperador
        retriever = vector_store.as_retriever(
            search_type=get_config('retrieval_search_type', 'similarity'),
            search_kwargs=get_config('retrieval_kwargs', {'k': 4})
        )
        
        # Cria cadeia de conversação
        chat_chain = ConversationalRetrievalChain.from_llm(
            llm=chat,
            memory=memory,
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )

        # Armazena no estado da sessão
        st.session_state['chain'] = chat_chain
        
        # Feedback de sucesso
        st.success(f"Chatbot inicializado com {len(documentos)} documento(s)!")
        
        return chat_chain
    
    except Exception as e:
        st.error(f"Erro crítico ao criar cadeia de conversa: {e}")
        return None

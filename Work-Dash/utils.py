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
from dotenv import load_dotenv, find_dotenv
from configs import *
import openai

# Carregar variáveis de ambiente
_ = load_dotenv(find_dotenv())

# Definir o caminho da pasta de arquivos
PASTA_ARQUIVOS = Path(__file__).parent / 'pdfs'

def importacao_documentos() -> list:
    """Importa documentos PDF da pasta especificada.

    Returns:
        list: Lista de documentos carregados.
    """
    documentos = []
    for arquivo in PASTA_ARQUIVOS.glob('*.pdf'):
        loader = PyPDFLoader(str(arquivo))
        documentos_arquivo = loader.load()
        if documentos_arquivo:
            documentos.extend(documentos_arquivo)
    if not documentos:
        raise ValueError("Nenhum documento foi carregado.")
    return documentos

def split_de_documentos(documentos: list) -> list:
    """Divide documentos em partes menores.

    Args:
        documentos (list): Lista de documentos a serem divididos.

    Returns:
        list: Lista de documentos divididos.
    """
    recur_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,
        chunk_overlap=250,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    documentos_divididos = recur_splitter.split_documents(documentos)

    # Adiciona metadados a cada documento
    for i, doc in enumerate(documentos_divididos):
        doc.metadata['source'] = doc.metadata['source'].split('/')[-1]
        doc.metadata['doc_id'] = i

    if not documentos_divididos:
        raise ValueError("Nenhum documento foi dividido.")
    return documentos_divididos

def cria_vector_store(documentos: list) -> FAISS:
    """Cria um vetor de armazenamento a partir dos documentos.

    Args:
        documentos (list): Lista de documentos.

    Returns:
        FAISS: Armazenamento vetorial criado.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY não está definido")

    embedding_model = OpenAIEmbeddings(api_key=openai_api_key)
    vector_store = FAISS.from_documents(
        documents=documentos,
        embedding=embedding_model
    )
    
    # Verificar se embeddings foram gerados
    if vector_store.index.ntotal == 0:
        raise ValueError("Nenhum embedding foi gerado.")
    return vector_store

def cria_chain_conversa() -> None:
    """Cria a cadeia de conversa para o chatbot."""
    documentos = importacao_documentos()
    documentos = split_de_documentos(documentos)
    vector_store = cria_vector_store(documentos)

    # Inicializa o modelo de chat
    chat = ChatOpenAI(model=get_config('model_name'))
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key='chat_history',
        output_key='answer'
    )
    
    # Configura o recuperador de documentos
    retriever = vector_store.as_retriever(
        search_type=get_config('retrieval_search_type'),
        search_kwargs=get_config('retrieval_kwargs')
    )
    
    # Configura o prompt
    prompt = PromptTemplate.from_template(get_config('prompt'))
    
    # Cria a cadeia de recuperação conversacional
    chat_chain = ConversationalRetrievalChain.from_llm(
        llm=chat,
        memory=memory,
        retriever=retriever,
        return_source_documents=True,
        verbose=True,
        combine_docs_chain_kwargs={'prompt': prompt}
    )

    # Armazena a cadeia de conversa no estado da sessão
    st.session_state['chain'] = chat_chain

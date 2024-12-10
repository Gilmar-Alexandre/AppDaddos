import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression
from carregar_dados import leitura_de_dados

st.set_page_config(page_title="Gestão de Contratos", layout="wide")

# Carrega os dados
leitura_de_dados()

# Acesso aos dados carregados
dados = st.session_state['dados']
df = dados['df_contratos']

# Exemplo de visualização de dados
st.title("Dashboard de Gestão de Contratos")

def process_data(df):
    """Processa os dados agrupando por contrato e somando valores relevantes."""
    grouped_df = df.groupby('CONTRATO Nº').agg({
        'EMPRESA': 'first',
        'SISTEMA': 'first',
        'MÊS': 'first',
        'ÍNDICE': 'first',
        'VALOR PAGO': 'sum',
        'VALOR REAJUSTADO': 'sum',
        'PEDIDO/ORDEM DE COMPRAS': 'first',
        'STATUS / AÇÃO': 'first',
        'DIFERENÇA DE VALOR DE CONTRATO': 'sum'
    }).reset_index()

    value_columns = [
        'VALOR PAGO',
        'VALOR REAJUSTADO',
        'DIFERENÇA DE VALOR DE CONTRATO'
    ]

    for col in value_columns:
        grouped_df[col] = grouped_df[col].astype(float)

    return grouped_df

grouped_df = process_data(df)

# Barra Lateral
with st.sidebar:
    st.header("Filtros")
    
    status = grouped_df['STATUS / AÇÃO'].unique()
    selected_status = st.multiselect("Selecione o Status", options=status, default=status)
    
    meses = sorted(grouped_df['MÊS'].unique())
    selected_months = st.multiselect("Selecione o mês", options=meses, default=meses)

# Filtrando os dados com base nos filtros selecionados
filtered_df = grouped_df[
    (grouped_df['STATUS / AÇÃO'].isin(selected_status)) &
    (grouped_df['MÊS'].isin(selected_months))
]

# Função para formatar valores no formato brasileiro
def format_currency(value):
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Calculando os valores das métricas
def calculate_metrics(df):
    """Calcula as métricas a partir do DataFrame filtrado."""
    valor_previsto = df['VALOR REAJUSTADO'].sum()
    valor_renovado = df[df['STATUS / AÇÃO'] == 'RENOVADO']['VALOR REAJUSTADO'].sum()
    valor_em_processo = df[df['STATUS / AÇÃO'] == 'EM PROCESSO']['VALOR REAJUSTADO'].sum()
    valor_cancelado = df[df['STATUS / AÇÃO'] == 'CANCELADO']['VALOR REAJUSTADO'].sum()

    # Calcular a diferença entre valor pago e valor reajustado para os cancelados
    df_cancelado = df[df['STATUS / AÇÃO'] == 'CANCELADO']
    diferenca_cancelado = (df_cancelado['VALOR REAJUSTADO'] - df_cancelado['VALOR PAGO']).sum()

    # Calcular a diferença entre valor pago e valor reajustado para os renovados
    df_renovado = df[df['STATUS / AÇÃO'] == 'RENOVADO']
    diferenca_renovado = (df_renovado['VALOR REAJUSTADO'] - df_renovado['VALOR PAGO']).sum()

    # Calcular a diferença entre valor pago e valor reajustado para os em processo
    df_em_processo = df[df['STATUS / AÇÃO'] == 'EM PROCESSO']
    diferenca_em_processo = (df_em_processo['VALOR REAJUSTADO'] - df_em_processo['VALOR PAGO']).sum()

    # Calcular o percentual de renovação
    total_contratos = len(df)
    total_renovados = len(df_renovado)
    percentual_renovacao = (total_renovados / total_contratos) * 100 if total_contratos > 0 else 0

    return {
        "valor_previsto": valor_previsto,
        "valor_renovado": valor_renovado,
        "valor_em_processo": valor_em_processo,
        "valor_cancelado": valor_cancelado,
        "diferenca_cancelado": diferenca_cancelado,
        "diferenca_renovado": diferenca_renovado,
        "diferenca_em_processo": diferenca_em_processo,
        "percentual_renovacao": percentual_renovacao
    }

# Calculando as métricas
metrics = calculate_metrics(filtered_df)

# Exibindo as métricas
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Valor Previsto", value=format_currency(metrics["valor_previsto"]))

with col2:
    st.metric(label="Valor Renovado", value=format_currency(metrics["valor_renovado"]), delta=format_currency(metrics["diferenca_renovado"]), delta_color="normal")

with col3:
    st.metric(label="Valor em Processo", value=format_currency(metrics["valor_em_processo"]), delta=format_currency(metrics["diferenca_em_processo"]), delta_color="normal")

with col4:
    st.metric(
        label="Valor Cancelado",
        value=format_currency(metrics["valor_cancelado"]),
        delta=format_currency(metrics["diferenca_cancelado"]),
        delta_color="inverse"
    )

with col5:
    st.metric(
        label="Percentual de Renovação",
        value=f"{metrics['percentual_renovacao']:.2f}%",
        delta=None
    )

# Funções de plotagem
def plot_value_acrescentado(df):
    df['ACRESCIMO_REAJUSTE'] = df['VALOR REAJUSTADO'] - df['VALOR PAGO']
    month_order = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
    df['MÊS'] = pd.Categorical(df['MÊS'], categories=month_order, ordered=True)
    monthly_acrescimento = df.groupby('MÊS').agg({'ACRESCIMO_REAJUSTE': 'sum'}).reset_index()
    monthly_acrescimento = monthly_acrescimento.sort_values('MÊS')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_acrescimento['MÊS'],
        y=monthly_acrescimento['ACRESCIMO_REAJUSTE'],
        mode='lines+markers+text',
        line=dict(color='darkblue', width=2, shape='spline'),
        text=monthly_acrescimento['ACRESCIMO_REAJUSTE'],
        texttemplate='%{text:.2s}',
        textposition='top center',
        marker=dict(symbol='circle', size=8, color='royalblue')
    ))

    total_acrescimo = monthly_acrescimento['ACRESCIMO_REAJUSTE'].sum()
    fig.add_annotation(
        text=f"Total Acréscimo: {format_currency(total_acrescimo)}",
        xref="paper", yref="paper",
        x=0.5, y=1.1, showarrow=False,
        font=dict(size=18, color="white")
    )

    fig.update_layout(
        title="Acréscimo no Reajuste por Mês",
        xaxis_title='Mês',
        yaxis_title='Valor Acrescentado (R$)',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showline=False, showgrid=False, zeroline=False,
            categoryorder='array', categoryarray=month_order
        ),
        yaxis=dict(showline=False, showgrid=False, zeroline=False)
    )

    return fig

def plot_index_analysis(df):
    index_summary = df.groupby('ÍNDICE').agg({
        'VALOR PAGO': 'mean',
        'VALOR REAJUSTADO': 'mean'
    }).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=index_summary['ÍNDICE'],
        y=index_summary['VALOR PAGO'],
        name='Valor Pago',
        marker_color='lightcyan'
    ))

    fig.add_trace(go.Scatter(
        x=index_summary['ÍNDICE'],
        y=index_summary['VALOR REAJUSTADO'],
        name='Valor Reajustado',
        mode='lines+markers',
        line=dict(color='darkblue', width=2),
    ))

    fig.update_layout(
        title="Percentual de Indice de Reajuste",
        xaxis=dict(showline=False, showgrid=False, zeroline=False),
        yaxis=dict(showline=False, showgrid=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

def plot_contracts_per_month(df):
    contracts_per_month = df.groupby('MÊS').size().reset_index(name='TOTAL DE CONTRATOS')
    months_order = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
                    'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
    contracts_per_month['MÊS'] = pd.Categorical(contracts_per_month['MÊS'], categories=months_order, ordered=True)
    contracts_per_month = contracts_per_month.sort_values('MÊS')

    fig = px.bar(contracts_per_month, x='MÊS', y='TOTAL DE CONTRATOS',
                 labels={'TOTAL DE CONTRATOS': 'Total de Contratos', 'MÊS': 'Mês'},
                 color='TOTAL DE CONTRATOS',
                 color_discrete_sequence=['royalblue'])

    fig.update_traces(texttemplate='%{y}', textposition='outside')

    fig.update_layout(
        title="Total de Contratos por Mês",
        xaxis=dict(showline=False, showgrid=False, zeroline=False),
        yaxis=dict(showline=False, showgrid=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    return fig

def plot_pie_chart(df):
    status_counts = df['STATUS / AÇÃO'].value_counts().reset_index()
    status_counts.columns = ['STATUS / AÇÃO', 'COUNT']

    fig = go.Figure(go.Pie(
        labels=status_counts['STATUS / AÇÃO'],
        values=status_counts['COUNT'],
        hole=0.5,
        marker=dict(colors=['royalblue', 'darkblue', 'lightcyan']),
        textinfo='none'
    ))

    fig.update_layout(
        title="Distribuição por Status",
        annotations=[dict(text=f'Total: {status_counts["COUNT"].sum()}', x=0.5, y=0.5, font_size=18, showarrow=False)]
    )

    return fig

def plot_regression_chart(df):
    df['DIFERENÇA'] = df['VALOR REAJUSTADO'] - df['VALOR PAGO']

    X = df[['VALOR PAGO']]
    y = df['DIFERENÇA']

    reg = LinearRegression()
    reg.fit(X, y)

    df['PREDICTED_DIFERENÇA'] = reg.predict(X)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['VALOR PAGO'],
        y=df['DIFERENÇA'],
        mode='markers',
        name='Diferença Observada',
        marker=dict(color='royalblue', size=10, opacity=0.6),
        text=[f"Contrato: {row['CONTRATO Nº']}, Empresa: {row['EMPRESA']}" for idx, row in df.iterrows()]
    ))

    fig.add_trace(go.Scatter(
        x=df['VALOR PAGO'],
        y=df['PREDICTED_DIFERENÇA'],
        mode='lines',
        name='Diferença Estimada',
        line=dict(color='darkblue', width=2)
    ))

    fig.update_layout(
        title="Diferença de Valor em Relação ao Valor Pago",
        xaxis_title="Valor Pago",
        yaxis_title="Diferença de Valor",
        xaxis=dict(showline=True, showgrid=False, zeroline=False),
        yaxis=dict(showline=True, showgrid=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

# Gráficos
col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(plot_value_acrescentado(filtered_df), use_container_width=True)
with col2:
    st.plotly_chart(plot_pie_chart(filtered_df), use_container_width=True)
with col3:
    st.plotly_chart(plot_regression_chart(filtered_df), use_container_width=True)

col4, col5 = st.columns(2)

with col4:
    st.plotly_chart(plot_contracts_per_month(filtered_df), use_container_width=True)
with col5:
    st.plotly_chart(plot_index_analysis(filtered_df), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Painel de Indústrias de Alagoas",
    layout="wide"
)

# Pasta onde o app.py está localizado
BASE_DIR = Path(__file__).resolve().parent


@st.cache_data
def load_data():
    arquivo = BASE_DIR / "industrias_ativas.xlsx"
    
    if not arquivo.exists():
        st.error(f"Arquivo não encontrado: {arquivo}")
        st.stop()
    
    return pd.read_excel(
        arquivo,
        sheet_name="Planilha1"
    )


# Carregar dados
df = load_data()

# Filtro lateral por Porte
st.sidebar.header("Filtros")
portes_disponiveis = df['Porte'].unique().tolist()
porte_selecionado = st.sidebar.multiselect("Selecione o Porte:", portes_disponiveis, default=portes_disponiveis)

# Filtrando o DataFrame
df_filtrado = df[df['Porte'].isin(porte_selecionado)]

# --- SEÇÃO DOS GRÁFICOS PRINCIPAIS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 15 Municípios com Mais Indústrias")
    top_munis = df_filtrado['Municipio'].value_counts().head(15).reset_index()
    top_munis.columns = ['Municipio', 'Quantidade']
    
    fig_bar = px.bar(
        top_munis, 
        x='Quantidade', 
        y='Municipio', 
        orientation='h',
        text='Quantidade',
        color='Quantidade',
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, width='stretch')

with col2:
    st.subheader("Distribuição Geral por Porte")
    porte_counts = df_filtrado['Porte'].value_counts().reset_index()
    porte_counts.columns = ['Porte', 'Quantidade']
    
    fig_pie = px.pie(
        porte_counts, 
        names='Porte', 
        values='Quantidade', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_pie, width='stretch')

# --- TABELA DETALHADA ---
st.subheader("📋 Tabela Resumo Consolidada por Município")
tabela_resumo = pd.crosstab(df_filtrado['Municipio'], df_filtrado['Porte']).reset_index()
tabela_resumo['Total'] = tabela_resumo.select_dtypes(include=['number']).sum(axis=1)
tabela_resumo = tabela_resumo.sort_values(by='Total', ascending=False)

st.dataframe(tabela_resumo, width='stretch')

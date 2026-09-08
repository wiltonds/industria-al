import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Inteligência Industrial — Alagoas",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO = BASE_DIR / "industrias_ativas_sebrae.xlsx"


# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>

    .main {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1 {
        font-size: 2.2rem !important;
    }

    .kpi {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .kpi-title {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 5px;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# CARREGAR DADOS
# ============================================================

@st.cache_data
def carregar_dados():

    if not ARQUIVO.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n{ARQUIVO}"
        )

    df = pd.read_excel(ARQUIVO)

    # --------------------------------------------------------
    # Limpeza básica
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Garantir colunas esperadas
    colunas_esperadas = [
        "cnpj",
        "situacao_atual",
        "razao_social",
        "SETOR",
        "CNAE PRIMARIO",
        "Porte",
        "Municipio",
        "SESI",
        "SENAI",
        "cnae_norm",
        "cnae_divisao",
        "secao",
        "setor",
        "subsetor",
        "elegivel_sebrae",
        "oportunidade_comercial"
    ]

    faltantes = [
        c for c in colunas_esperadas
        if c not in df.columns
    ]

    if faltantes:

        st.warning(
            "Colunas não encontradas: "
            + ", ".join(faltantes)
        )

    # --------------------------------------------------------
    # Criar indicadores SESI/SENAI
    # --------------------------------------------------------

    if "SESI" in df.columns:

        df["tem_sesi"] = (
            df["SESI"]
            .notna()
            &
            df["SESI"]
            .astype(str)
            .str.strip()
            .ne("")
            &
            df["SESI"]
            .astype(str)
            .str.strip()
            .ne("nan")
        )

    else:

        df["tem_sesi"] = False


    if "SENAI" in df.columns:

        df["tem_senai"] = (
            df["SENAI"]
            .notna()
            &
            df["SENAI"]
            .astype(str)
            .str.strip()
            .ne("")
            &
            df["SENAI"]
            .astype(str)
            .str.strip()
            .ne("nan")
        )

    else:

        df["tem_senai"] = False


    # --------------------------------------------------------
    # Recalcular classificação comercial
    # --------------------------------------------------------

    def classificar(row):

        elegivel = str(
            row.get("elegivel_sebrae", "")
        ).strip().upper()

        if elegivel != "SIM":
            return "FORA DO ESCOPO SEBRAE"

        sesi = row["tem_sesi"]
        senai = row["tem_senai"]

        if sesi and senai:
            return "CLIENTE SESI + SENAI"

        if sesi and not senai:
            return "CLIENTE SESI / OPORTUNIDADE SENAI"

        if not sesi and senai:
            return "CLIENTE SENAI / OPORTUNIDADE SESI"

        return "OPORTUNIDADE NOVA"


    df["oportunidade_comercial"] = df.apply(
        classificar,
        axis=1
    )

    return df


# ============================================================
# CARREGAMENTO
# ============================================================

try:

    df = carregar_dados()

except Exception as e:

    st.error(
        f"Erro ao carregar a base:\n\n{e}"
    )

    st.stop()


# ============================================================
# CABEÇALHO
# ============================================================

st.title("🏭 Inteligência Industrial — Alagoas")

st.caption(
    "Exploração comercial da base industrial "
    "com cruzamento SEBRAE × SESI × SENAI"
)


# ============================================================
# MODO PRINCIPAL
# ============================================================

modo = st.radio(
    "Universo de análise",
    [
        "TODAS AS INDÚSTRIAS",
        "SEBRAE"
    ],
    horizontal=True
)


# ============================================================
# FILTRO SEBRAE
# ============================================================

if modo == "SEBRAE":

    df_view = df[
        df["elegivel_sebrae"]
        .astype(str)
        .str.upper()
        .str.strip()
        .eq("SIM")
    ].copy()

else:

    df_view = df.copy()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filtros")


def opcoes(coluna):

    if coluna not in df_view.columns:
        return ["Todos"]

    valores = (
        df_view[coluna]
        .dropna()
        .astype(str)
        .str.strip()
    )

    valores = valores[
        valores.ne("")
        & valores.ne("nan")
    ]

    return ["Todos"] + sorted(
        valores.unique().tolist()
    )


# Município

municipio = st.sidebar.selectbox(
    "Município",
    opcoes("Municipio")
)


# Setor

setor = st.sidebar.selectbox(
    "Setor",
    opcoes("setor")
)


# Subsetor

subsetor = st.sidebar.selectbox(
    "Subsetor",
    opcoes("subsetor")
)


# Porte

porte = st.sidebar.selectbox(
    "Porte",
    opcoes("Porte")
)


# Relacionamento

relacionamento = st.sidebar.selectbox(
    "Relacionamento SESI/SENAI",
    [
        "Todos",
        "OPORTUNIDADE NOVA",
        "CLIENTE SESI / OPORTUNIDADE SENAI",
        "CLIENTE SENAI / OPORTUNIDADE SESI",
        "CLIENTE SESI + SENAI",
        "FORA DO ESCOPO SEBRAE"
    ]
)


# ============================================================
# APLICAR FILTROS
# ============================================================

if municipio != "Todos":

    df_view = df_view[
        df_view["Municipio"]
        .astype(str)
        .str.strip()
        .eq(municipio)
    ]


if setor != "Todos":

    df_view = df_view[
        df_view["setor"]
        .astype(str)
        .str.strip()
        .eq(setor)
    ]


if subsetor != "Todos":

    df_view = df_view[
        df_view["subsetor"]
        .astype(str)
        .str.strip()
        .eq(subsetor)
    ]


if porte != "Todos":

    df_view = df_view[
        df_view["Porte"]
        .astype(str)
        .str.strip()
        .eq(porte)
    ]


if relacionamento != "Todos":

    df_view = df_view[
        df_view["oportunidade_comercial"]
        .eq(relacionamento)
    ]


# ============================================================
# KPIs
# ============================================================

total = len(df_view)

clientes_sesi = int(
    df_view["tem_sesi"].sum()
)

clientes_senai = int(
    df_view["tem_senai"].sum()
)

clientes_dois = int(
    (
        df_view["tem_sesi"]
        &
        df_view["tem_senai"]
    ).sum()
)

oportunidades = int(
    (
        df_view["oportunidade_comercial"]
        == "OPORTUNIDADE NOVA"
    ).sum()
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Empresas no universo",
        f"{total:,}".replace(",", ".")
    )


with col2:

    st.metric(
        "Clientes SESI",
        f"{clientes_sesi:,}".replace(",", ".")
    )


with col3:

    st.metric(
        "Clientes SENAI",
        f"{clientes_senai:,}".replace(",", ".")
    )


with col4:

    st.metric(
        "SESI + SENAI",
        f"{clientes_dois:,}".replace(",", ".")
    )


with col5:

    st.metric(
        "Oportunidades novas",
        f"{oportunidades:,}".replace(",", ".")
    )


st.divider()


# ============================================================
# MATRIZ SESI × SENAI
# ============================================================

st.subheader("Matriz de relacionamento")

m1, m2 = st.columns(2)


with m1:

    matriz = pd.DataFrame({

        "": [
            "Não possui SESI",
            "Possui SESI"
        ],

        "Não possui SENAI": [
            int(
                (
                    ~df_view["tem_sesi"]
                    &
                    ~df_view["tem_senai"]
                ).sum()
            ),

            int(
                (
                    df_view["tem_sesi"]
                    &
                    ~df_view["tem_senai"]
                ).sum()
            )
        ],

        "Possui SENAI": [
            int(
                (
                    ~df_view["tem_sesi"]
                    &
                    df_view["tem_senai"]
                ).sum()
            ),

            int(
                (
                    df_view["tem_sesi"]
                    &
                    df_view["tem_senai"]
                ).sum()
            )
        ]
    })

    st.dataframe(
        matriz,
        use_container_width=True,
        hide_index=True
    )


with m2:

    st.markdown("### Leitura comercial")

    st.markdown(
        f"""
        **🟢 Oportunidade nova:**  
        {(
            ~df_view["tem_sesi"]
            &
            ~df_view["tem_senai"]
        ).sum():,} empresas

        **🟡 Cliente SESI → oportunidade SENAI:**  
        {(
            df_view["tem_sesi"]
            &
            ~df_view["tem_senai"]
        ).sum():,} empresas

        **🟠 Cliente SENAI → oportunidade SESI:**  
        {(
            ~df_view["tem_sesi"]
            &
            df_view["tem_senai"]
        ).sum():,} empresas

        **🔵 Cliente SESI + SENAI:**  
        {(
            df_view["tem_sesi"]
            &
            df_view["tem_senai"]
        ).sum():,} empresas
        """
    )


st.divider()


# ============================================================
# GRÁFICOS
# ============================================================

col_g1, col_g2 = st.columns(2)


with col_g1:

    st.subheader("Empresas por setor")

    if "setor" in df_view.columns:

        dados_setor = (
            df_view["setor"]
            .fillna("Não informado")
            .value_counts()
            .head(15)
        )

        st.bar_chart(dados_setor)


with col_g2:

    st.subheader("Empresas por município")

    if "Municipio" in df_view.columns:

        dados_municipio = (
            df_view["Municipio"]
            .fillna("Não informado")
            .value_counts()
            .head(15)
        )

        st.bar_chart(dados_municipio)


# ============================================================
# OPORTUNIDADES POR TIPO
# ============================================================

st.subheader("Distribuição das oportunidades")

dados_oportunidade = (
    df_view["oportunidade_comercial"]
    .value_counts()
)

st.bar_chart(dados_oportunidade)


# ============================================================
# PRINCIPAIS CNAEs
# ============================================================

st.subheader("Principais CNAEs")

if "cnae_norm" in df_view.columns:

    dados_cnae = (
        df_view
        .groupby(
            [
                "cnae_norm",
                "CNAE PRIMARIO"
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="empresas"
        )
        .sort_values(
            "empresas",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        dados_cnae,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TABELA DE EMPRESAS
# ============================================================

st.divider()

st.subheader(
    f"Empresas encontradas ({len(df_view):,})"
)


colunas_tabela = [
    "cnpj",
    "razao_social",
    "Municipio",
    "Porte",
    "CNAE PRIMARIO",
    "setor",
    "subsetor",
    "SESI",
    "SENAI",
    "elegivel_sebrae",
    "oportunidade_comercial"
]


colunas_tabela = [
    c for c in colunas_tabela
    if c in df_view.columns
]


tabela = df_view[colunas_tabela].copy()


st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
    height=500
)


# ============================================================
# DOWNLOAD
# ============================================================

csv = df_view.to_csv(
    index=False,
    encoding="utf-8-sig"
)


st.download_button(
    label="⬇️ Baixar empresas filtradas",
    data=csv,
    file_name="empresas_oportunidades_sebrae.csv",
    mime="text/csv"
)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Inteligência Industrial — Alagoas | "
    "Base CNPJ + CNAE + SEBRAE + SESI + SENAI"
)
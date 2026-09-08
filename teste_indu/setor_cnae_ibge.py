"""
setor_cnae_ibge.py
==================

Classificacao setorial deterministica a partir do CNAE primario,
seguindo a estrutura de secoes e divisoes da CNAE 2.0 (IBGE).

Cobre TODAS as secoes (A..U, divisoes 01-99) -> nenhuma linha fica orfa.
Cada CNPJ recebe o setor real da sua atividade economica.

Dois conceitos SEPARADOS, de proposito:
  - setor       : a atividade economica real (IBGE). Ex.: "Comercio...",
                  "Industria de transformacao", "Transporte...".
  - e_industria : True/False -- se esse setor e industrial pelo IBGE
                  (secoes B, C, D, E, F). Nao confundir com o criterio
                  de contribuicao da CNI, que vive na tabela de referencia
                  (coluna "Industria CNI?") e diz POR QUE a empresa esta
                  na base -- coisa diferente de qual atividade ela exerce.

Filosofia (regra do projeto): setor e atributo legalmente ancorado ->
resolve-se por LOOKUP na arvore CNAE, nunca por inferencia de LLM.

Colunas geradas por classificar_setores():
    cnae_norm, cnae_divisao, secao, setor, subsetor, e_industria, auditoria
(auditoria = True apenas quando NAO foi possivel classificar: CNAE ausente
 ou invalido -- nao mais para "nao-industrial".)
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd


# ---------------------------------------------------------------------------
# 1) Normalizacao do CNAE
# ---------------------------------------------------------------------------
def normalizar_cnae(valor) -> Optional[str]:
    """CNAE apenas com digitos, 7 posicoes, ou None se invalido.
    "10.11-2/01" -> "1011201" | "0500-3/01" -> "0500301" | 1011201.0 -> "1011201"
    """
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    if isinstance(valor, float):
        valor = f"{valor:.0f}"
    digitos = re.sub(r"\D", "", str(valor))
    if not digitos:
        return None
    return digitos.zfill(7)


def divisao_cnae(cnae_norm) -> Optional[int]:
    """Divisao (2 primeiros digitos) como inteiro. Tolera NaN/float."""
    if cnae_norm is None or not isinstance(cnae_norm, str) or len(cnae_norm) < 2:
        return None
    return int(cnae_norm[:2])


# ---------------------------------------------------------------------------
# 2) Divisao -> Secao IBGE (A..U), cobrindo 01-99
# ---------------------------------------------------------------------------
def secao_ibge(divisao: Optional[int]) -> str:
    if divisao is None:
        return "Invalido"
    faixas = [
        (1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"),
        (41, 43, "F"), (45, 47, "G"), (49, 53, "H"), (55, 56, "I"), (58, 63, "J"),
        (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"), (84, 84, "O"),
        (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 97, "T"),
        (99, 99, "U"),
    ]
    for ini, fim, letra in faixas:
        if ini <= divisao <= fim:
            return letra
    return "Invalido"


SECAO_PARA_SETOR = {
    "A": "Agricultura, pecuaria e florestal",
    "B": "Industria extrativa",
    "C": "Industria de transformacao",
    "D": "Eletricidade e gas",
    "E": "Agua, esgoto e residuos",
    "F": "Construcao",
    "G": "Comercio e reparacao de veiculos",
    "H": "Transporte e armazenagem",
    "I": "Alojamento e alimentacao",
    "J": "Informacao e comunicacao",
    "K": "Atividades financeiras e seguros",
    "L": "Atividades imobiliarias",
    "M": "Atividades profissionais e tecnicas",
    "N": "Atividades administrativas e servicos",
    "O": "Administracao publica",
    "P": "Educacao",
    "Q": "Saude humana e servicos sociais",
    "R": "Artes, cultura, esporte e recreacao",
    "S": "Outras atividades de servicos",
    "T": "Servicos domesticos",
    "U": "Organismos internacionais",
    "Invalido": "Invalido / sem CNAE",
}

# Secoes que o IBGE considera industria
SECOES_INDUSTRIAIS = {"B", "C", "D", "E", "F"}


# ---------------------------------------------------------------------------
# 3) Subsetor (divisao nomeada) -- detalhado para as secoes industriais
# ---------------------------------------------------------------------------
DIVISAO_PARA_SUBSETOR = {
    5:  "Extracao de carvao mineral",
    6:  "Extracao de petroleo e gas natural",
    7:  "Extracao de minerais metalicos",
    8:  "Extracao de minerais nao-metalicos",
    9:  "Atividades de apoio a extracao de minerais",
    10: "Alimentos", 11: "Bebidas", 12: "Produtos do fumo", 13: "Produtos texteis",
    14: "Confeccao de vestuario e acessorios", 15: "Couros, artefatos e calcados",
    16: "Produtos de madeira", 17: "Celulose, papel e produtos de papel",
    18: "Impressao e reproducao de gravacoes",
    19: "Coque, derivados de petroleo e biocombustiveis", 20: "Produtos quimicos",
    21: "Produtos farmoquimicos e farmaceuticos", 22: "Borracha e material plastico",
    23: "Produtos de minerais nao-metalicos", 24: "Metalurgia",
    25: "Produtos de metal (exceto maquinas)", 26: "Informatica, eletronicos e opticos",
    27: "Maquinas, aparelhos e materiais eletricos", 28: "Maquinas e equipamentos",
    29: "Veiculos automotores, reboques e carrocerias", 30: "Outros equip. de transporte",
    31: "Moveis", 32: "Produtos diversos", 33: "Manutencao, reparacao e instalacao de maquinas",
    35: "Eletricidade, gas e outras utilidades",
    36: "Captacao, tratamento e distribuicao de agua", 37: "Esgoto e atividades relacionadas",
    38: "Coleta e tratamento de residuos", 39: "Descontaminacao e gestao de residuos",
    41: "Construcao de edificios", 42: "Obras de infraestrutura",
    43: "Servicos especializados para construcao",
}


def subsetor_ibge(divisao: Optional[int], setor: str) -> str:
    """Subsetor detalhado para industria; para nao-industria devolve o
    proprio setor (nome da secao), que ja e o grao util fora da industria."""
    if divisao is None:
        return "Invalido / sem CNAE"
    return DIVISAO_PARA_SUBSETOR.get(divisao, setor)


# ---------------------------------------------------------------------------
# 4) Aplicacao no DataFrame
# ---------------------------------------------------------------------------
def classificar_setores(df: pd.DataFrame, coluna_cnae: str = "cnae_primario") -> pd.DataFrame:
    if coluna_cnae not in df.columns:
        raise KeyError(
            f"Coluna '{coluna_cnae}' nao encontrada. Disponiveis: {list(df.columns)}"
        )
    out = df.copy()
    out["cnae_norm"] = out[coluna_cnae].map(normalizar_cnae)
    out["cnae_divisao"] = out["cnae_norm"].map(divisao_cnae)
    out["secao"] = out["cnae_divisao"].map(secao_ibge)
    out["setor"] = out["secao"].map(SECAO_PARA_SETOR)
    out["subsetor"] = out.apply(
        lambda r: subsetor_ibge(r["cnae_divisao"], r["setor"]), axis=1
    )
    out["e_industria"] = out["secao"].isin(SECOES_INDUSTRIAIS)
    # auditoria agora e so o que NAO deu para classificar (CNAE ausente/invalido)
    out["auditoria"] = out["secao"].eq("Invalido")
    return out


def relatorio_auditoria(df_classificado: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        df_classificado["setor"].value_counts(dropna=False)
        .rename_axis("setor").reset_index(name="qtd")
    )
    resumo["pct"] = (resumo["qtd"] / len(df_classificado) * 100).round(1)
    return resumo


# ---------------------------------------------------------------------------
# 5) Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    exemplo = pd.DataFrame({
        "cnpj": ["001", "002", "003", "004", "005", "006", "007"],
        "cnae_primario": [
            "10.11-2/01",   # Transformacao - Alimentos (industria)
            "0500-3/01",    # Extrativa - carvao (industria)
            "4120-4/00",    # Construcao (industria)
            "4711-3/02",    # Comercio (NAO industria -> agora setor proprio)
            "7112-0/00",    # Servicos de engenharia (NAO industria)
            "6110-8/03",    # Telecom (NAO industria)
            None,           # invalido -> auditoria
        ],
    })
    r = classificar_setores(exemplo, coluna_cnae="cnae_primario")
    cols = ["cnpj", "cnae_primario", "secao", "setor", "e_industria", "auditoria"]
    print(r[cols].to_string(index=False))
    print("\n--- Resumo ---")
    print(relatorio_auditoria(r).to_string(index=False))
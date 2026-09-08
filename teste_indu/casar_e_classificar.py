"""
casar_e_classificar.py
=======================

Sua base (industrias_ativas.xlsx) so tem a DESCRICAO do CNAE, nao o codigo.
Este script recupera o codigo casando a descricao contra a tabela de
referencia da CNI (CNAE Industrial CNI 2023.xlsx), que tem descricao +
codigo lado a lado. Com o codigo na mao, classifica o setor pela divisao.

Fluxo:
  base[CNAE PRIMARIO]  --casa por texto normalizado-->  CNI[subclasse_cnae_descricao]
                                                        --> puxa subclasse_cnae_codigo
                                                        --> classifica setor (modulo)

Saidas:
  - industrias_ativas_classificado.xlsx  (base + codigo + setor + subsetor)
  - nao_casados.xlsx                      (linhas cuja descricao nao bateu)

Rode dentro da pasta teste_indu:
    python casar_e_classificar.py
"""

import re
import unicodedata

import pandas as pd

from setor_cnae_ibge import classificar_setores, relatorio_auditoria

# ---------------------------------------------------------------------------
# Ajuste aqui se os nomes dos arquivos ou colunas forem diferentes
# ---------------------------------------------------------------------------
ARQ_BASE = "industrias_ativas.xlsx"
ARQ_CNI = "CNAE Industrial CNI 2023.xlsx"

COL_DESC_BASE = "CNAE PRIMARIO"                # descricao na SUA base
COL_DESC_CNI = "subclasse_cnae_descricao"      # descricao na referencia CNI
COL_COD_CNI = "subclasse_cnae_codigo"          # codigo na referencia CNI


# ---------------------------------------------------------------------------
# Normalizacao de texto: o casamento quebra no detalhe invisivel.
# Tira acento, poe em maiuscula, colapsa espacos, remove pontuacao final.
# Aplicado nos DOIS lados para que "Fabricacao de X " case com "Fabricacao de X".
# ---------------------------------------------------------------------------
def normalizar_texto(s) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    # remove acentos (NFKD separa o acento da letra; encode ascii descarta)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)          # colapsa espacos multiplos
    s = re.sub(r"[.;,]+$", "", s)       # tira pontuacao no fim
    return s


def main():
    # 1. Ler as duas planilhas
    base = pd.read_excel(ARQ_BASE)
    cni = pd.read_excel(ARQ_CNI, header=1)

    print(f"Base: {len(base)} linhas | CNI: {len(cni)} linhas")

    for col, arq in [(COL_DESC_BASE, ARQ_BASE), (COL_DESC_CNI, ARQ_CNI), (COL_COD_CNI, ARQ_CNI)]:
        origem = base if arq == ARQ_BASE else cni
        if col not in origem.columns:
            raise KeyError(f"Coluna '{col}' nao existe em {arq}. Colunas: {list(origem.columns)}")

    # 2. Chave normalizada dos dois lados
    base["_chave"] = base[COL_DESC_BASE].map(normalizar_texto)
    cni["_chave"] = cni[COL_DESC_CNI].map(normalizar_texto)

    # 3. Tabela de-para descricao->codigo (sem duplicatas de chave)
    depara = (
        cni.drop_duplicates(subset="_chave")[["_chave", COL_COD_CNI]]
        .rename(columns={COL_COD_CNI: "cnae_codigo_recuperado"})
    )

    # 4. Casar (left join: mantem todas as linhas da base)
    base = base.merge(depara, on="_chave", how="left")

    total = len(base)
    casou = base["cnae_codigo_recuperado"].notna().sum()
    print(f"\nCasamento por descricao: {casou}/{total} ({casou/total*100:.1f}%)")

    # 5. Classificar setor a partir do codigo recuperado
    base = classificar_setores(base, coluna_cnae="cnae_codigo_recuperado")

    # 6. Relatorios
    print("\n--- Distribuicao por setor ---")
    print(relatorio_auditoria(base).to_string(index=False))

    nao_casados = base[base["cnae_codigo_recuperado"].isna()]
    if len(nao_casados):
        print(f"\n--- {len(nao_casados)} descricoes NAO casaram (amostra) ---")
        print(nao_casados[COL_DESC_BASE].drop_duplicates().head(15).to_string(index=False))
        nao_casados.to_excel("nao_casados.xlsx", index=False)
        print("\nSalvo: nao_casados.xlsx (para investigar)")

    # 7. Salvar base classificada (tira a coluna interna _chave)
    base.drop(columns="_chave").to_excel("industrias_ativas_classificado.xlsx", index=False)
    print("\nPronto: industrias_ativas_classificado.xlsx")


if __name__ == "__main__":
    main()
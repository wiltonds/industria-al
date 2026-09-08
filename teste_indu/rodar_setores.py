import pandas as pd
from setor_cnae_ibge import classificar_setores, relatorio_auditoria

# 1. Ler a tabela (troque o nome do arquivo pelo seu)
df = pd.read_excel("industrias_ativas.xlsx")   # se for .csv: pd.read_csv("arquivo.csv", sep=";")

# 2. Ver como as colunas se chamam de verdade
print(df.columns.tolist())

# 3. Classificar (ajuste 'cnae_primario' pro nome real da coluna de CNAE)
df = classificar_setores(df, coluna_cnae="CNAE PRIMARIO")

# 4. Conferir a distribuição — "Fora do escopo" tem que ser baixo
print(relatorio_auditoria(df))

# 5. Salvar cópia nova, sem mexer no original
df.to_excel("industrias_ativas_AL_com_setor.xlsx", index=False)
print("Pronto: industrias_ativas_AL_com_setor.xlsx")
"""
painel.py
=========

Le a base ja classificada (industrias_ativas_classificado.xlsx) e gera
um painel HTML local com contagens por SETOR, PORTE e MUNICIPIO, mais
o cruzamento SETOR x PORTE. Abre no navegador automaticamente.

Sem dependencia de internet nem lib de grafico: as barras sao calculadas
em Python e viram HTML/CSS puro. Reflete sempre o dado atual do arquivo.

Rode dentro da pasta teste_indu:
    python painel.py
"""

import webbrowser
from pathlib import Path

import pandas as pd

ARQ = "industrias_ativas_classificado.xlsx"
TOP_MUNICIPIOS = 15


def fmt(n):
    """Numero no padrao brasileiro: 32926 -> 32.926."""
    return f"{n:,}".replace(",", ".")


def achar_coluna(df, candidatos):
    """Acha a coluna ignorando maiuscula/minuscula e espacos."""
    norm = {c.strip().lower(): c for c in df.columns}
    for cand in candidatos:
        if cand.lower() in norm:
            return norm[cand.lower()]
    raise KeyError(f"Nenhuma de {candidatos} encontrada. Colunas: {list(df.columns)}")


def barras(series, total, cor="#378ADD"):
    """Gera as linhas de barra HTML para uma Series (rotulo -> contagem)."""
    if len(series) == 0:
        return "<p>(sem dados)</p>"
    maximo = series.max()
    linhas = []
    for rotulo, qtd in series.items():
        larg = qtd / maximo * 100
        pct = qtd / total * 100
        linhas.append(f"""
        <div class="linha">
          <div class="rotulo" title="{rotulo}">{rotulo}</div>
          <div class="trilha"><div class="barra" style="width:{larg:.1f}%;background:{cor}"></div></div>
          <div class="valor">{fmt(qtd)}<span class="pct">{pct:.1f}%</span></div>
        </div>""")
    return "".join(linhas)


def heatmap(cross):
    """Tabela setor x porte colorida por intensidade (sequencial azul)."""
    maximo = cross.values.max() if cross.size else 1
    stops = ["#E6F1FB", "#B5D4F4", "#85B7EB", "#378ADD", "#185FA5"]
    texto = ["#185FA5", "#0C447C", "#042C53", "#fff", "#fff"]

    def cor(v):
        if maximo == 0:
            return 0
        frac = v / maximo
        idx = min(int(frac * len(stops)), len(stops) - 1)
        return idx

    cab = "".join(f"<th>{c}</th>" for c in cross.columns)
    linhas = []
    for setor, row in cross.iterrows():
        cels = []
        for v in row:
            i = cor(v)
            vtxt = fmt(v) if v else "-"
            cels.append(f'<td style="background:{stops[i]};color:{texto[i]}">{vtxt}</td>')
        linhas.append(f"<tr><th class='rowh'>{setor}</th>{''.join(cels)}</tr>")
    return f"<table class='hm'><thead><tr><th></th>{cab}</tr></thead><tbody>{''.join(linhas)}</tbody></table>"


def main():
    if not Path(ARQ).exists():
        raise FileNotFoundError(f"Nao achei {ARQ} nesta pasta. Rode primeiro o casar_e_classificar.py")

    df = pd.read_excel(ARQ)
    total = len(df)

    col_setor = achar_coluna(df, ["setor"])
    col_porte = achar_coluna(df, ["Porte", "porte"])
    col_muni = achar_coluna(df, ["Municipio", "municipio", "MUNICIPIO"])

    por_setor = df[col_setor].value_counts()
    por_porte = df[col_porte].value_counts()
    por_muni = df[col_muni].value_counts().head(TOP_MUNICIPIOS)
    cross = pd.crosstab(df[col_setor], df[col_porte])

    html = f"""<!DOCTYPE html><html lang="pt-br"><head><meta charset="utf-8">
<title>Panorama industrial AL</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:920px;margin:32px auto;padding:0 20px;color:#1a1a19}}
 h1{{font-size:22px;font-weight:500;margin:0 0 4px}}
 .sub{{color:#6b6a64;font-size:14px;margin:0 0 28px}}
 h2{{font-size:17px;font-weight:500;margin:32px 0 12px;border-bottom:1px solid #e5e4dd;padding-bottom:6px}}
 .kpis{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px}}
 .kpi{{background:#f4f3ee;border-radius:8px;padding:12px 16px;flex:1;min-width:150px}}
 .kpi .l{{font-size:13px;color:#6b6a64;margin-bottom:4px}}
 .kpi .n{{font-size:24px;font-weight:500}}
 .linha{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}}
 .rotulo{{width:230px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#3a3a37}}
 .trilha{{flex:1;background:#efeee8;border-radius:4px;height:20px}}
 .barra{{height:20px;border-radius:4px}}
 .valor{{width:110px;font-variant-numeric:tabular-nums}}
 .pct{{color:#8a8980;margin-left:6px;font-size:12px}}
 table.hm{{border-collapse:separate;border-spacing:3px;font-size:13px;margin-top:8px}}
 table.hm th{{font-weight:500;color:#6b6a64;padding:4px 8px}}
 table.hm th.rowh{{text-align:right;color:#3a3a37}}
 table.hm td{{text-align:center;padding:8px 12px;border-radius:6px;font-variant-numeric:tabular-nums;min-width:52px}}
</style></head><body>
<h1>Panorama industrial &mdash; Alagoas</h1>
<p class="sub">Base de {fmt(total)} empresas classificadas &middot; setor por CNAE/IBGE</p>
<div class="kpis">
 <div class="kpi"><div class="l">Total de empresas</div><div class="n">{fmt(total)}</div></div>
 <div class="kpi"><div class="l">Setores</div><div class="n">{por_setor.shape[0]}</div></div>
 <div class="kpi"><div class="l">Municipios</div><div class="n">{df[col_muni].nunique()}</div></div>
</div>
<h2>Por setor</h2>{barras(por_setor, total)}
<h2>Por porte</h2>{barras(por_porte, total, cor="#1D9E75")}
<h2>Top {TOP_MUNICIPIOS} municipios</h2>{barras(por_muni, total, cor="#BA7517")}
<h2>Setor &times; porte</h2>{heatmap(cross)}
</body></html>"""

    saida = Path("painel.html")
    saida.write_text(html, encoding="utf-8")
    print(f"Gerado: {saida.resolve()}")
    webbrowser.open(saida.resolve().as_uri())


if __name__ == "__main__":
    main()

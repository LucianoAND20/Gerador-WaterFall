import io
import re
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import plotly.graph_objects as go

# Dicionário de cores amigáveis para o usuário
DIC_CORES = {
    "Amarelo/Ouro": "#f1c40f",
    "Laranja": "#e67e22",
    "Verde Padrão": "#2ecc71",
    "Vermelho Padrão": "#e74c3c",
    "Azul Escuro": "#34495e",
    "Azul Claro": "#3498db",
    "Cinza": "#95a5a6",
    "Roxo": "#9b59b6",
}


def limpar_e_converter_valor(valor_str):
    if pd.isna(valor_str):
        return 0.0
    val_limpo = str(valor_str).strip()
    val_limpo = re.sub(r"[R\$\s]", "", val_limpo)
    if not val_limpo:
        return 0.0

    if "," in val_limpo and "." in val_limpo:
        val_limpo = val_limpo.replace(".", "").replace(",", ".")
    elif "," in val_limpo:
        val_limpo = val_limpo.replace(",", ".")

    try:
        return float(val_limpo)
    except ValueError:
        return 0.0


def formatar_quantidade(valor_str):
    """Remove caracteres não numéricos e formata com ponto separador de milhar brasileiro."""
    if pd.isna(valor_str):
        return "0"
    limpo = re.sub(r"[^\d-]", "", str(valor_str).strip())
    if not limpo:
        return "0"
    try:
        val_int = int(limpo)
        return f"{val_int:,}".replace(",", ".")
    except ValueError:
        return limpo


def obter_cor(combo, entrada_manual, cor_padrao_hex):
    manual = entrada_manual.get().strip()
    if manual:
        return manual
    nome_cor = combo.get()
    return DIC_CORES.get(nome_cor, cor_padrao_hex)


def gerar_grafico():
    conteudo_colado = txt_area.get("1.0", tk.END).strip()

    if not conteudo_colado:
        messagebox.showwarning(
            "Aviso", "Por favor, cole a tabela antes de gerar o gráfico!"
        )
        return

    # Captura os mapeamentos da tela
    col_nome = ent_col_nome.get().strip()
    col_valor = ent_col_valor.get().strip()
    col_volume = ent_col_volume.get().strip()
    termo_total = ent_termo_total.get().strip().lower()

    itens_fixos_texto = ent_itens_fixos.get().strip().lower()
    lista_itens_fixos = (
        [x.strip() for x in itens_fixos_texto.split(";")]
        if itens_fixos_texto
        else []
    )

    if not col_nome or not col_valor or not col_volume or not termo_total:
        messagebox.showerror(
            "Erro de Configuração",
            "Nenhum dos campos de mapeamento do Excel pode ficar vazio.",
        )
        return

    # Captura das cores configuradas na tela
    cor_b1_pos = obter_cor(cb_b1_pos, ent_b1_pos_manual, "#f1c40f")
    cor_b1_neg = obter_cor(cb_b1_neg, ent_b1_neg_manual, "#f1c40f")
    cor_b2_pos = obter_cor(cb_b2_pos, ent_b2_pos_manual, "#e67e22")
    cor_b2_neg = obter_cor(cb_b2_neg, ent_b2_neg_manual, "#e67e22")
    cor_final = obter_cor(cb_tot, ent_tot_manual, "#34495e")
    cor_fixas = obter_cor(cb_fixas, ent_fixas_manual, "#95a5a6")

    tamanho_fonte_eixos = int(cb_fonte_eixos.get())
    tamanho_fonte_numeros = int(cb_fonte_numeros.get())

    if var_ativar_linhas.get():
        cfg_connector = dict(
            line=dict(color="red", width=1.5, dash="dash"), visible=True
        )
    else:
        cfg_connector = dict(visible=False)

    try:
        df_original = pd.read_csv(io.StringIO(conteudo_colado), sep="\t")
        df_original.columns = df_original.columns.str.strip()

        if (
            col_nome not in df_original.columns
            or col_valor not in df_original.columns
            or col_volume not in df_original.columns
        ):
            messagebox.showerror(
                "Erro de Mapeamento",
                f"Não encontrei as colunas '{col_nome}', '{col_valor}' ou '{col_volume}' nos dados colados.",
            )
            return

        df_original["Valor_Num"] = df_original[col_valor].apply(limpar_e_converter_valor)

        # === REORDENAÇÃO CRONOLÓGICA DAS BARRAS HISTÓRICAS ===
        df_fixos = df_original[df_original[col_nome].astype(str).str.strip().str.lower().isin(lista_itens_fixos)].copy()
        df_fluxo = df_original[~df_original[col_nome].astype(str).str.strip().str.lower().isin(lista_itens_fixos)].copy()
        
        df = pd.concat([df_fixos, df_fluxo], ignore_index=True)
        lista_nomes_ordenados = df[col_nome].astype(str).str.strip().tolist()

        idx_total_meio = -1
        for idx, nome in enumerate(lista_nomes_ordenados):
            if nome.lower() == termo_total:
                idx_total_meio = idx
                break

        if idx_total_meio == -1:
            messagebox.showerror(
                "Erro de Estrutura",
                f"Não encontrei a linha intermediária '{ent_termo_total.get().strip()}' para dividir os blocos.",
            )
            return

        acumulado_bloco1 = 0.0
        for idx in range(idx_total_meio):
            if lista_nomes_ordenados[idx].lower() not in lista_itens_fixos:
                acumulado_dinamico = df.loc[idx, "Valor_Num"]
                acumulado_bloco1 += acumulado_dinamico

        # Usamos identificadores temporários no eixo X nativo para indexar as barras numericamente
        df["Eixo_X_ID"] = [f"B_{i}" for i in range(len(df))]
        ordem_eixo_x_id = df["Eixo_X_ID"].tolist()

        x_t1, y_t1, m_t1 = [], [], []
        x_t2, y_t2, m_t2 = [], [], []
        x_fx, y_fx, m_fx = [], [], []

        anotacoes = []
        corrente_y = 0.0

        for idx, row in df.iterrows():
            nome_original = str(row[col_nome]).strip()
            nome_id = str(row["Eixo_X_ID"]).strip()
            nome_lower = nome_original.lower()
            val_num = row["Valor_Num"]
            val_texto = str(row[col_valor]).strip()
            
            # Formata dinamicamente o volume com separador de milhar brasileiro (.)
            vol_texto = formatar_quantidade(row[col_volume])

            texto_interno = f"{val_texto}<br>Qtde {vol_texto}"
            posicao_x_base = idx 

            if nome_lower in lista_itens_fixos:
                inicio_interno_y = 0.0 if val_num >= 0 else val_num
                cor_texto = "white"
                pos_x_anotacao = posicao_x_base 
                
                x_fx.append(nome_id); y_fx.append(val_num); m_fx.append("absolute")

            elif idx == idx_total_meio:
                inicio_interno_y = 0.0
                val_acum_formatado = f"R$ {acumulado_bloco1:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
                
                # === BARRA CENTRAL BICOLOR: Alinhamento das anotações internas por offset ===
                # Texto da metade esquerda (Amarela) recua -0.2
                pos_x_anotacao_esquerda = posicao_x_base - 0.2
                anotacoes.append(dict(
                    x=pos_x_anotacao_esquerda, y=inicio_interno_y, text=f"{val_acum_formatado}<br>Qtde {vol_texto}",
                    showarrow=False, yanchor="bottom", yshift=8, xref="x", yref="y",
                    font=dict(size=tamanho_fonte_numeros, color="black", family="Arial", weight="bold")
                ))

                # === ALINHAMENTO DO NOME NO PÉ EXTERNO (EIXO X) ===
                # Como a barra central é dupla, o nome dela fica perfeitamente centralizado no meio exato da junção (posicao_x_base)
                anotacoes.append(dict(
                    x=posicao_x_base, y=0, text=f"<b>{nome_original}</b>",
                    showarrow=False, yanchor="top", yshift=-10, xref="x", yref="y",
                    font=dict(size=tamanho_fonte_eixos, color="#2c3e50", family="Arial")
                ))

                x_t1.append(nome_id); y_t1.append(0); m_t1.append("total")
                x_t2.append(nome_id); y_t2.append(acumulado_bloco1); m_t2.append("absolute")
                
                corrente_y = acumulado_bloco1
                continue

            elif idx == len(df) - 1:
                inicio_interno_y = 0.0
                cor_texto = "white"
                pos_x_anotacao = posicao_x_base + 0.2
                
                x_t2.append(nome_id); y_t2.append(0); m_t2.append("total")

            else:
                if val_num >= 0:
                    inicio_interno_y = corrente_y
                else:
                    inicio_interno_y = corrente_y + val_num
                
                if idx < idx_total_meio:
                    cor_texto = "black"
                    pos_x_anotacao = posicao_x_base - 0.2
                    x_t1.append(nome_id); y_t1.append(val_num); m_t1.append("relative")
                else:
                    cor_texto = "white"
                    pos_x_anotacao = posicao_x_base + 0.2
                    x_t2.append(nome_id); y_t2.append(val_num); m_t2.append("relative")
                
                corrente_y += val_num

            # Adiciona o bloco de texto interno da barra (Valor + Qtde)
            anotacoes.append(dict(
                x=pos_x_anotacao, y=inicio_interno_y, text=texto_interno,
                showarrow=False, yanchor="bottom", yshift=8, xref="x", yref="y",
                font=dict(size=tamanho_fonte_numeros, color=cor_texto, family="Arial", weight="bold")
            ))

            # === ALINHAMENTO DOS NOMES DAS DEMAIS BARRAS NO PÉ EXTERNO ===
            # Vincula a anotação do nome exatamente embaixo do centro geométrico de cada barra utilizando seu offset correspondente
            if nome_lower in lista_itens_fixos:
                pos_x_nome_pe = posicao_x_base
            elif idx < idx_total_meio:
                pos_x_nome_pe = posicao_x_base - 0.2 # Alinha com as barras do Bloco 1
            else:
                pos_x_nome_pe = posicao_x_base + 0.2 # Alinha com as barras do Bloco 2 e Final

            anotacoes.append(dict(
                x=pos_x_nome_pe, y=0, text=f"<b>{nome_original}</b>",
                showarrow=False, yanchor="top", yshift=-10, xref="x", yref="y",
                font=dict(size=tamanho_fonte_eixos, color="#2c3e50", family="Arial")
            ))

        # --- CONSTRUÇÃO DO GRÁFICO ---
        fig = go.Figure()

        # 1. Barras Históricas Fixas (Cinza)
        if x_fx:
            fig.add_trace(go.Waterfall(
                orientation="v", measure=m_fx, x=x_fx, y=y_fx,
                textposition="none", width=0.4, offset=-0.2,
                increasing={"marker": {"color": cor_fixas}},
                decreasing={"marker": {"color": cor_fixas}},
                totals={"marker": {"color": cor_fixas}},
                connector=dict(visible=False), showlegend=False
            ))

        # 2. Bloco 1 (Escada Amarela)
        if x_t1:
            fig.add_trace(go.Waterfall(
                orientation="v", measure=m_t1, x=x_t1, y=y_t1,
                textposition="none", width=0.4, offset=-0.4,
                increasing={"marker": {"color": cor_b1_pos}},
                decreasing={"marker": {"color": cor_b1_neg}},
                totals={"marker": {"color": cor_b1_pos}},
                connector=cfg_connector, showlegend=False
            ))

        # 3. Bloco 2 (Escada Laranja + Barra Final)
        if x_t2:
            fig.add_trace(go.Waterfall(
                orientation="v", measure=m_t2, x=x_t2, y=y_t2,
                textposition="none", width=0.4, offset=0.0,
                increasing={"marker": {"color": cor_b2_pos}},
                decreasing={"marker": {"color": cor_b2_neg}},
                totals={"marker": {"color": cor_final}},
                connector=cfg_connector, showlegend=False
            ))

        fig.update_layout(
            title="Gráfico Waterfall Executivo V28",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Valores Financeiros (R$)",
            font=dict(size=tamanho_fonte_eixos),
            barmode="overlay",
            annotations=anotacoes,
            # Desativa as legendas originais do eixo X para não duplicar, mantendo a escala numérica oculta
            xaxis=dict(
                tickvals=[i for i in range(len(df))],
                ticktext=["" for _ in range(len(df))],
                categoryorder="array",
                categoryarray=ordem_eixo_x_id
            )
        )

        fig.show()
        janela.destroy()

    except Exception as e:
        messagebox.showerror("Erro de Processamento", f"Falha ao gerar o gráfico.\nDetalhes: {e}")


# === PALCO INTERFACE GRÁFICA V28 ===
janela = tk.Tk()
janela.title("Gerador de Waterfall - V28")
janela.geometry("920x940")
janela.minsize(850, 800)

opcoes_cores = list(DIC_CORES.keys())
tamanhos_fonte = ["10", "12", "14", "16", "18", "20", "22", "24", "28"]

frame_top = tk.Frame(janela)
frame_top.pack(pady=10, fill="x")

btn_generar = tk.Button(
    frame_top, text="Gerar Gráfico Waterfall - V28 📊", command=gerar_grafico,
    bg="#2ecc71", fg="white", font=("Arial", 13, "bold"), cursor="hand2"
)
btn_generar.pack(ipady=6, padx=40, fill="x")

var_ativar_linhas = tk.BooleanVar(value=True)
chk_linhas = tk.Checkbutton(
    frame_top, text="Ativar Linhas de Conexão Vermelhas Tracejadas", 
    variable=var_ativar_linhas, font=("Arial", 11, "bold"), fg="#e74c3c"
)
chk_linhas.pack(pady=5)

frame_mapeamento = tk.LabelFrame(janela, text=" 1. Mapeamento Estrutural do Excel ", font=("Arial", 11, "bold"))
frame_mapeamento.pack(padx=15, pady=5, fill="x")
frame_mapeamento.columnconfigure([1, 3], weight=1)

tk.Label(frame_mapeamento, text="Coluna Nomes:").grid(row=0, column=0, padx=5, pady=4, sticky="w")
ent_col_nome = tk.Entry(frame_mapeamento, font=("Arial", 11)); ent_col_nome.grid(row=0, column=1, padx=5, pady=4, sticky="ew"); ent_col_nome.insert(0, "Analise")

tk.Label(frame_mapeamento, text="Coluna Valores:").grid(row=0, column=2, padx=5, pady=4, sticky="w")
ent_col_valor = tk.Entry(frame_mapeamento, font=("Arial", 11)); ent_col_valor.grid(row=0, column=3, padx=5, pady=4, sticky="ew"); ent_col_valor.insert(0, "Valor")

tk.Label(frame_mapeamento, text="Termo p/ Totais:").grid(row=1, column=0, padx=5, pady=4, sticky="w")
ent_termo_total = tk.Entry(frame_mapeamento, font=("Arial", 11)); ent_termo_total.grid(row=1, column=1, padx=5, pady=4, sticky="ew"); ent_termo_total.insert(0, "Total")

tk.Label(frame_mapeamento, text="Itens no Início/Fora (Separar por ; ):", fg="#2980b9", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=4, sticky="w")
ent_itens_fixos = tk.Entry(frame_mapeamento, font=("Arial", 11), fg="#2980b9"); ent_itens_fixos.grid(row=1, column=3, padx=5, pady=4, sticky="ew"); ent_itens_fixos.insert(0, "Mês 1;Mês 2")

tk.Label(frame_mapeamento, text="Coluna Volumes (Qtde):", fg="#16a085", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5, pady=4, sticky="w")
ent_col_volume = tk.Entry(frame_mapeamento, font=("Arial", 11), fg="#16a085"); ent_col_volume.grid(row=2, column=1, padx=5, pady=4, sticky="ew"); ent_col_volume.insert(0, "Qtde")

frame_cores = tk.LabelFrame(janela, text=" 2. Paleta de Cores ", font=("Arial", 11, "bold"))
frame_cores.pack(padx=15, pady=5, fill="x")
frame_cores.columnconfigure([1, 2], weight=1)

tk.Label(frame_cores, text="B1 - Positivos (+):").grid(row=0, column=0, padx=6, pady=3, sticky="w")
cb_b1_pos = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_b1_pos.grid(row=0, column=1, padx=6, pady=3, sticky="ew"); cb_b1_pos.set("Amarelo/Ouro")
ent_b1_pos_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_b1_pos_manual.grid(row=0, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="B1 - Negativos (-):").grid(row=1, column=0, padx=6, pady=3, sticky="w")
cb_b1_neg = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_b1_neg.grid(row=1, column=1, padx=6, pady=3, sticky="ew"); cb_b1_neg.set("Amarelo/Ouro")
ent_b1_neg_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_b1_neg_manual.grid(row=1, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="B2 - Positivos (+):").grid(row=2, column=0, padx=6, pady=3, sticky="w")
cb_b2_pos = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_b2_pos.grid(row=2, column=1, padx=6, pady=3, sticky="ew"); cb_b2_pos.set("Laranja")
ent_b2_pos_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_b2_pos_manual.grid(row=2, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="B2 - Negativos (-):").grid(row=3, column=0, padx=6, pady=3, sticky="w")
cb_b2_neg = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_b2_neg.grid(row=3, column=1, padx=6, pady=3, sticky="ew"); cb_b2_neg.set("Laranja")
ent_b2_neg_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_b2_neg_manual.grid(row=3, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="Cor das Colunas do Início:", fg="#2980b9").grid(row=4, column=0, padx=6, pady=3, sticky="w")
cb_fixas = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_fixas.grid(row=4, column=1, padx=6, pady=3, sticky="ew"); cb_fixas.set("Cinza")
ent_fixas_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_fixas_manual.grid(row=4, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="Barra Final Absoluta:").grid(row=5, column=0, padx=6, pady=3, sticky="w")
cb_tot = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10)); cb_tot.grid(row=5, column=1, padx=6, pady=3, sticky="ew"); cb_tot.set("Azul Escuro")
ent_tot_manual = tk.Entry(frame_cores, font=("Arial", 11)); ent_tot_manual.grid(row=5, column=2, padx=6, pady=3, sticky="ew")

frame_fontes = tk.LabelFrame(janela, text=" 3. Dimensionamento de Textos ", font=("Arial", 11, "bold"))
frame_fontes.pack(padx=15, pady=5, fill="x")
tk.Label(frame_fontes, text="Fonte Legendas/Eixos:").grid(row=0, column=0, padx=8, pady=4)
cb_fonte_eixos = ttk.Combobox(frame_fontes, values=tamanhos_fonte, state="readonly", width=8); cb_fonte_eixos.grid(row=0, column=1, padx=8, pady=4); cb_fonte_eixos.set("12")
tk.Label(frame_fontes, text="Fonte Valores (Barras):").grid(row=0, column=2, padx=8, pady=4)
cb_fonte_numeros = ttk.Combobox(frame_fontes, values=tamanhos_fonte, state="readonly", width=8); cb_fonte_numeros.grid(row=0, column=3, padx=8, pady=4); cb_fonte_numeros.set("12")

frame_texto = tk.Frame(janela)
frame_texto.pack(padx=15, pady=10, fill="both", expand=True)
tk.Label(frame_texto, text="Cole seus dados do Excel abaixo:", font=("Arial", 10, "italic")).pack(anchor="w")
txt_area = tk.Text(frame_texto, wrap="none", font=("Courier New", 11)); txt_area.pack(side="left", fill="both", expand=True)
scroll_y = tk.Scrollbar(frame_texto, command=txt_area.yview); scroll_y.pack(side="right", fill="y"); txt_area.config(yscrollcommand=scroll_y.set)

janela.protocol("WM_DELETE_WINDOW", lambda: (janela.destroy(), exit()))
janela.mainloop()
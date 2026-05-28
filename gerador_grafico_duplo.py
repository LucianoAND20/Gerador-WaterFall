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

    col_nome = ent_col_nome.get().strip()
    col_valor = ent_col_valor.get().strip()
    termo_total = ent_termo_total.get().strip().lower()

    if not col_nome or not col_valor or not termo_total:
        messagebox.showerror(
            "Erro de Configuração",
            "Os campos de mapeamento não podem ficar vazios.",
        )
        return

    # Captura das cores configuradas na tela
    cor_b1_pos = obter_cor(cb_b1_pos, ent_b1_pos_manual, "#f1c40f")
    cor_b1_neg = obter_cor(cb_b1_neg, ent_b1_neg_manual, "#f39c12")
    cor_b2_pos = obter_cor(cb_b2_pos, ent_b2_pos_manual, "#e67e22")
    cor_b2_neg = obter_cor(cb_b2_neg, ent_b2_neg_manual, "#d35400")
    cor_final = obter_cor(cb_tot, ent_tot_manual, "#34495e")

    tamanho_fonte_eixos = int(cb_fonte_eixos.get())
    tamanho_fonte_numeros = int(cb_fonte_numeros.get())

    try:
        df = pd.read_csv(io.StringIO(conteudo_colado), sep="\t")
        df.columns = df.columns.str.strip()

        if col_nome not in df.columns or col_valor not in df.columns:
            messagebox.showerror(
                "Erro de Mapeamento",
                f"Não encontrei as colunas '{col_nome}' ou '{col_valor}'.",
            )
            return

        df["Valor_Num"] = df[col_valor].apply(limpar_e_converter_valor)

        indices_totais = df[
            df[col_nome].astype(str).str.strip().str.lower() == termo_total
        ].index.tolist()

        if not indices_totais:
            messagebox.showerror(
                "Erro de Estrutura",
                f"Não encontrei nenhuma linha com o termo '{ent_termo_total.get().strip()}' para dividir os blocos.",
            )
            return

        idx_corte = indices_totais[0]

        # Calcula o topo acumulado para sustentar a flutuação do Bloco 2
        acumulado = 0.0
        for idx, linha in df.iterrows():
            if idx < idx_corte:
                acumulado += linha["Valor_Num"]

        df_b1 = df.loc[:idx_corte].copy()
        df_b2 = df.loc[idx_corte:].copy()

        # --- PROCESSAMENTO DO BLOCO 1 ---
        etapas_b1 = df_b1[col_nome].tolist()
        valores_b1 = df_b1["Valor_Num"].tolist()
        tipos_b1 = ["relative"] * len(df_b1)
        tipos_b1[-1] = "total"
        valores_b1[-1] = 0

        # --- PROCESSAMENTO DO BLOCO 2 ---
        etapas_b2 = df_b2[col_nome].tolist()
        valores_b2 = df_b2["Valor_Num"].tolist()
        tipos_b2 = ["relative"] * len(df_b2)
        
        # A primeira barra do Bloco 2 é o início da nossa transição flutuante.
        # Para que ela herde a cor do Bloco 2 perfeitamente sem pintar o gráfico todo,
        # mudamos o tipo dela para 'relative' e aplicamos o valor acumulado diretamente.
        tipos_b2[0] = "relative"
        valores_b2[0] = acumulado
        
        # A última barra fecha o gráfico como o Total Absoluto
        tipos_b2[-1] = "total"
        valores_b2[-1] = 0

        # --- MONTAGEM DO GRÁFICO (ABORDAGEM 100% NATIVA) ---
        fig = go.Figure()

        # Trace 1: Lado Esquerdo da Transição (Bloco 1)
        fig.add_trace(
            go.Waterfall(
                orientation="v",
                measure=tipos_b1,
                x=etapas_b1,
                y=valores_b1,
                text=df_b1[col_valor].tolist(),
                textposition="outside",
                texttemplate="%{text}",
                textfont=dict(size=tamanho_fonte_numeros),
                width=0.4,
                offset=-0.4,
                # Define as cores de forma estrita para o Bloco 1
                increasing={"marker": {"color": cor_b1_pos}},
                decreasing={"marker": {"color": cor_b1_neg}},
                totals={"marker": {"color": cor_b1_pos}},  # Metade esquerda da barra central
                showlegend=False,
            )
        )

        # Trace 2: Lado Direito da Transição (Bloco 2 - Flutuando)
        fig.add_trace(
            go.Waterfall(
                orientation="v",
                measure=tipos_b2,
                x=etapas_b2,
                y=valores_b2,
                text=df_b2[col_valor].tolist(),
                textposition="outside",
                texttemplate="%{text}",
                textfont=dict(size=tamanho_fonte_numeros),
                width=0.4,
                offset=0.0,
                # Define as cores de forma estrita para o Bloco 2
                increasing={"marker": {"color": cor_b2_pos}},
                decreasing={"marker": {"color": cor_b2_neg}},
                totals={"marker": {"color": cor_final}},  # Barra final absoluta respeitada!
                showlegend=False,
            )
        )

        fig.update_layout(
            title="Gráfico Waterfall Customizado - Avançado (V15)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title=f"{col_valor} (R$)",
            font=dict(size=tamanho_fonte_eixos),
            barmode="overlay",
        )

        fig.show()
        janela.destroy()

    except Exception as e:
        messagebox.showerror(
            "Erro de Processamento",
            f"Ocorreu um erro ao processar os dados.\nDetalhes: {e}",
        )


# === INTERFACE GRÁFICA ===
janela = tk.Tk()
janela.title("Gerador de Waterfall Profissional - V15")
janela.geometry("880x840")
janela.minsize(800, 700)

opcoes_cores = list(DIC_CORES.keys())
tamanhos_fonte = ["10", "12", "14", "16", "18", "20", "22", "24", "28"]

# Botão de Ação no Topo
frame_botao = tk.Frame(janela)
frame_botao.pack(pady=10, fill="x")
btn_gerar = tk.Button(
    frame_botao,
    text="Gerar Gráfico Waterfall Duplo Bicolor 📊",
    command=gerar_grafico,
    bg="#2ecc71",
    fg="white",
    font=("Arial", 13, "bold"),
    cursor="hand2",
)
btn_gerar.pack(ipady=6, padx=40, fill="x")

# Mapeamento do Excel
frame_mapeamento = tk.LabelFrame(
    janela, text=" 1. Definições do Excel ", font=("Arial", 11, "bold")
)
frame_mapeamento.pack(padx=15, pady=5, fill="x")

tk.Label(frame_mapeamento, text="Coluna de Nomes:", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=4, sticky="w")
ent_col_nome = tk.Entry(frame_mapeamento, font=("Arial", 11))
ent_col_nome.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
ent_col_nome.insert(0, "Analise")

tk.Label(frame_mapeamento, text="Coluna de Valores:", font=("Arial", 11)).grid(row=0, column=2, padx=5, pady=4, sticky="w")
ent_col_valor = tk.Entry(frame_mapeamento, font=("Arial", 11))
ent_col_valor.grid(row=0, column=3, padx=5, pady=4, sticky="ew")
ent_col_valor.insert(0, "Valor")

tk.Label(frame_mapeamento, text="Termo para Totais:", font=("Arial", 11)).grid(row=1, column=0, padx=5, pady=4, sticky="w")
ent_termo_total = tk.Entry(frame_mapeamento, font=("Arial", 11))
ent_termo_total.grid(row=1, column=1, padx=5, pady=4, sticky="ew")
ent_termo_total.insert(0, "Total")

frame_mapeamento.columnconfigure([1, 3], weight=1)

# Customização Avançada de Cores
frame_cores = tk.LabelFrame(
    janela, text=" 2. Paleta de Cores dos Blocos (Opcional: Hexadecimal à direita) ", font=("Arial", 11, "bold")
)
frame_cores.pack(padx=15, pady=5, fill="x")
frame_cores.columnconfigure([1, 2], weight=1)

# Bloco 1
tk.Label(frame_cores, text="Bloco 1 - Positivos (+):", font=("Arial", 11)).grid(row=0, column=0, padx=6, pady=3, sticky="w")
cb_b1_pos = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10))
cb_b1_pos.grid(row=0, column=1, padx=6, pady=3, sticky="ew")
cb_b1_pos.set("Amarelo/Ouro")
ent_b1_pos_manual = tk.Entry(frame_cores, font=("Arial", 11))
ent_b1_pos_manual.grid(row=0, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="Bloco 1 - Negativos (-):", font=("Arial", 11)).grid(row=1, column=0, padx=6, pady=3, sticky="w")
cb_b1_neg = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10))
cb_b1_neg.grid(row=1, column=1, padx=6, pady=3, sticky="ew")
cb_b1_neg.set("Amarelo/Ouro")
ent_b1_neg_manual = tk.Entry(frame_cores, font=("Arial", 11))
ent_b1_neg_manual.grid(row=1, column=2, padx=6, pady=3, sticky="ew")

# Bloco 2
tk.Label(frame_cores, text="Bloco 2 - Positivos (+):", font=("Arial", 11)).grid(row=2, column=0, padx=6, pady=3, sticky="w")
cb_b2_pos = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10))
cb_b2_pos.grid(row=2, column=1, padx=6, pady=3, sticky="ew")
cb_b2_pos.set("Laranja")
ent_b2_pos_manual = tk.Entry(frame_cores, font=("Arial", 11))
ent_b2_pos_manual.grid(row=2, column=2, padx=6, pady=3, sticky="ew")

tk.Label(frame_cores, text="Bloco 2 - Negativos (-):", font=("Arial", 11)).grid(row=3, column=0, padx=6, pady=3, sticky="w")
cb_b2_neg = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10))
cb_b2_neg.grid(row=3, column=1, padx=6, pady=3, sticky="ew")
cb_b2_neg.set("Laranja")
ent_b2_neg_manual = tk.Entry(frame_cores, font=("Arial", 11))
ent_b2_neg_manual.grid(row=3, column=2, padx=6, pady=3, sticky="ew")

# Total Final
tk.Label(frame_cores, text="Barra Final Absoluta:", font=("Arial", 11)).grid(row=4, column=0, padx=6, pady=3, sticky="w")
cb_tot = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly", font=("Arial", 10))
cb_tot.grid(row=4, column=1, padx=6, pady=3, sticky="ew")
cb_tot.set("Azul Escuro")
ent_tot_manual = tk.Entry(frame_cores, font=("Arial", 11))
ent_tot_manual.grid(row=4, column=2, padx=6, pady=3, sticky="ew")

# Fontes e Textos
frame_fontes = tk.LabelFrame(
    janela, text=" 3. Dimensionamento de Textos ", font=("Arial", 11, "bold")
)
frame_fontes.pack(padx=15, pady=5, fill="x")

tk.Label(frame_fontes, text="Tamanho dos Eixos/Legendas:", font=("Arial", 11)).grid(row=0, column=0, padx=8, pady=4)
cb_fonte_eixos = ttk.Combobox(frame_fontes, values=tamanhos_fonte, state="readonly", width=8)
cb_fonte_eixos.grid(row=0, column=1, padx=8, pady=4)
cb_fonte_eixos.set("14")

tk.Label(frame_fontes, text="Tamanho dos Valores (Barras):", font=("Arial", 11)).grid(row=0, column=2, padx=8, pady=4)
cb_fonte_numeros = ttk.Combobox(frame_fontes, values=tamanhos_fonte, state="readonly", width=8)
cb_fonte_numeros.grid(row=0, column=3, padx=8, pady=4)
cb_fonte_numeros.set("14")

# Área de Texto / Ctrl+V
frame_texto = tk.Frame(janela)
frame_texto.pack(padx=15, pady=10, fill="both", expand=True)

tk.Label(frame_texto, text="Cole seus dados do Excel abaixo:", font=("Arial", 10, "italic")).pack(anchor="w")
txt_area = tk.Text(frame_texto, wrap="none", font=("Courier New", 11))
txt_area.pack(side="left", fill="both", expand=True)

scroll_y = tk.Scrollbar(frame_texto, command=txt_area.yview)
scroll_y.pack(side="right", fill="y")
txt_area.config(yscrollcommand=scroll_y.set)

janela.protocol("WM_DELETE_WINDOW", lambda: (janela.destroy(), exit()))
janela.mainloop()
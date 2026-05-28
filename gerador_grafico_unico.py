import io
import re
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import plotly.graph_objects as go

# Dicionário de cores amigáveis para o usuário
DIC_CORES = {
    "Verde Padrão": "#2ecc71",
    "Vermelho Padrão": "#e74c3c",
    "Azul Escuro": "#34495e",
    "Azul Claro": "#3498db",
    "Cinza": "#95a5a6",
    "Laranja": "#e67e22",
    "Roxo": "#9b59b6",
    "Amarelo/Ouro": "#f1c40f",
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

    # Mapeamento dos campos da tela
    col_nome = ent_col_nome.get().strip()
    col_valor = ent_col_valor.get().strip()
    termo_total = ent_termo_total.get().strip().lower()

    if not col_nome or not col_valor or not termo_total:
        messagebox.showerror(
            "Erro de Configuração",
            "Os campos de nome das colunas e termo do total não podem ficar vazios.",
        )
        return

    cor_positivo = obter_cor(cb_pos, ent_pos_manual, "#2ecc71")
    cor_negativo = obter_cor(cb_neg, ent_neg_manual, "#e74c3c")
    cor_total = obter_cor(cb_tot, ent_tot_manual, "#34495e")

    # Captura os tamanhos de fontes definidos na tela
    tamanho_fonte_eixos = int(cb_fonte_eixos.get())
    tamanho_fonte_numeros = int(cb_fonte_numeros.get())

    try:
        df = pd.read_csv(io.StringIO(conteudo_colado), sep="\t")
        df.columns = df.columns.str.strip()

        if col_nome not in df.columns or col_valor not in df.columns:
            messagebox.showerror(
                "Erro de Mapeamento",
                f"Não encontrei as colunas '{col_nome}' ou '{col_valor}' nos dados colados.\n\n"
                f"Colunas detectadas no seu Ctrl+V: {list(df.columns)}",
            )
            return

        df["Valor_Num"] = df[col_valor].apply(limpar_e_converter_valor)

        df_itens = df[
            df[col_nome].astype(str).str.strip().str.lower() != termo_total
        ]
        df_total = df[
            df[col_nome].astype(str).str.strip().str.lower() == termo_total
        ]

        etapas = list(df_itens[col_nome])
        valores = list(df_itens["Valor_Num"])
        tipos = ["relative"] * len(df_itens)

        if not df_total.empty:
            etapas.append(ent_termo_total.get().strip())
            valores.append(0)
            tipos.append("total")

        fig = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=tipos,
                x=etapas,
                y=valores,
                text=valores,
                textposition="outside",
                texttemplate="%{y:,.2f}",
                # Ajustando o tamanho da fonte especificamente para os números das barras
                textfont=dict(size=tamanho_fonte_numeros),
                increasing={"marker": {"color": cor_positivo}},
                decreasing={"marker": {"color": cor_negativo}},
                totals={"marker": {"color": cor_total}},
            )
        )

        fig.update_layout(
            title="Gráfico de Cascata Automático",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title=f"{col_valor} (R$)",
            showlegend=False,
            # Ajustando o tamanho da fonte geral (eixos e títulos)
            font=dict(size=tamanho_fonte_eixos),
        )

        fig.show()
        janela.destroy()

    except Exception as e:
        messagebox.showerror(
            "Erro de Processamento",
            f"Ocorreu um erro ao processar os dados.\nDetalhes: {e}",
        )


# === CONFIGURAÇÃO DA INTERFACE GRÁFICA ===
janela = tk.Tk()
janela.title("Gerador de Waterfall Automático - V7 Final")
janela.geometry("820x780")
janela.minsize(700, 600)

estilo = ttk.Style()
estilo.configure("TCombobox", font=("Arial", 12))
janela.option_add("*TCombobox*Listbox.font", ("Arial", 12))

# 1. Instruções
frame_instrucoes = tk.Frame(janela)
frame_instrucoes.pack(pady=5, padx=15, fill="x")

label_instrucao = tk.Label(
    frame_instrucoes,
    text="1. Ajuste abaixo as configurações de mapeamento e aparência.\n"
    "2. Copie a tabela do Excel, cole no campo inferior e clique em Gerar.",
    justify="left",
    font=("Arial", 12, "bold"),
    fg="#2c3e50",
)
label_instrucao.pack(anchor="w")

# 2. Botão Gerar no Topo (Fixo)
frame_botao = tk.Frame(janela)
frame_botao.pack(pady=10, fill="x")

btn_gerar = tk.Button(
    frame_botao,
    text="Gerar Gráfico Waterfall 📊",
    command=gerar_grafico,
    bg="#2ecc71",
    fg="white",
    font=("Arial", 14, "bold"),
    cursor="hand2",
)
btn_gerar.pack(ipady=8, padx=60, fill="x")

# 3. Mapeamento de Colunas
frame_mapeamento = tk.LabelFrame(
    janela, text=" Mapeamento das Colunas do Excel ", font=("Arial", 12, "bold")
)
frame_mapeamento.pack(padx=15, pady=5, fill="x")

tk.Label(frame_mapeamento, text="Coluna de Nomes/Texto:", font=("Arial", 12)).grid(row=0, column=0, padx=8, pady=6, sticky="w")
ent_col_nome = tk.Entry(frame_mapeamento, font=("Arial", 12))
ent_col_nome.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
ent_col_nome.insert(0, "Analise")

tk.Label(frame_mapeamento, text="Coluna de Valores:", font=("Arial", 12)).grid(row=0, column=2, padx=8, pady=6, sticky="w")
ent_col_valor = tk.Entry(frame_mapeamento, font=("Arial", 12))
ent_col_valor.grid(row=0, column=3, padx=8, pady=6, sticky="ew")
ent_col_valor.insert(0, "Valor")

tk.Label(frame_mapeamento, text="Palavra da linha final (Total):", font=("Arial", 12)).grid(row=1, column=0, padx=8, pady=6, sticky="w")
ent_termo_total = tk.Entry(frame_mapeamento, font=("Arial", 12))
ent_termo_total.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
ent_termo_total.insert(0, "Total")

frame_mapeamento.columnconfigure(1, weight=1)
frame_mapeamento.columnconfigure(3, weight=1)

# 4. Painel de Configurações de Aparência
frame_cores = tk.LabelFrame(
    janela, text=" Configurações de Aparência ", font=("Arial", 12, "bold")
)
frame_cores.pack(padx=15, pady=5, fill="x")

frame_cores.columnconfigure(1, weight=1)
frame_cores.columnconfigure(2, weight=1)

opcoes_cores = list(DIC_CORES.keys())
tamanhos_fonte = ["10", "12", "14", "16", "18", "20", "22", "24", "28"]

# --- Linhas de Cores ---
tk.Label(frame_cores, text="Valores Positivos (+):", font=("Arial", 12)).grid(row=0, column=0, padx=8, pady=4, sticky="w")
cb_pos = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly")
cb_pos.grid(row=0, column=1, padx=8, pady=4, sticky="ew")
cb_pos.set("Verde Padrão")
ent_pos_manual = tk.Entry(frame_cores, font=("Arial", 12))
ent_pos_manual.grid(row=0, column=2, padx=8, pady=4, sticky="ew")

# --- Linha Negativos ---
tk.Label(frame_cores, text="Valores Negativos (-):", font=("Arial", 12)).grid(row=1, column=0, padx=8, pady=4, sticky="w")
cb_neg = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly")
cb_neg.grid(row=1, column=1, padx=8, pady=4, sticky="ew")
cb_neg.set("Vermelho Padrão")
ent_neg_manual = tk.Entry(frame_cores, font=("Arial", 12))
ent_neg_manual.grid(row=1, column=2, padx=8, pady=4, sticky="ew")

# --- Linha Total ---
tk.Label(frame_cores, text="Barra de Total / Saldo:", font=("Arial", 12)).grid(row=2, column=0, padx=8, pady=4, sticky="w")
cb_tot = ttk.Combobox(frame_cores, values=opcoes_cores, state="readonly")
cb_tot.grid(row=2, column=1, padx=8, pady=4, sticky="ew")
cb_tot.set("Azul Escuro")
ent_tot_manual = tk.Entry(frame_cores, font=("Arial", 12))
ent_tot_manual.grid(row=2, column=2, padx=8, pady=4, sticky="ew")

# --- CONTROLES DE FONTE SEPARADOS ---
tk.Label(frame_cores, text="Tamanho da Fonte dos Eixos:", font=("Arial", 12)).grid(row=3, column=0, padx=8, pady=4, sticky="w")
cb_fonte_eixos = ttk.Combobox(frame_cores, values=tamanhos_fonte, state="readonly")
cb_fonte_eixos.grid(row=3, column=1, padx=8, pady=4, sticky="w")
cb_fonte_eixos.set("14")

tk.Label(frame_cores, text="Tamanho dos Números (Barras):", font=("Arial", 12)).grid(row=4, column=0, padx=8, pady=4, sticky="w")
cb_fonte_numeros = ttk.Combobox(frame_cores, values=tamanhos_fonte, state="readonly")
cb_fonte_numeros.grid(row=4, column=1, padx=8, pady=4, sticky="w")
cb_fonte_numeros.set("14")

# 5. Área de Texto para Colagem
frame_texto = tk.Frame(janela)
frame_texto.pack(padx=15, pady=10, fill="both", expand=True)

label_colar = tk.Label(frame_texto, text="Cole seus dados aqui:", font=("Arial", 11, "italic"))
label_colar.pack(anchor="w")

scroll_y = tk.Scrollbar(frame_texto)
scroll_y.pack(side="right", fill="y")

txt_area = tk.Text(frame_texto, wrap="none", font=("Courier New", 12), yscrollcommand=scroll_y.set)
txt_area.pack(side="left", fill="both", expand=True)
scroll_y.config(command=txt_area.yview)

janela.protocol("WM_DELETE_WINDOW", lambda: (janela.destroy(), exit()))

janela.mainloop()
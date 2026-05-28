import io
import re
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import plotly.graph_objects as go


def limpar_e_converter_valor(valor_str):
    """Função para limpar strings financeiras do Excel (ex: 'R$ 1.250,50')

    e converter em float puro (1250.50) para o gráfico.
    """
    if pd.isna(valor_str):
        return 0.0
    val_limpo = str(valor_str).strip()
    # Remove 'R$', '$' e qualquer espaço em branco gerado pela formatação
    val_limpo = re.sub(r"[R\$\s]", "", val_limpo)
    if not val_limpo:
        return 0.0

    # Tratamento para o padrão brasileiro: '1.250,00' -> '1250.00'
    if "," in val_limpo and "." in val_limpo:
        val_limpo = val_limpo.replace(".", "").replace(",", ".")
    elif "," in val_limpo:
        val_limpo = val_limpo.replace(",", ".")

    try:
        return float(val_limpo)
    except ValueError:
        return 0.0


def gerar_grafico():
    conteudo_colado = txt_area.get("1.0", tk.END).strip()

    if not conteudo_colado:
        messagebox.showwarning(
            "Aviso", "Por favor, cole a tabela antes de gerar o gráfico!"
        )
        return

    try:
        # Lê o conteúdo separado por TAB (padrão de cópia do Excel)
        df = pd.read_csv(io.StringIO(conteudo_colado), sep="\t")
        df.columns = df.columns.str.strip()

        if "Analise" not in df.columns or "Valor" not in df.columns:
            messagebox.showerror(
                "Erro de Colunas",
                'A tabela precisa conter os cabeçalhos exatos: "Analise" e "Valor".\n'
                f"Detectado na colagem: {list(df.columns)}",
            )
            return

        # Aplica a limpeza de dados e conversão numérica na coluna Valor
        df["Valor_Num"] = df["Valor"].apply(limpar_e_converter_valor)

        # Separa os itens comuns do Total final
        df_itens = df[df["Analise"].astype(str).str.strip().str.lower() != "total"]
        df_total = df[df["Analise"].astype(str).str.strip().str.lower() == "total"]

        etapas = list(df_itens["Analise"])
        valores = list(df_itens["Valor_Num"])
        tipos = ["relative"] * len(df_itens)

        if not df_total.empty:
            etapas.append("Total")
            valores.append(0)  # O Plotly calcula o fechamento dinamicamente
            tipos.append("total")

        # Configuração visual do gráfico Waterfall
        fig = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=tipos,
                x=etapas,
                y=valores,
                text=valores,
                textposition="outside",
                texttemplate="%{y:,.2f}",  # Formata o rótulo do gráfico com 2 casas decimais
                increasing={"marker": {"color": "#2ecc71"}},  # Verde
                decreasing={"marker": {"color": "#e74c3c"}},  # Vermelho
                totals={"marker": {"color": "#34495e"}},  # Azul escuro
            )
        )

        fig.update_layout(
            title="Gráfico de Cascata Automático",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Valores (R$)",
            showlegend=False,
        )

        fig.show()

    except Exception as e:
        messagebox.showerror(
            "Erro de Processamento",
            f"Ocorreu um erro ao processar os dados colados.\nDetalhes: {e}",
        )


# === CONFIGURAÇÃO DA INTERFACE GRÁFICA (CORRIGIDA) ===
janela = tk.Tk()
janela.title("Gerador de Waterfall - Inteligente")
janela.geometry("650x500")  # Janela inicial maior para melhor visualização
janela.minsize(450, 350)  # Impede que o usuário encolha a tela a ponto de sumir o botão

# Container superior para instruções
frame_instrucoes = tk.Frame(janela)
frame_instrucoes.pack(pady=10, padx=15, fill="x")

label_instrucao = tk.Label(
    frame_instrucoes,
    text="1. Selecione e copie a tabela no Excel (inclua os cabeçalhos 'Analise' e 'Valor').\n"
    "2. Cole (Ctrl+V) no campo de texto abaixo e clique no botão para gerar.",
    justify="left",
    font=("Arial", 10),
)
label_instrucao.pack(anchor="w")

# Container central para a caixa de texto e barra de rolagem
frame_texto = tk.Frame(janela)
frame_texto.pack(padx=15, pady=5, fill="both", expand=True)

scroll_y = tk.Scrollbar(frame_texto)
scroll_y.pack(side="right", fill="y")

txt_area = tk.Text(
    frame_texto, wrap="none", font=("Courier New", 10), yscrollcommand=scroll_y.set
)
txt_area.pack(side="left", fill="both", expand=True)
scroll_y.config(command=txt_area.yview)

# Container inferior fixo para o botão (garante que ele nunca suma)
frame_botao = tk.Frame(janela)
frame_botao.pack(pady=15, fill="x")

btn_gerar = tk.Button(
    frame_botao,
    text="Gerar Gráfico Waterfall 📊",
    command=gerar_grafico,
    bg="#2ecc71",
    fg="white",
    font=("Arial", 11, "bold"),
    cursor="hand2",
)
btn_gerar.pack(ipady=5, padx=50, fill="x")

janela.mainloop()
import os
import subprocess
import tkinter as tk
from tkinter import filedialog


def encontrar_metaeditor():
    caminhos_comuns = [
        r"C:\Program Files\MetaTrader 5\metaeditor64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\metaeditor64.exe",
    ]

    for caminho in caminhos_comuns:
        if os.path.exists(caminho):
            return caminho

    return None


def pedir_caminho_arquivo():
    while True:
        try:
            raiz = tk.Tk()
            raiz.withdraw()
            raiz.attributes("-topmost", True)

            caminho = filedialog.askopenfilename(
                title="Selecione o arquivo .mq5",
                filetypes=[("Arquivos MetaTrader 5", "*.mq5")],
            )
            raiz.destroy()
        except Exception:
            caminho = ""

        caminho = caminho.strip().strip('"')
        if os.path.exists(caminho) and caminho.lower().endswith(".mq5"):
            return caminho

        print("Nenhum arquivo .mq5 valido foi selecionado. Tente novamente.")


def pedir_metaeditor():
    while True:
        try:
            raiz = tk.Tk()
            raiz.withdraw()
            raiz.attributes("-topmost", True)

            caminho = filedialog.askopenfilename(
                title="Selecione o metaeditor64.exe",
                filetypes=[("MetaEditor", "metaeditor64.exe"), ("Executaveis", "*.exe")],
            )
            raiz.destroy()
        except Exception:
            caminho = ""

        caminho = caminho.strip().strip('"')
        if os.path.exists(caminho):
            return caminho
        print("Nenhum executavel valido foi selecionado. Tente novamente.")


def compilar(metaeditor, arquivo_mq5, log_path):
    comando = [
        metaeditor,
        f"/compile:{arquivo_mq5}",
        f"/log:{log_path}",
    ]

    print("\nCompilando...\n")
    subprocess.run(comando)


def mostrar_log(log_path):
    if os.path.exists(log_path):
        print("\nLOG DA COMPILACAO:\n")
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            print(f.read())
    else:
        print("Log nao encontrado.")


def main():
    arquivo_mq5 = pedir_caminho_arquivo()

    metaeditor = encontrar_metaeditor()

    if not metaeditor:
        print("MetaEditor nao encontrado automaticamente.")
        metaeditor = pedir_metaeditor()
    else:
        print(f"MetaEditor encontrado em: {metaeditor}")

    log_path = os.path.join(os.path.dirname(arquivo_mq5), "log_compilacao.txt")

    compilar(metaeditor, arquivo_mq5, log_path)
    mostrar_log(log_path)


if __name__ == "__main__":
    main()

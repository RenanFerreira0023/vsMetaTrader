import os
import subprocess
import tkinter as tk
from tkinter import filedialog


def encontrar_metaeditor():
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminho_local = os.path.join(diretorio_script, "MetaEditor64.exe")

    caminhos_comuns = [
        caminho_local,
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
        print("Erro: MetaEditor64.exe nao encontrado no diretorio do script ou nos caminhos padrao.")
        return

    print(f"MetaEditor encontrado em: {metaeditor}")

    log_path = os.path.join(os.path.dirname(arquivo_mq5), "log_compilacao.txt")

    compilar(metaeditor, arquivo_mq5, log_path)
    mostrar_log(log_path)


if __name__ == "__main__":
    main()

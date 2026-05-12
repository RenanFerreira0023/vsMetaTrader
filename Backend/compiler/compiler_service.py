import os
import subprocess
import uuid
import logging
from typing import Dict, Any

logger = logging.getLogger("compiler_service")

def find_metaeditor():
    """Localiza o executável do MetaEditor64."""
    # Tenta no diretório específico onde sabemos que está
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_local = os.path.join(base_dir, "MetaEditor64exe", "MetaEditor64.exe")
    
    caminhos_comuns = [
        caminho_local,
        r"C:\Program Files\MetaTrader 5\metaeditor64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\metaeditor64.exe",
    ]

    for caminho in caminhos_comuns:
        if os.path.exists(caminho):
            return caminho
    return None

def compile_mql_code(code: str, extension: str = ".mq5") -> Dict[str, Any]:
    """
    Compila o código MQL fornecido e retorna os resultados.
    """
    metaeditor = find_metaeditor()
    if not metaeditor:
        return {"success": False, "error": "MetaEditor64.exe não encontrado no sistema."}

    # Criar diretório temporário para compilação se não existir
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_compile")
    os.makedirs(temp_dir, exist_ok=True)

    # Gerar nome de arquivo único
    unique_id = str(uuid.uuid4())[:8]
    file_name = f"agent_robot_{unique_id}{extension}"
    file_path = os.path.join(temp_dir, file_name)
    log_path = os.path.join(temp_dir, f"{file_name}.log.txt")

    try:
        # Salvar o código no arquivo
        with open(file_path, "w", encoding="utf-16") as f: # MQL costuma preferir UTF-16 ou UTF-8 com BOM
            f.write(code)

        # Comando de compilação
        # /compile: path to file
        # /log: path to log file
        comando = [
            metaeditor,
            f"/compile:{file_path}",
            f"/log:{log_path}",
        ]

        logger.info(f"Executando compilação: {file_name}")
        # MQL MetaEditor retorna imediatamente se for chamado via subprocess? 
        # Geralmente ele roda e fecha. Usamos shell=True se necessário, mas primeiro tentamos direto.
        subprocess.run(comando, capture_output=True, timeout=30)

        # Ler o log gerado
        log_content = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-16", errors="ignore") as f:
                log_content = f.read()
        
        # Verificar se houve erro no log
        # O MetaEditor costuma escrever "0 error(s), 0 warning(s)" ou algo similar na última linha
        # Vamos ser mais criteriosos na detecção de erros.
        
        is_success = False
        errors_found = 0
        
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-16", errors="ignore") as f:
                log_content = f.read()
            
            # Tenta encontrar a contagem de erros no final do log
            # Pode vir como "0 error(s)" ou "0 errors"
            import re
            error_match = re.search(r"(\d+)\s+error", log_content)
            if error_match:
                errors_found = int(error_match.group(1))
                is_success = (errors_found == 0)
            else:
                # Fallback caso o formato mude: procura pela palavra 'error' fora de contextos normais
                # Mas geralmente o check acima é o mais confiável para MetaEditor.
                is_success = "0 error(s)" in log_content.lower() and "failed" not in log_content.lower()
        
        # --- NOVO: Exibe o log no console para monitoramento em tempo real ---
        print("\n" + "╔" + "═"*60 + "╗")
        print(f"║ COMPILAÇÃO MQL5: {file_name.ljust(41)} ║")
        print("╠" + "═"*60 + "╣")
        print(log_content.strip())
        status_msg = "✅ SUCESSO" if is_success else "❌ FALHA"
        print("╠" + "═"*60 + "╣")
        print(f"║ STATUS: {status_msg.ljust(51)} ║")
        print("╚" + "═"*60 + "╝\n")

        return {
            "success": is_success,
            "errors_count": errors_found,
            "log": log_content,
            "file_path": file_path if is_success else None
        }

    except Exception as e:
        logger.error(f"Erro durante a compilação: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # Limpezas opcionais: podemos decidir manter o arquivo se for sucesso
        # por enquanto vamos manter para debug se o usuário quiser ver
        if os.path.exists(log_path):
            try: os.remove(log_path)
            except: pass

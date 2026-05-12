import os
import httpx
import json
from rag.rag_service import rag_service
from compiler.compiler_service import compile_mql_code

async def search_robot_examples(query: str) -> str:
    """Busca fragmentos de código relevantes nos robôs do usuário via RAG."""
    results = await rag_service.search(query, top_k=3)
    if not results:
        return "No relevant examples found in your robots."
    response = "Relevant code examples from your robots:\n"
    for item in results:
        response += f"From {item['file']} (similarity {item['score']:.2f}):\n{item['content']}\n\n"
    return response

async def read_url_content(Url: str) -> str:
    """Lê o conteúdo de uma URL e limpa tags HTML para facilitar a leitura da IA."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(Url, timeout=10.0)
            response.raise_for_status()
            
            import re
            html = response.text
            html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<.*?>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:2500] 
    except Exception as e:
        return f"Error reading URL: {str(e)}"

def lookup_mql_error(error_code: str) -> str:
    """Busca a descrição de um código de erro MQL nos arquivos JSON locais."""
    base_path = os.path.join(os.path.dirname(__file__), "codigoErros")
    files = [
        "Avisos_do_Compilador.json",
        "Codigos_de_Retorno_do_Servidor_de_Negociacao.json",
        "Erros_de_Compilação.json",
        "Erros_em_Tempo_de_Execução.json"
    ]
    
    error_code = str(error_code).strip()
    
    for filename in files:
        path = os.path.join(base_path, filename)
        if not os.path.exists(path):
            continue
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Caso o JSON seja uma lista direta (Compilação, Avisos, Retorno)
                if isinstance(data, list):
                    for item in data:
                        if str(item.get("errorCode")) == error_code:
                            return f"Erro {error_code} encontrado em {filename}: {item.get('description')} ({item.get('constant', 'N/A')})"
                
                # Caso o JSON seja por categorias (Execução)
                elif isinstance(data, dict):
                    for category, items in data.items():
                        for item in items:
                            if str(item.get("errorCode")) == error_code:
                                return f"Erro {error_code} encontrado em {filename} ({category}): {item.get('description')} ({item.get('constant', 'N/A')})"
        except Exception as e:
            continue
            
    return f"Código de erro {error_code} não encontrado na base de dados local."

def _get_code_content(input_data: str) -> str:
    """Helper para decidir se o input é código bruto ou um caminho de arquivo."""
    if input_data.endswith(".mq5") or input_data.endswith(".mqh"):
        if os.path.exists(input_data):
            with open(input_data, "r", encoding="utf-8") as f:
                return f.read()
    return input_data

def validate_mql_structure(code: str) -> str:
    """Valida a estrutura básica de um código MQL (EA ou Indicator)."""
    actual_code = _get_code_content(code)
    has_oninit = 'OnInit' in actual_code
    has_ontick = 'OnTick' in actual_code
    has_ondeinit = 'OnDeinit' in actual_code
    has_oncalculate = 'OnCalculate' in actual_code
    is_ea = has_oninit and has_ontick
    is_indicator = has_oncalculate
    if is_ea:
        return "Valid EA structure: Has OnInit and OnTick."
    elif is_indicator:
        return "Valid Indicator structure: Has OnCalculate."
    else:
        return "Invalid structure: Missing OnInit/OnTick for EA or OnCalculate for Indicator."

def compile_meta_trader_code(code: str) -> str:
    """Compila o código MQL usando o MetaEditor real e retorna os erros se houver."""
    actual_code = _get_code_content(code)
    result = compile_mql_code(actual_code)
    if result.get("success"):
        return "Compilation Successful! No errors found."
    else:
        log = result.get("log", "Unknown error during compilation.")
        return f"Compilation Failed! Errors found in log:\n\n{log}"

async def explain_mql_function(function_name: str) -> str:
    """Explica uma função MQL baseada nos exemplos dos robôs do usuário."""
    results = await rag_service.search(f"function {function_name}", top_k=5)
    if not results:
        return f"No information found for function {function_name}."
    response = f"Information about {function_name}:\n"
    for item in results:
        if function_name in item['content']:
            response += f"From {item['file']}:\n{item['content']}\n\n"
    return response

# ─── Registro e Documentação de Ferramentas (Utilizado pelo ReAct) ────────

TOOLS_REGISTRY = {
    "search_robot_examples": search_robot_examples,
    "validate_mql_structure": validate_mql_structure,
    "compile_meta_trader_code": compile_meta_trader_code,
    "explain_mql_function": explain_mql_function,
    "read_url_content": read_url_content
}

TOOLS_DESCRIPTION = """Você tem acesso às seguintes ferramentas:
[
  {
    "name": "search_robot_examples",
    "description": "Busca exemplos de código nos seus robôs antigos.",
    "parameters": {"query": "termo de busca"}
  },
  {
    "name": "read_url_content",
    "description": "Lê a documentação oficial do MQL5 em uma URL. Use para aprender como usar funções (iClose, iMA, etc) ou componentes novos.",
    "parameters": {"Url": "link da documentação"}
  },
  {
    "name": "compile_meta_trader_code",
    "description": "Compila o código MQL. Aceita o CÓDIGO BRUTO ou o NOME DO ARQUIVO (ex: codigo-resumido.mq5).",
    "parameters": {"code": "código ou nome do arquivo"}
  },
  {
    "name": "validate_mql_structure",
    "description": "Valida a estrutura do código. Aceita o CÓDIGO BRUTO ou o NOME DO ARQUIVO.",
    "parameters": {"code": "código ou nome do arquivo"}
  },
  {
    "name": "explain_mql_function",
    "description": "Explica uma função MQL.",
    "parameters": {"function_name": "nome da função"}
  }
]"""

from rag import rag_engine
from compiler_service import compile_mql_code

def search_robot_examples(query: str) -> str:
    """Busca fragmentos de código relevantes nos robôs do usuário via RAG."""
    results = rag_engine.search_context(query, top_k=3)
    if not results:
        return "No relevant examples found in your robots."
    response = "Relevant code examples from your robots:\n"
    for chunk, meta in results:
        response += f"From {meta['file']} (chunk {meta['chunk_id']}):\n{chunk}\n\n"
    return response

def validate_mql_structure(code: str) -> str:
    """Valida a estrutura básica de um código MQL (EA ou Indicator)."""
    has_oninit = 'OnInit' in code
    has_ontick = 'OnTick' in code
    has_ondeinit = 'OnDeinit' in code
    has_oncalculate = 'OnCalculate' in code
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
    result = compile_mql_code(code)
    if result.get("success"):
        return "Compilation Successful! No errors found."
    else:
        log = result.get("log", "Unknown error during compilation.")
        return f"Compilation Failed! Errors found in log:\n\n{log}"

def explain_mql_function(function_name: str) -> str:
    """Explica uma função MQL baseada nos exemplos dos robôs do usuário."""
    results = rag_engine.search_context(f"function {function_name}", top_k=5)
    if not results:
        return f"No information found for function {function_name}."
    response = f"Information about {function_name}:\n"
    for chunk, meta in results:
        if function_name in chunk:
            response += f"From {meta['file']}:\n{chunk}\n\n"
    return response


# ─── Registro e Documentação de Ferramentas (Utilizado pelo ReAct) ────────

TOOLS_REGISTRY = {
    "search_robot_examples": search_robot_examples,
    "validate_mql_structure": validate_mql_structure,
    "compile_meta_trader_code": compile_meta_trader_code,
    "explain_mql_function": explain_mql_function
}

TOOLS_DESCRIPTION = """Você tem acesso às seguintes ferramentas. Caso precise utilizar uma, você DEVE retornar ESTRITAMENTE o formato JSON descrito na regra!
[
  {
    "name": "search_robot_examples",
    "description": "Busca exemplos de código relevantes nos robôs do usuário para inspirar a geração de novo código MQL.",
    "parameters": {"query": "<descrição do que procurar>"}
  },
  {
    "name": "compile_meta_trader_code",
    "description": "Compila o código MQL usando o MetaEditor real. Use SEMPRE que gerar um código novo para garantir que ele não tem erros de sintaxe.",
    "parameters": {"code": "<o código MQL completo para compilar>"}
  },
  {
    "name": "validate_mql_structure",
    "description": "Valida se um código MQL tem a estrutura básica de um EA ou Indicator.",
    "parameters": {"code": "<o código MQL a validar>"}
  },
  {
    "name": "explain_mql_function",
    "description": "Explica uma função MQL baseada nos exemplos dos robôs do usuário.",
    "parameters": {"function_name": "<nome da função>"}
  }
]"""

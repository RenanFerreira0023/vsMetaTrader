import json
import logging
import ollama
from typing import List, Dict, Any, AsyncGenerator
from config import settings
from rag.rag_service import rag_service
from compiler.compiler_service import compile_mql_code
from compiler.error_parser import MqlErrorParser
from prompts.prompts import get_system_prompt
from mql5_sanitizer import sanitize as mql5_sanitize

logger = logging.getLogger("mql_agent")

class MqlAgent:
    def __init__(self):
        self.error_parser = MqlErrorParser()
        self.max_retries = 3

    async def generate_ea(self, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        Gera um Expert Advisor completo seguindo o loop:
        Geração -> Compilação -> Correção
        """
        yield "🔍 Analisando sua solicitação e buscando exemplos relevantes...\n"
        
        # 1. Busca RAG especializada
        # Busca globais, oninit, ontick separadamente para contexto rico
        context_chunks = []
        context_chunks.extend(await rag_service.search(user_prompt, top_k=2, filter_type='globals'))
        context_chunks.extend(await rag_service.search(user_prompt, top_k=2, filter_type='OnTick'))
        
        context_str = "ESTUDO DE CASO (EXEMPLOS REAIS):\n"
        for item in context_chunks:
            context_str += f"--- Exemplo ({item['metadata']['type']}) ---\n{item['content']}\n\n"

        system_prompt = get_system_prompt()
        
        # 2. Primeira Geração
        yield "🤖 Gerando versão inicial do código MQL5...\n"
        
        current_code = await self._call_llm(user_prompt, context_str, system_prompt)
        current_code = mql5_sanitize(current_code)
        
        # 3. Loop de Compilação e Correção
        for attempt in range(self.max_retries):
            yield f"🛠️ Tentativa {attempt + 1}: Compilando e validando...\n"
            
            comp_result = compile_mql_code(current_code)
            
            if comp_result.get("success"):
                yield "✅ Compilação bem-sucedida!\n"
                yield f"\n```mql5\n{current_code}\n```\n"
                return

            # Se falhou, parsear erros e tentar corrigir
            log_content = comp_result.get("log", "")
            errors = self.error_parser.parse(log_content)
            error_msg = self.error_parser.format_for_llm(errors)
            
            yield f"⚠️ Erros encontrados. Solicitando correção automática...\n"
            # yield f"DEBUG ERRORS: {error_msg}\n"
            
            # Prompt de correção
            fix_prompt = f"""
            O código gerado anteriormente teve erros de compilação.
            
            {error_msg}
            
            CÓDIGO ATUAL:
            {current_code}
            
            Por favor, corrija os erros acima e retorne o código completo e funcional.
            Mantenha a lógica da estratégia solicitada: {user_prompt}
            """
            
            current_code = await self._call_llm(fix_prompt, context_str, system_prompt)
            current_code = mql5_sanitize(current_code)

        yield "❌ Não foi possível corrigir todos os erros após as tentativas limite.\n"
        yield f"Última versão gerada (com possíveis erros):\n\n```mql5\n{current_code}\n```\n"

    async def _call_llm(self, prompt: str, context: str, system: str) -> str:
        """Helper para chamar o Ollama."""
        messages = [
            {'role': 'system', 'content': system},
            {'role': 'system', 'content': context},
            {'role': 'user', 'content': prompt}
        ]
        
        client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        response = await client.chat(
            model=settings.MODEL_NAME,
            messages=messages,
            options={'temperature': 0.1}
        )
        
        # Extrair código se vier dentro de blocos ```mql5
        content = response['message']['content']
        code_match = re.search(r'```(?:mql5|cpp)?\n(.*?)\n```', content, re.DOTALL | re.IGNORECASE)
        if code_match:
            return code_match.group(1)
        return content

# Instância global
mql_agent = MqlAgent()

import re # Para o regex acima

import re
from typing import Dict, List, Optional

class MqlParser:
    """
    Parser especializado em extrair blocos lógicos de arquivos MQL5.
    Focado em identificar: OnInit, OnDeinit, OnTick, OnCalculate, 
    variáveis globais, inputs e funções customizadas.
    """
    
    def __init__(self):
        # Regex para identificar funções comuns do MQL5
        self.function_patterns = {
            'OnInit': r'(int\s+OnInit\s*\([^)]*\)\s*\{)',
            'OnDeinit': r'(void\s+OnDeinit\s*\([^)]*\)\s*\{)',
            'OnTick': r'(void\s+OnTick\s*\([^)]*\)\s*\{)',
            'OnCalculate': r'(int\s+OnCalculate\s*\([^)]*\)\s*\{)',
            'OnTimer': r'(void\s+OnTimer\s*\([^)]*\)\s*\{)',
            'OnTrade': r'(void\s+OnTrade\s*\([^)]*\)\s*\{)',
            'OnChartEvent': r'(void\s+OnChartEvent\s*\([^)]*\)\s*\{)',
        }

    def parse(self, code: str) -> List[Dict[str, str]]:
        """
        Analisa o código e retorna uma lista de chunks com metadados.
        """
        chunks = []
        
        # 1. Extrair Inputs e Globais (tudo antes da primeira função)
        first_func_pos = len(code)
        for pattern in self.function_patterns.values():
            match = re.search(pattern, code)
            if match and match.start() < first_func_pos:
                first_func_pos = match.start()
        
        globals_part = code[:first_func_pos].strip()
        if globals_part:
            chunks.append({
                'type': 'globals',
                'content': globals_part
            })

        # 2. Extrair funções conhecidas
        for func_name, pattern in self.function_patterns.items():
            chunks.extend(self._extract_function_block(code, func_name, pattern))

        # 3. Extrair funções customizadas (simplificado: qualquer coisa que pareça uma função)
        # TODO: Implementar parser mais robusto para funções customizadas se necessário
        
        return chunks

    def _extract_function_block(self, code: str, func_name: str, pattern: str) -> List[Dict[str, str]]:
        """
        Extrai o bloco completo de uma função baseado no balanço de chaves {}.
        """
        results = []
        for match in re.finditer(pattern, code):
            start_pos = match.start()
            # Encontrar o fim do bloco balanceando chaves
            brace_count = 0
            end_pos = -1
            
            for i in range(start_pos, len(code)):
                if code[i] == '{':
                    brace_count += 1
                elif code[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos != -1:
                results.append({
                    'type': func_name,
                    'content': code[start_pos:end_pos].strip()
                })
        
        return results

# Exemplo de uso:
# parser = MqlParser()
# chunks = parser.parse(mql_code)

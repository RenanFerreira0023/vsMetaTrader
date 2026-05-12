import re
from typing import List, Dict, Any

class MqlErrorParser:
    """
    Parser para logs de compilação do MetaEditor.
    Extrai informações estruturadas sobre erros e avisos.
    """
    
    def parse(self, log_content: str) -> List[Dict[str, Any]]:
        r"""
        Analisa o log e retorna uma lista de erros.
        Exemplo de linha do log:
        'C:\Path\To\File.mq5(45,10) : error 123: unexpected token'
        """
        errors = []
        # Regex para capturar: arquivo, linha, coluna, tipo (error/warning), código, descrição
        pattern = r'(?P<file>.*)\((?P<line>\d+),(?P<col>\d+)\)\s*:\s*(?P<severity>error|warning)\s+(?P<code>\d+)\s*:\s*(?P<description>.*)'
        
        lines = log_content.splitlines()
        for line in lines:
            match = re.search(pattern, line)
            if match:
                error_data = match.groupdict()
                error_data['line'] = int(error_data['line'])
                error_data['col'] = int(error_data['col'])
                errors.append(error_data)
        
        return errors

    def format_for_llm(self, errors: List[Dict[str, Any]]) -> str:
        """Formata a lista de erros para ser enviada ao LLM."""
        if not errors:
            return "No errors found."
        
        formatted = "COMPILATION ERRORS FOUND:\n"
        for i, err in enumerate(errors):
            formatted += f"{i+1}. Line {err['line']}, Col {err['col']}: [{err['severity']} {err['code']}] {err['description']}\n"
        
        return formatted

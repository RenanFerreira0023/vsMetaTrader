# Plano de Ação: Migração para Ollama e DeepSeek-Coder

Este documento descreve as etapas para substituir o motor de inferência **GPT4All** pelo **Ollama** e adotar o modelo **DeepSeek-Coder**, focado em geração de código.

## 1. Justificativa
- **DeepSeek-Coder:** É uma das melhores LLMs abertas para programação, superando modelos genéricos em tarefas de MQL5.
- **Ollama:** Oferece melhor gerenciamento de memória, suporte superior a GPUs NVIDIA e uma API mais robusta que o GPT4All para integração com backends.

## 2. Pré-requisitos (Ações do Usuário)
Antes de aplicarmos as mudanças no código, você precisará:
1. **Instalar o Ollama:** Baixe e instale em [ollama.com](https://ollama.com/).
2. **Baixar o Modelo:** No terminal, execute:
   ```bash
   ollama pull deepseek-coder-v2
   ```
   *(Ou a versão desejada, como `deepseek-coder:6.7b-instruct-q4_K_M` para máquinas com menos VRAM).*

## 3. Etapas de Implementação no Código

### Fase 1: Atualização de Dependências
- Remover `gpt4all` do `requirements.txt`.
- Adicionar `ollama` (biblioteca oficial em Python).

### Fase 2: Configuração (`config.py`)
- Adicionar variável `OLLAMA_BASE_URL` (padrão: `http://localhost:11434`).
- Atualizar `MODEL_NAME` para o nome usado no Ollama (ex: `deepseek-coder-v2`).

### Fase 3: Refatoração do Motor de Chat (`api.py`)
- Substituir a inicialização do `GPT4All` no `lifespan` pela conexão com o cliente Ollama.
- Atualizar a função `response_generator` para usar o método `ollama.chat` com suporte a streaming.
- Manter a lógica de **Agent Loop (ReAct)** e **Auto-validação**, adaptando o tratamento de tags `<think>` se necessário (o DeepSeek-Coder puro geralmente não usa essa tag, mas o DeepSeek-R1 sim).

### Fase 4: Ajuste de Prompts (`prompts.py`)
- Revisar a persona para garantir compatibilidade com o formato de instrução do DeepSeek-Coder.

## 4. Próximos Passos
Após sua aprovação deste plano, procederei com:
1. Edição do `requirements.txt`.
2. Modificação do `config.py`.
3. Refatoração completa da lógica de carregamento e inferência no `api.py`.

---
> [!IMPORTANT]
> Certifique-se de que o Ollama esteja rodando em segundo plano antes de iniciarmos os testes após a migração.

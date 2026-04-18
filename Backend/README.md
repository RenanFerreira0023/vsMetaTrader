# 🤖 vsMetaTrader - AI Robot Factory

Este projeto é uma **experiência prática avançada** explorando o uso de **LLMs (Large Language Models)**, **Sistemas de Agentes Autônomos** e técnicas de **Fine-tuning/RAG** para a geração automatizada de estratégias de trading em MQL4/MQL5.

O objetivo principal é criar um ecossistema onde uma IA não apenas escreva código, mas aprenda com robôs existentes, valide sua própria saída e utilize ferramentas para buscar a melhor implementação possível para o MetaTrader 4/5.

## 🧠 O que este projeto faz?

- **Geração Inteligente de código MQL:** Cria Experts Advisors (EAs), Indicadores e Scripts funcionais a partir de linguagem natural.
- **RAG (Retrieval-Augmented Generation):** O sistema "lê" seus robôs locais na pasta `robots/` e aprende seu estilo de codificação, bibliotecas preferidas e padrões de arquitetura.
- **Agente ReAct (Reasoning and Acting):** A IA possui autonomia para executar "ferramentas" (procurar documentação, validar sintaxe, buscar exemplos) antes de entregar o código final.
- **Memória de Longo Prazo:** Mantém o contexto de sessões anteriores utilizando bancos de dados PostgreSQL para continuidade no desenvolvimento de estratégias complexas.
- **Streaming de Resposta:** Respostas em tempo real via WebSocket/HTTP para uma experiência de desenvolvimento fluida.

---

## 🛠️ Requisitos Técnicos e Versões

Para rodar este projeto com alta performance (especialmente usando aceleração por GPU), utilize as versões recomendadas abaixo:

| Tecnologia | Versão Recomendada | Link de Download |
| :--- | :--- | :--- |
| **Python** | 3.12.x | [Python Official](https://www.python.org/downloads/windows/) |
| **CUDA Toolkit** | 12.1 | [NVIDIA CUDA Archive](https://developer.nvidia.com/cuda-12-1-0-download-archive) |
| **PyTorch (CUDA)** | 2.2+ (cu121) | [PyTorch.org](https://pytorch.org/get-started/locally/) |
| **Bancos de Dados** | PostgreSQL 16+ | [PostgreSQL Downloads](https://www.postgresql.org/download/windows/) |

### Comando para Instalação do Torch com CUDA 12.1:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 🚀 Instalação e Execução

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/RenanFerreira0023/vsMetaTrader-Backend
   cd vsMetaTrader-Backend
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o ambiente:**
   - Copie o arquivo `Exemplo-env` para `.env`.
   - Configure suas credenciais do PostgreSQL e o caminho dos modelos GGUF.
   ```bash
   cp Exemplo-env .env
   ```

5. **Adicione seu conhecimento (Opcional):**
   - Coloque arquivos `.mq4` ou `.mq5` na pasta `robots/`. Eles serão usados pelo motor de RAG para dar "personalidade" ao código gerado.

6. **Inicie a API:**
   ```bash
   python api.py
   ```

---

## 📂 Estrutura do Projeto

- `api.py`: Servidor FastAPI com lógica de Agent Loop e Streaming.
- `rag.py`: Motor de busca semântica usando FAISS e Sentence-Transformers.
- `tools.py`: Ferramentas que o Agente pode invocar autonomamente.
- `prompts.py`: Engenharia de prompt e definição da persona do especialista MQL.
- `database.py`: Gestão de persistência com SQLAlchemy e PostgreSQL.
- `models/`: Pasta destinada aos modelos LLM (ex: DeepSeek-R1 Distill).

---

## 🏗️ Conceito de Experiência

Este projeto não é apenas um utilitário, mas uma **prova de conceito** em:
- **Agentes:** Implementação de loops ReAct onde a IA decide quando precisa de mais informação.
- **Fine-tuning via Contexto:** Uso de RAG massivo para simular um modelo finetunado em MQL sem o custo de treinamento de pesos.
- **Hardware Local:** Otimização para rodar LLMs de 8B a 32B parâmetros em hardware doméstico (RTX 4060+) com latência mínima.

---

**Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023)**  
*Parte do ecossistema vsMetaTrader para automação de trading com IA.*

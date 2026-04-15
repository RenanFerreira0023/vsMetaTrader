# 🤖 MQL Robot Factory API

API para geração automática de código MQL4/MQL5 para MetaTrader usando IA com RAG (Retrieval-Augmented Generation).

## 🧠 O que faz?
- **Geração de Código MQL:** Cria Experts Advisors (EAs) e Indicadores funcionais
- **RAG Personalizado:** Aprende o estilo de programação dos seus robôs existentes
- **Agente Inteligente:** Usa ferramentas para validar código, buscar exemplos e explicar funções
- **Streaming:** Respostas em tempo real via WebSocket/HTTP

Construído com **FastAPI**, **DeepSeek-R1** e **Sentence-Transformers** para embeddings.

---

## ⚠️ Requisitos

- **Python 3.12**
- **CUDA Toolkit 12** (opcional, acelera GPU)
- Placa NVIDIA (opcional)
- PostgreSQL ou SQLite

---

## 🚀 Instalação e Execução

1. **Clone e configure:**
```bash
git clone <seu-repo>
cd vsMetaTrader-Backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Configure ambiente:**
```bash
cp Exemplo-env .env
# Edite .env com suas configurações
```

3. **Adicione seus robôs:**
```bash
# Coloque arquivos .mq4/.mq5 na pasta robots/
# Exemplo: robots/meus_robos/EA_Simples.mq5
```

4. **Execute:**
```bash
python api.py
```

5. **Teste:**
```bash
# Health check
curl http://localhost:8000/health

# Indexar robôs
curl -X POST http://localhost:8000/index-robots -d '{"path": "./robots"}'

# Gerar código
curl -X POST http://localhost:8000/chat \
  -d '{"prompt": "Crie um EA que compra no RSI < 30", "session_uuid": "test"}'
```

---

## 📁 Estrutura

```
├── api.py          # Servidor FastAPI
├── rag.py          # Motor de RAG com FAISS
├── tools.py        # Ferramentas do agente
├── prompts.py      # Sistema prompt
├── database.py     # Models SQLAlchemy
├── config.py       # Configurações
├── robots/         # Seus arquivos MQL (não versionar)
├── models/         # Modelos baixados (não versionar)
└── requirements.txt
```

---

## 🔧 Endpoints

- `GET /health` - Status do sistema
- `POST /index-robots` - Reindexar robôs para RAG
- `POST /chat` - Gerar código MQL com streaming

---

## 🎯 Como Usar

1. Adicione seus robôs na pasta `robots/`
2. Inicie o servidor
3. Faça POST para `/index-robots`
4. Use `/chat` para gerar código personalizado

O RAG injeta exemplos do seu estilo no prompt automaticamente!
DB_NAME=super-aluno-ingles # <- O banco já deve existir

# Configurações do Motor de IA
USE_GPU=True
MODEL_NAME=DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf
CONTEXT_SIZE=16384         # Contexto expandido para digerir aulas densas
```

3. Inicie o Servidor:
```bash
python api.py
```
A API rodará localmente respondendo na porta `8000`.

> [!TIP]
> **Acesso Externo / Como liberar no Windows Firewall:**
> Se precisar que a API seja acessível por outros dispositivos, siga este passo a passo:
> 1. Pressione a tecla `Win` e procure por **"Windows Defender Firewall com Segurança Avançada"**.
> 2. No menu à esquerda, clique em **Regras de Entrada**.
> 3. No menu à direita, clique em **Nova Regra...**.
> 4. Escolha o tipo **Porta** e clique em Avançar.
> 5. Selecione **TCP** e em Portas locais específicas, digite **8000**.
> 6. Selecione **Permitir a conexão** e avance até o final.
> 7. Dê um nome como `Backend Super Aluno (8000)` e finalize.

---

## 🛠️ Resumo Técnico das Features Adicionadas

- **Ajustes de Persona Externalizados (`prompts.py`):** Todo o comportamento da IA como "Super Aluno" que fala PT-BR e captura anotações e pronúncias de aulas foi isolado em um módulo prático.
- **Auto-Correção (Agent Loop ReAct):** O servidor percebe e contorna falhas na geração das requisições JSON da IA de forma transparente ao usuário (trabalhando limites de tentativas).
- **Adequação Limite de Token:** O sistema adota limites agressivos de Tokens (16K ctx) garantindo que os vídeos passem no *input*.
- **Rotas Principais:** Trabalhos por trás dos panos nos endpoints `/chat` (gerado em pedaços e validado) e fluxo rápido de áudio no `/uploadVideo` acelerado via CUDA 12.

---
**Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023)**.  
Acesse a Interface: [frontend-agente-estudos-ingles](https://github.com/RenanFerreira0023/frontend-agente-estudos-ingles)

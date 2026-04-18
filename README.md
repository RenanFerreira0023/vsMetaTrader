# 🤖 vsMetaTrader

Este projeto é uma **iniciativa de estudo e pesquisa em Inteligência Artificial** aplicada à automação de negociações no mercado financeiro (MetaTrader 4 e 5). O objetivo é explorar as capacidades de Agentes Autônomos, LLMs (Large Language Models) e RAG (Retrieval-Augmented Generation) para criar estratégias de trading de alta qualidade.

## 📂 Estrutura do Repositório

O projeto está dividido em duas partes principais:

### 1. [Backend](./Backend)
É o "cérebro" do sistema. Desenvolvido em **Python** com **FastAPI**, ele gerencia:
- O loop de raciocínio do **Agente IA** (Persona especialista em MQL5).
- O motor de **RAG**, que utiliza códigos locais para aprender padrões de trading.
- Integração com modelos LLM locais (via GGUF/Llama.cpp).
- Persistência de sessões e memória em **PostgreSQL**.

### 2. [Frontend](./Frontend)
Interface de usuário para interação com o agente de IA, permitindo o acompanhamento da geração de código e configuração das estratégias de forma amigável.

---

## 🔬 Objetivo do Estudo
Este é um projeto experimental focado em:
- **Agentes Autônomos:** Implementação de loops ReAct para tomada de decisão.
- **RAG Massivo:** Alimentar a IA com documentação técnica e códigos legados para precisão extrema.
- **Performance Local:** Execução de modelos de IA avançados em hardware doméstico (GPUs NVIDIA).

---
Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023).
# ✦ DeepSeek-R1 API - Documentação

Esta API foi desenvolvida para servir como uma interface de "back-end" para o modelo de linguagem **DeepSeek-R1-Distill-Llama-8B**, permitindo que outros sistemas ou ferramentas (como o Postman) interajam com a inteligência artificial sem a necessidade de uma interface gráfica.

---

## 🛠️ Tecnologias Utilizadas
1. **FastAPI**: Framework web moderno e de alto desempenho para Python. Ele gerencia as rotas e a comunicação HTTP.
2. **GPT4All**: Biblioteca que permite rodar modelos de linguagem pesados localmente, utilizando CPU ou GPU.
3. **Pydantic**: Utilizado para validar os dados que entram e saem da API (garantindo que o JSON esteja correto).
4. **Uvicorn**: O servidor que "roda" o código FastAPI.

---

## 🚀 Como Rodar a API
1. Ative seu ambiente virtual (se estiver usando um).
2. Execute o comando no terminal:
   ```bash
   python api.py
   ```
   *O servidor iniciará em `http://localhost:8000`.*

---

## 🛣️ Rotas Disponíveis

### 1. `POST /chat`
É a rota principal de conversação. 
*   **Ação**: Recebe uma pergunta, processa no modelo local e retorna a resposta gerada.
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "prompt": "Sua pergunta aqui"
    }
    ```
*   **Lógica Interna (Configuração Atual)**:
    *   **Max Tokens**: 2048 (permite respostas bem longas).
    *   **Temperatura**: 0.5 (equilíbrio entre precisão e fluidez).
*   **Retorno**: `{"response": "Texto gerado pela IA..."}`

### 2. `GET /health`
Uma rota simples de monitoramento.
*   **Ação**: Verifica se a API está online e se o modelo foi carregado com sucesso.
*   **Retorno**: `{"status": "ok", "model": "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"}`

### 3. `GET /docs`
O FastAPI gera automaticamente uma documentação interativa.
*   **Ação**: Acesse pelo navegador para ver todos os detalhes técnicos e testar as rotas visualmente.

---

## 🧠 Ciclo de Vida do Modelo
Diferente do Streamlit (que pode recarregar a cada clique), a API carrega o modelo **uma única vez** assim que o servidor inicia. Isso economiza memória e torna as respostas subsequentes muito mais rápidas, pois o modelo já está "aquecido" na memória RAM.

---

## 📝 Notas de Implementação
*   O modelo está configurado para usar o dispositivo `kompute` (aceleração por GPU), caso disponível.
*   O sistema utiliza `chat_session()` do GPT4All para manter a coerência durante a geração da resposta.
*   Erros inesperados durante a geração são capturados e retornados como `Status 500` com a descrição do erro para facilitar o debug.

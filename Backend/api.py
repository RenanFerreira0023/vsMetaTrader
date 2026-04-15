from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gpt4all import GPT4All
import os
import uvicorn
import logging
import sys
from typing import Optional
from config import settings
from utils.utils import decode_base64

# ─── Configuração de Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("api")

# ─── Inicialização da APP ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME, 
    description=f"API para interação com o modelo {settings.MODEL_NAME}"
)

# ─── Middlewares ────────────────────────────────────────────────────────────
# 1. Trusted Host Middleware (Segurança de cabeçalho Host)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.TRUSTED_HOSTS
)

# 2. CORS Middleware (Restrição de origens)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Inicialização do Modelo ────────────────────────────────────────────────
os.makedirs(settings.MODEL_PATH, exist_ok=True)
logger.info(f"⏳ Carregando modelo {settings.MODEL_NAME} em {settings.MODEL_PATH}...")

try:
    model = GPT4All(settings.MODEL_NAME, model_path=settings.MODEL_PATH, allow_download=True)
    logger.info("✅ Modelo carregado com sucesso!")
except Exception as e:
    logger.critical(f"❌ Erro crítico ao carregar o modelo: {e}")
    raise e

# ─── Modelos de Dados ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    prompt: str
    file: Optional[str] = None

# ─── Rotas ──────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Rota para enviar um prompt ao modelo e receber a resposta gerada via streaming.
    """
    try:
        file_content = None
        if request.file:
            try:
                file_content = decode_base64(request.file)
                logger.info("Arquivo recebido e decodificado via base64.")
            except Exception as e:
                logger.warning(f"Erro ao decodificar arquivo: {e}")
                raise HTTPException(status_code=400, detail=f"Erro ao decodificar arquivo base64: {str(e)}")

        def response_generator():
            with model.chat_session():
                prompt = request.prompt
                if file_content and isinstance(file_content, str):
                    prompt = f"Conteúdo do arquivo enviado:\n---\n{file_content}\n---\n\n{prompt}\n---\n\nResponda em portugues do brasil"
                
                logger.info(f"Gerando resposta para prompt: {request.prompt[:50]}...")
                for token in model.generate(
                    prompt,
                    max_tokens=settings.MAX_TOKENS, 
                    temp=settings.TEMPERATURE, 
                    streaming=True
                ):
                    yield token

        return StreamingResponse(response_generator(), media_type="text/plain")
            
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar chat")

@app.get("/health")
async def health():
    """
    Verifica se a API e o modelo estão operacionais.
    """
    return {"status": "ok", "model": settings.MODEL_NAME}

if __name__ == "__main__":
    # Configuração de execução do servidor
    logger.info(f"Iniciando {settings.APP_NAME} em {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "api:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )

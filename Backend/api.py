import os
# Forçar modo offline para evitar erros de conexão (DNS/HuggingFace)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
import ollama
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys
import json
import re
import uuid

from config import settings
from database import init_db
from tasks import start_scheduler
from rag import rag_engine
from schemas import ChatRequest, IndexRobotsRequest
from agent import generate_mql_response

# ─── Configuração de Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("api")

# ─── Estado Global do Modelo ────────────────────────────────────────────────
state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação: carrega o modelo na inicialização.
    """
    logger.info("🔧 Inicializando Banco de Dados...")
    init_db()
    
    logger.info("⚙️ Acordando Trabalhadores de Fundo (Background Tasks)...")
    start_scheduler()
    
    logger.info("🔍 Indexando robôs para RAG em segundo plano...")
    import threading
    def start_indexing():
        try:
            rag_engine.index_robots(settings.ROBOTS_PATH)
            logger.info("✅ Robôs indexados com sucesso!")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao indexar robôs: {e}")
    
    threading.Thread(target=start_indexing, daemon=True).start()
    
    logger.info(f"⏳ Verificando conexão com Ollama em {settings.OLLAMA_BASE_URL}...")
    try:
        client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        await client.list()
        state["client"] = client
        logger.info("✅ Conexão com Ollama estabelecida!")
    except Exception as e:
        logger.critical(f"❌ Erro ao conectar com Ollama: {e}")
        raise e
    
    yield
    state.clear()
    logger.info("🛑 Servidor desligado e recursos liberados.")

# ─── Inicialização da APP ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME, 
    description=f"API para geração de código MQL usando {settings.MODEL_NAME}",
    lifespan=lifespan
)

# ─── Middlewares ────────────────────────────────────────────────────────────
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.TRUSTED_HOSTS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Rotas ──────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(request: Request):
    """
    Rota tolerante para receber prompts, aceitando JSONs 'quebrados' com quebras de linha manuais.
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        try:
            cleaned_body = re.sub(r'\n', '\\n', body_str)
            cleaned_body = re.sub(r'\\n\s*"', '"', cleaned_body)
            data = json.loads(cleaned_body)
        except Exception:
            raise HTTPException(status_code=400, detail="Erro ao processar JSON. Certifique-se de que os campos 'prompt' e 'session_uuid' estão presentes.")

    estagio0 = data.get("estagio0", "")
    estagio1 = data.get("estagio1", "")
    estagio2 = data.get("estagio2", "")
    estagio3 = data.get("estagio3", "")
    prompt_text = data.get("prompt", "")
    session_uuid = data.get("session_uuid") or str(uuid.uuid4())

    if estagio0 or estagio1 or estagio2 or estagio3:
        prompt_text = (
            f"ESTÁGIO 0 (Panorama Geral): {estagio0}\n"
            f"ESTÁGIO 1 (Indicadores): {estagio1}\n"
            f"ESTÁGIO 2 (Regra de Abertura): {estagio2}\n"
            f"ESTÁGIO 3 (Proteção/Saída): {estagio3}"
        )

    if not prompt_text:
        raise HTTPException(status_code=400, detail="O campo 'prompt' ou os estágios são obrigatórios.")

    client = state.get("client")
    if not client:
        raise HTTPException(status_code=503, detail="Ollama não está disponível")

    try:
        headers = {"X-Session-ID": session_uuid}
        headers["Access-Control-Expose-Headers"] = "X-Session-ID"
        return StreamingResponse(
            generate_mql_response(session_uuid, estagio0, estagio1, estagio2, estagio3, prompt_text, client), 
            media_type="text/plain", 
            headers=headers
        )
            
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar chat")

@app.get("/health")
async def health():
    return {
        "status": "ok" if "client" in state else "error", 
        "model": settings.MODEL_NAME,
        "ollama_url": settings.OLLAMA_BASE_URL
    }

@app.post("/index-robots")
async def index_robots(request: IndexRobotsRequest):
    """
    Reindexa os robôs do usuário para o RAG.
    """
    try:
        rag_engine.index_robots(request.path)
        stats = {
            "files_indexed": len(rag_engine.chunks),
            "total_chunks": len(rag_engine.chunks)
        }
        return {"message": "Robôs indexados com sucesso", "stats": stats}
    except Exception as e:
        logger.error(f"Erro ao indexar robôs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Iniciando {settings.APP_NAME} em {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "api:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )

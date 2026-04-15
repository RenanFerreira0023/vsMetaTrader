import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from rag import rag_engine
from config import settings

logger = logging.getLogger("tasks")
scheduler = AsyncIOScheduler()

async def reindex_robots():
    """
    Rotina que reindexa os robôs do usuário para o RAG periodicamente.
    """
    logger.info("⏰ [Job Background] Iniciando reindexação dos robôs...")
    try:
        rag_engine.index_robots(settings.ROBOTS_PATH)
        logger.info("✅ Robôs reindexados com sucesso.")
    except Exception as e:
        logger.error(f"Erro na reindexação: {e}")

def start_scheduler():
    """Inicia o agendador de tarefas em background."""
    # Reindexar a cada 24 horas
    scheduler.add_job(reindex_robots, trigger='interval', hours=24)
    scheduler.start()
    logger.info("⏱️ APScheduler (Background Worker) acoplado e rolando lindamente.")

import os
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from database import SessionLocal, VectorChunk, engine
from rag.mql_parser import MqlParser
import ollama
from config import settings

logger = logging.getLogger("rag_service")

class RagService:
    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name
        self.parser = MqlParser()

    async def get_embedding(self, text: str) -> List[float]:
        """Gera embedding usando Ollama."""
        try:
            # Limitar o tamanho do texto para evitar erro de contexto (Ollama/Nomic)
            # 4000 caracteres é uma margem muito segura.
            truncated_text = text[:4000]
            
            client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
            response = await client.embeddings(model=self.model_name, prompt=truncated_text)
            return response['embedding']
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return []

    def index_robots(self, path: str):
        """Indexa robôs usando o parser especializado e salva no pgvector."""
        db = SessionLocal()
        try:
            # Limpar chunks antigos (opcional, ou podemos fazer incremental)
            # db.query(VectorChunk).delete()
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(('.mq4', '.mq5')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Remover caracteres NUL (0x00) que podem quebrar o banco/parser
                            content = content.replace('\x00', '')
                            
                            if not content.strip():
                                continue

                            # Parsear o código em chunks funcionais
                            chunks = self.parser.parse(content)
                            
                            for chunk_data in chunks:
                                chunk_text = chunk_data['content']
                                chunk_type = chunk_data['type']
                                
                                # Gerar embedding
                                import asyncio
                                embedding = asyncio.run(self.get_embedding(chunk_text))
                                if not embedding:
                                    continue
                                    
                                # Salvar no banco
                                new_chunk = VectorChunk(
                                    file_path=file_path,
                                    content=chunk_text,
                                    embedding=embedding,
                                    metadata_json={'type': chunk_type, 'file': file}
                                )
                                db.add(new_chunk)
                            
                            db.commit()
                            logger.info(f"✅ Indexado: {file}")
                        except Exception as e:
                            logger.error(f"Erro ao ler {file_path}: {e}")
                            db.rollback()
        finally:
            db.close()

    async def search(self, query: str, top_k: int = 5, filter_type: str = None) -> List[Dict[str, Any]]:
        """Busca semântica no pgvector."""
        query_embedding = await self.get_embedding(query)
        if not query_embedding:
            return []

        db = SessionLocal()
        try:
            # Usando SQL puro para busca de similaridade de cosseno com pgvector
            # O operador <=> é para distância de cosseno. <-> é L2.
            
            sql = text("""
                SELECT file_path, content, metadata_json, (embedding <=> :emb) as distance
                FROM vector_chunks
                WHERE 1=1
            """)
            
            params = {"emb": str(query_embedding)}
            
            if filter_type:
                sql = text(str(sql) + " AND metadata_json->>'type' = :type")
                params["type"] = filter_type
                
            sql = text(str(sql) + " ORDER BY distance ASC LIMIT :limit")
            params["limit"] = top_k
            
            results = db.execute(sql, params).fetchall()
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'file': row[0],
                    'content': row[1],
                    'metadata': row[2],
                    'score': 1 - row[3] # Converter distância em score de similaridade
                })
            return formatted_results
        finally:
            db.close()

# Instância global
rag_service = RagService()

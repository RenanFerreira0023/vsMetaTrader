from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import json
from config import settings

# Montar a URL de conexão do banco PostgreSQL
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Criar Engine e Session Local
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para criar as models
Base = declarative_base()

# --- Definição das Tabelas ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_uuid = Column(String(100), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(20), nullable=False) # 'user', 'assistant', 'system', 'tool'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")

class RobotTemplate(Base):
    __tablename__ = "robot_templates"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), nullable=False)
    language = Column(String(10), nullable=False) # 'MQL4' or 'MQL5'
    size_bytes = Column(Integer, nullable=False)
    indexed_at = Column(DateTime, default=datetime.utcnow)

class VectorChunk(Base):
    __tablename__ = "vector_chunks"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768)) # nomic-embed-text tem 768 dimensões
    metadata_json = Column(JSON, nullable=True) # type: OnInit, OnTick, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

# Index para busca vetorial (HNSW é geralmente mais rápido que IVFFlat para datasets médios)
# Nota: Requer que a extensão pgvector esteja instalada.
# Index('vector_chunks_embedding_idx', VectorChunk.embedding, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})

# Função para criar o banco de dados (tabelas)
def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

# Dependência do FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from database import init_db, engine, text
import logging

logging.basicConfig(level=logging.INFO)

try:
    print("Tentando inicializar o banco...")
    init_db()
    print("Banco inicializado com sucesso!")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result:
            print("Extensão 'vector' detectada!")
        else:
            print("Extensão 'vector' NÃO encontrada.")
except Exception as e:
    print(f"Erro: {e}")

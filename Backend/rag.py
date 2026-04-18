import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Any
from config import settings

import torch

class RagEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Mapear dispositivo: SentenceTransformer (PyTorch) espera 'cuda' para placas NVIDIA.
        # Aceitamos tanto 'gpu' quanto 'kompute' no settings.DEVICE.
        torch_device = "cuda" if settings.DEVICE in ["gpu", "kompute"] else settings.DEVICE
        
        # Verificar se CUDA está realmente disponível no PyTorch instalado
        if torch_device == "cuda" and not torch.cuda.is_available():
            print("⚠️ Aviso: GPU (CUDA) solicitada para o RAG, mas o PyTorch instalado não suporta CUDA.")
            print("💡 Para corrigir, execute: pip install torch --index-url https://download.pytorch.org/whl/cu121")
            torch_device = "cpu"
            
        self.model = SentenceTransformer(model_name, device=torch_device)
        self.index = None
        self.chunks: List[str] = []
        self.metadata: List[Dict[str, Any]] = []

    def index_robots(self, path: str):
        """Index all .mq4 and .mq5 files in the given path recursively."""
        self.chunks = []
        self.metadata = []
        embeddings = []

        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.mq4', '.mq5')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Simple chunking: split by double newlines (paragraphs)
                        raw_chunks = content.split('\n\n')
                        for i, chunk in enumerate(raw_chunks):
                            chunk = chunk.strip()
                            if chunk:
                                self.chunks.append(chunk)
                                self.metadata.append({
                                    'file': file_path,
                                    'chunk_id': i,
                                    'language': 'MQL4' if file.endswith('.mq4') else 'MQL5'
                                })
                                # Embed the chunk
                                embedding = self.model.encode(chunk)
                                embeddings.append(embedding)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

        if embeddings:
            embeddings = np.array(embeddings)
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
        else:
            self.index = None

    def search_context(self, query: str, top_k: int = 3) -> List[Tuple[str, Dict[str, Any]]]:
        """Search for the top_k most relevant chunks to the query."""
        if self.index is None or not self.chunks:
            return []

        query_embedding = self.model.encode(query).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                results.append((self.chunks[idx], self.metadata[idx]))

        return results

# Global instance
rag_engine = RagEngine()
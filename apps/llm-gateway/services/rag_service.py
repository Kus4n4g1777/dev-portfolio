"""
Production RAG Service - Polyglot Architecture
"""
import google.generativeai as genai
from typing import List, Dict, Optional
import os
import logging
import json
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        vector_db_url = os.getenv(
            "VECTOR_DB_URL",
            "postgresql://vector_user:B3Str0ng@vector_db:5432/vector_store"
        )
        
        self.engine = create_engine(vector_db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        self.embedding_model = "models/text-embedding-004"
        self.generation_model = "gemini-2.5-flash"
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        self._init_schema()
    
    def _init_schema(self):
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    metadata JSONB,
                    source VARCHAR(255),
                    chunk_index INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS rag_documents_embedding_idx 
                ON rag_documents 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_query_logs (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    response TEXT,
                    sources_used JSONB,
                    latency_ms FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            conn.commit()
            logger.info("✅ Vector DB schema initialized")
    
    def chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                for boundary in ['. ', '? ', '! ', '\n']:
                    last_boundary = text[start:end].rfind(boundary)
                    if last_boundary > self.chunk_size * 0.7:
                        end = start + last_boundary + len(boundary)
                        break
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
        
        return chunks
    
    async def create_embedding(self, text: str) -> List[float]:
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []
    
    async def add_document(self, content: str, source: str = "unknown", 
                          metadata: Optional[Dict] = None) -> Dict:
        chunks = self.chunk_text(content)
        total_chunks = len(chunks)
        
        session = self.SessionLocal()
        doc_ids = []
        
        try:
            for idx, chunk in enumerate(chunks):
                embedding = await self.create_embedding(chunk)
                
                if not embedding:
                    continue
                
                # FIX: Use raw SQL execution without type casting in params
                metadata_json = json.dumps(metadata or {})
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Execute raw SQL with proper escaping
                result = session.execute(
                    text("""
                        INSERT INTO rag_documents 
                        (content, embedding, metadata, source, chunk_index, total_chunks)
                        VALUES (:content, :embedding, :metadata, :source, :chunk_index, :total_chunks)
                        RETURNING id
                    """),
                    {
                        "content": chunk,
                        "embedding": embedding_str,
                        "metadata": metadata_json,
                        "source": source,
                        "chunk_index": idx,
                        "total_chunks": total_chunks
                    }
                )
                
                doc_id = result.fetchone()[0]
                doc_ids.append(doc_id)
            
            session.commit()
            
            return {
                "status": "success",
                "total_chunks": total_chunks,
                "doc_ids": doc_ids,
                "source": source
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding document: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            session.close()
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = await self.create_embedding(query)
        
        if not query_embedding:
            return []
        
        session = self.SessionLocal()
        
        try:
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            result = session.execute(
                text("""
                    SELECT id, content, metadata, source, chunk_index,
                           (embedding <-> :query_embedding) as distance
                    FROM rag_documents
                    ORDER BY embedding <-> :query_embedding
                    LIMIT :top_k
                """),
                {
                    "query_embedding": embedding_str,
                    "top_k": top_k
                }
            )
            
            documents = []
            for row in result:
                documents.append({
                    "id": row.id,
                    "content": row.content,
                    "metadata": row.metadata,
                    "source": row.source,
                    "chunk_index": row.chunk_index,
                    "similarity": 1 - float(row.distance)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        finally:
            session.close()
    
    async def generate_with_context(self, query: str, context_docs: List[Dict]) -> str:
        if not context_docs:
            return "No relevant information found in knowledge base."
        
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            context_parts.append(f"[Source {i}]: {doc['content']}\n")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Based on the following context, answer the question with citations.

Context:
{context}

Question: {query}

Answer (with [Source N] citations):"""
        
        try:
            model = genai.GenerativeModel(self.generation_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def ask(self, question: str, top_k: int = 5) -> Dict:
        import time
        start_time = time.time()
    
        similar_docs = await self.search_similar(question, top_k)
        answer = await self.generate_with_context(question, similar_docs)
    
        latency_ms = (time.time() - start_time) * 1000
    
        # LOG THE QUERY (NEW!)
        session = self.SessionLocal()
        try:
            query = text("""
                INSERT INTO rag_query_logs 
                (query, response, sources_used, latency_ms)
                VALUES (:query, :response, :sources, :latency)
            """)
        
            session.execute(query, {
                "query": question,
                "response": answer,
                "sources": json.dumps([{
                    'id': doc['id'],
                    'source': doc['source'],
                    'similarity': doc['similarity']
                } for doc in similar_docs]),
                "latency": latency_ms
            })
            session.commit()
        finally:
            session.close()
    
        return {
            "question": question,
            "answer": answer,
            "sources": similar_docs,
            "latency_ms": latency_ms,
            "database": "vector_db (polyglot)"
        }

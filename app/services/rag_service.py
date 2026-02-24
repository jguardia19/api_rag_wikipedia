import textwrap
from typing import List, Dict, Tuple

import chromadb
import wikipedia
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY, CHROMA_PATH

if not GEMINI_API_KEY:
    raise RuntimeError("Falta GEMINI_API_KEY en .env")

# Persistencia para que no se pierda al reiniciar
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
genai_client = genai.Client(api_key=GEMINI_API_KEY)


# Dividir el texto en chunks
def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)

# Generar Embeddings de los chunks
def embed_documents(docs: List[str]) -> List[List[float]]:
    resp = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=docs,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return [e.values for e in resp.embeddings]

# Embeddings de la consulta
def embed_query(query: str) -> List[float]:
    resp = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return resp.embeddings[0].values

# Generar respuesta
def generate_answer(question: str, context_docs: List[str]) -> str:
    context_str = "\n".join(context_docs)
    prompt = textwrap.dedent(f"""
    Contexto:
    {context_str}

    Pregunta: {question}

    Instrucciones:
    - Responde muy técnico y como especialista en el tema.
    - Usa SOLO la información del contexto.
    - Responde en español.
    """)
    resp = genai_client.models.generate_content(
        model="gemma-3-1b-it",
        contents=prompt
    )
    return resp.text

# Crear colección de ChromaDB con los chunks de un tema

def create_collection_for_topic(topic: str, collection_name: str, max_chunks: int, chunk_size: int, chunk_overlap: int) -> Dict:
    page = wikipedia.page(topic, auto_suggest=True)

    chunks = chunk_text(page.content, chunk_size, chunk_overlap)[:max_chunks]
    if not chunks:
        raise ValueError("No se generaron chunks")

    embeddings = embed_documents(chunks)

    collection = chroma_client.get_or_create_collection(collection_name)
    ids = [f"id_{i}" for i in range(len(chunks))]
    metadatas = [{"source": page.url, "title": page.title, "chunk": i}
                 for i in range(len(chunks))]

    collection.add(ids=ids, embeddings=embeddings,
                   documents=chunks, metadatas=metadatas)

    return {"source": page.url, "title": page.title, "chunks_indexed": len(chunks)}

# Recuperar los chunks más relevantes


def query_collection(collection_name: str, question: str, top_k: int) -> Tuple[List[str], List[dict]]:
    collection = chroma_client.get_or_create_collection(collection_name)

    q_emb = embed_query(question)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return docs, metas


def delete_collection(collection_name: str) -> None:
    chroma_client.delete_collection(collection_name)

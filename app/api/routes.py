from uuid import uuid4
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_service import (
    create_collection_for_topic,
    query_collection,
    generate_answer,
    delete_collection,
)

router = APIRouter()

# Demo: sesiones en memoria (para prueba Quasar)
sessions: Dict[str, Dict] = {}


class ResearchIn(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    max_chunks: int = Field(30, ge=5, le=200)
    chunk_size: int = Field(500, ge=200, le=2000)
    chunk_overlap: int = Field(100, ge=0, le=500)


class ResearchOut(BaseModel):
    session_id: str
    topic: str
    created_at: str
    collection_name: str
    source: str
    chunks_indexed: int


class AskIn(BaseModel):
    session_id: str
    question: str = Field(..., min_length=3, max_length=700)
    top_k: int = Field(4, ge=1, le=10)


class AskOut(BaseModel):
    answer: str
    sources: List[str]
    topic: str


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/research", response_model=ResearchOut)
def research(payload: ResearchIn):
    topic = payload.topic.strip()
    session_id = str(uuid4())
    collection_name = f"rag_{session_id}"
    created_at = datetime.utcnow().isoformat() + "Z"

    try:
        info = create_collection_for_topic(
            topic=topic,
            collection_name=collection_name,
            max_chunks=payload.max_chunks,
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    sessions[session_id] = {
        "topic": topic,
        "collection_name": collection_name,
        "created_at": created_at,
    }

    return ResearchOut(
        session_id=session_id,
        topic=topic,
        created_at=created_at,
        collection_name=collection_name,
        source=info["source"],
        chunks_indexed=info["chunks_indexed"],
    )


@router.post("/ask", response_model=AskOut)
def ask(payload: AskIn):
    session = sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session_id no existe o expiró")

    docs, metas = query_collection(session["collection_name"], payload.question, payload.top_k)
    if not docs:
        raise HTTPException(status_code=404, detail="No encontré contexto relevante")

    answer = generate_answer(payload.question, docs)
    sources = sorted({m.get("source") for m in metas if m and m.get("source")})

    return AskOut(answer=answer, sources=list(sources), topic=session["topic"])


@router.delete("/research/{session_id}", status_code=204)
def delete_research(session_id: str):
    session = sessions.get(session_id)
    if session:
        delete_collection(session["collection_name"])
        del sessions[session_id]
    return None
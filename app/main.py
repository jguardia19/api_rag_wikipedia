from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_ORIGINS
from app.api.routes import router

app = FastAPI(title="RAG API", version="1.0.0")

# CORS para Quasar
if ALLOWED_ORIGINS.strip() == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"ok": True, "message": "RAG API funcionando ✅"}
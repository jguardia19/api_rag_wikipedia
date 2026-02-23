# RAG API 🤖

API de **Retrieval-Augmented Generation (RAG)** construida con FastAPI que permite investigar cualquier tema consultando Wikipedia, indexar su contenido en una base de datos vectorial y responder preguntas de forma precisa usando Google Gemini.

---

## 🧠 ¿Cómo funciona?

```
Usuario → POST /research (tema)
              │
              ▼
        Wikipedia API  ──►  Fragmentación de texto (LangChain)
                                      │
                                      ▼
                            Embeddings (Gemini gemini-embedding-001)
                                      │
                                      ▼
                              ChromaDB (almacenamiento vectorial)
                                      │
                                      └──► session_id al usuario

Usuario → POST /ask (session_id + pregunta)
              │
              ▼
        Embedding de la consulta
              │
              ▼
        Búsqueda vectorial en ChromaDB (top-k chunks relevantes)
              │
              ▼
        Generación de respuesta (Gemma 3 1B via Gemini API)
              │
              └──► Respuesta + fuentes al usuario
```

---

## 🚀 Tecnologías

| Tecnología | Uso |
|---|---|
| **FastAPI** | Framework web / API REST |
| **ChromaDB** | Base de datos vectorial persistente |
| **Google Gemini API** | Embeddings (`gemini-embedding-001`) y generación de texto (`gemma-3-1b-it`) |
| **Wikipedia** | Fuente de datos para los temas de investigación |
| **LangChain Text Splitters** | Fragmentación inteligente de texto |
| **Pydantic** | Validación de datos |
| **Uvicorn** | Servidor ASGI |
| **python-dotenv** | Gestión de variables de entorno |

---

## 📁 Estructura del proyecto

```
rag_api/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación FastAPI
│   ├── api/
│   │   └── routes.py        # Definición de los endpoints de la API
│   ├── core/
│   │   └── config.py        # Configuración y variables de entorno
│   └── services/
│       └── rag_service.py   # Lógica principal del pipeline RAG
├── chroma_db/               # Almacenamiento persistente de ChromaDB
├── requirements.txt         # Dependencias del proyecto
└── .env                     # Variables de entorno (no incluido en el repo)
```

---

## ⚙️ Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd rag_api
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
GEMINI_API_KEY=tu_api_key_de_google_gemini
CHROMA_PATH=./chroma_db
ALLOWED_ORIGINS=*
```

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `GEMINI_API_KEY` | Clave de API de Google Gemini (**obligatoria**) | — |
| `CHROMA_PATH` | Ruta al almacenamiento de ChromaDB | `./chroma_db` |
| `ALLOWED_ORIGINS` | Orígenes permitidos para CORS (separados por coma o `*`) | `*` |

> Obtén tu API Key gratuita en [Google AI Studio](https://aistudio.google.com/app/apikey).

### 4. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`.

---

## 📡 Endpoints

### `GET /`
Comprueba que la API está en funcionamiento.

**Respuesta:**
```json
{ "ok": true, "message": "RAG API funcionando ✅" }
```

---

### `GET /health`
Health check del sistema.

**Respuesta:**
```json
{ "ok": true }
```

---

### `POST /research`
Crea una sesión de investigación sobre un tema. Descarga la página de Wikipedia, la fragmenta, genera embeddings y la indexa en ChromaDB.

**Body:**
```json
{
  "topic": "Inteligencia Artificial",
  "max_chunks": 30,
  "chunk_size": 500,
  "chunk_overlap": 100
}
```

| Campo | Tipo | Descripción | Rango |
|---|---|---|---|
| `topic` | `string` | Tema a investigar (título de Wikipedia) | 3–200 chars |
| `max_chunks` | `int` | Número máximo de fragmentos a indexar | 5–200 |
| `chunk_size` | `int` | Tamaño de cada fragmento en caracteres | 200–2000 |
| `chunk_overlap` | `int` | Solapamiento entre fragmentos | 0–500 |

**Respuesta:**
```json
{
  "session_id": "a1b2c3d4-...",
  "topic": "Inteligencia Artificial",
  "created_at": "2026-02-23T10:00:00Z",
  "collection_name": "rag_a1b2c3d4-...",
  "source": "https://es.wikipedia.org/wiki/Inteligencia_artificial",
  "chunks_indexed": 30
}
```

---

### `POST /ask`
Realiza una pregunta sobre el tema de una sesión activa. Recupera los fragmentos más relevantes y genera una respuesta con Gemini.

**Body:**
```json
{
  "session_id": "a1b2c3d4-...",
  "question": "¿Qué es el aprendizaje profundo?",
  "top_k": 4
}
```

| Campo | Tipo | Descripción | Rango |
|---|---|---|---|
| `session_id` | `string` | ID de la sesión creada con `/research` | — |
| `question` | `string` | Pregunta a responder | 3–700 chars |
| `top_k` | `int` | Número de fragmentos relevantes a recuperar | 1–10 |

**Respuesta:**
```json
{
  "answer": "El aprendizaje profundo es una subrama del aprendizaje automático...",
  "sources": ["https://es.wikipedia.org/wiki/Inteligencia_artificial"],
  "topic": "Inteligencia Artificial"
}
```

---

### `DELETE /research/{session_id}`
Elimina la sesión y su colección de ChromaDB.

**Respuesta:** `204 No Content`

---

## 📖 Documentación interactiva

FastAPI genera automáticamente una interfaz interactiva para explorar y probar la API:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💡 Ejemplo de uso completo

```bash
# 1. Crear sesión de investigación
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Machine learning", "max_chunks": 20}'

# 2. Hacer una pregunta con el session_id obtenido
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_id>", "question": "¿Qué es el aprendizaje supervisado?", "top_k": 4}'

# 3. Eliminar la sesión al terminar
curl -X DELETE http://localhost:8000/research/<session_id>
```

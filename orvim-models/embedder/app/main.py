from fastapi import FastAPI
from typing import List
from sentence_transformers import SentenceTransformer
import os, uvicorn
import logging
import transformers

app = FastAPI()
logging.error("IMPORT APP")
# Load the embedding model

transformers.utils.logging.set_verbosity_error()
# EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING", "sergeyzh/LaBSE-ru-turbo")
EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING", "deepvk/USER-bge-m3")
if EMBEDDING_MODEL not in ("sergeyzh/LaBSE-ru-turbo", "deepvk/USER-bge-m3"):
    raise ValueError(f"Model {EMBEDDING_MODEL} doesn't supported")

embedder = SentenceTransformer(EMBEDDING_MODEL)
device = os.getenv("DEVICE", 'cpu')
embedder.to(device)
logging.error("MODEL INITIALIZED")


@app.post("/embed/")
async def create_embeddings(texts: List[str]):
    if not texts:
        return {"error": "No texts provided"}
    embeddings = embedder.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    embeddings_list = embeddings.tolist()
    return embeddings_list

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        reload=True,
        log_level="debug",
    )

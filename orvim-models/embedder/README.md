# Text Embedding Microservice

## Overview

This is a FastAPI microservice that generates embeddings for input texts using the SentenceTransformer model.

## Usage

### Run the Service

```bash
docker build -t text-embedding-service .
docker run -p 8000:80 text-embedding-service
```
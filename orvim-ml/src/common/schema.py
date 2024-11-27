from pydantic import BaseModel
from enum import Enum

class ConnectionNotion(BaseModel):
    url: str
    api_key: str
    user_space: str

class ConnectionUrl(BaseModel):
    url: str
    search_depth: int

class ConnectionS3(BaseModel):
    s3_paths: list[str]

class ConnectTask(BaseModel):
    id: str
    type: str
    data: ConnectionNotion | ConnectionUrl | ConnectionS3
    run: list[int]
    all_data:str



class TransformPdfParser(BaseModel):
    max_symbols: int

class TransformOCR(BaseModel):
    endpoint_url: str
    headers: str
    max_symbols: int


class TransformASR(BaseModel):
    endpoint_url: str
    headers: str
    max_symbols: int


class TransformTextParser(BaseModel):
    max_symbols: int


class TransformClip(BaseModel):
    endpoint_url: str
    headers: str
    max_symbols: int


class TransformTask(BaseModel):
    id: str
    type: str
    data: ConnectionNotion | ConnectionUrl | ConnectionS3
    all_data:str


class RagModel(BaseModel):
    promt: str
    llm_name: str
    embeddings: str
    embedding_kwargs: str
    llm_kwargs: str


d = {
    TransformTextParser: ["","txt","md"],
    TransformClip: ["png", "jpg"],
    
    }

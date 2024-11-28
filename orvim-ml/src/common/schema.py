from pydantic import BaseModel
from .workflow import EnumConnectionType, RagChunker, RagEmbedder, RagLLMQa

class Transform(BaseModel):
    type: str
    data: dict

class ConnectTask(BaseModel):
    flow_id: int
    type: EnumConnectionType
    data: dict
    transforms: list[Transform]
    embedder: RagEmbedder
    chunker: RagChunker
    llmqa: RagLLMQa


class Document(BaseModel):
    type: str = ""
    data: str
    source: str


class TransformTask(BaseModel):
    flow_id: int
    connector_id: int
    document: Document
    type: str
    data: dict
    embedder: RagEmbedder
    chunker: RagChunker
    llmqa: RagLLMQa



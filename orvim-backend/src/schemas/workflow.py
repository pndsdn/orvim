from pydantic import BaseModel, model_validator, field_validator
from typing import List, Optional
from enum import StrEnum


class EnumWorkflowStatus(StrEnum):
    completed = "completed"
    in_progress = "in_progress"
    error = "error"


class EnumConnectionType(StrEnum):
    notion = "notion"
    confluence = "confluence"
    db = "db"
    url = "url"
    s3 = "s3"


class EnumConnectionDBTypes(StrEnum):
    postgres = "postgres"
    mysql = "mysql"
    sqlite = "sqlite"


class EnumTransformType(StrEnum):
    pdf_parser = "pdf_parser"
    ocr = "ocr"
    asr = "asr"
    txt_parser = "txt_parser"
    clip = "clip"
    clap = "clap"


class ConnectionNotion(BaseModel):
    url: str
    api_key: str
    user_space: str


class ConnectionConfluence(BaseModel):
    url: str
    api_token: str
    email: str


class ConnectionDB(BaseModel):
    db_port: int
    db_username: str
    db_password: str
    db_type: EnumConnectionDBTypes
    db_address: str
    db_name: str
    sql_query: str


class ConnectionUrl(BaseModel):
    url: str
    search_depth: int


class ConnectionS3(BaseModel):
    s3_path: List[str]


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


class TransformClap(BaseModel):
    # НЕ ИСПОЛЬЗУЕТСЯ
    example: int


class RagModel(BaseModel):
    promt: str
    llm_name: str
    embeddings: str
    embedding_kwargs: str
    llm_kwargs: str


class RagChunker(BaseModel):
    chunk_size: int
    chunk_overlap: int


class RagEmbedder(BaseModel):
    url: str
    modal_name: str
    headers: str


class RagLLMQa(BaseModel):
    url: str
    modal_name: str
    api_token: str
    headers: str
    rag_n: str
    use_additional_instruction: bool
    additional_instruction: str
    prompt_template: str


class WorkflowGraphSettings(BaseModel):
    id: str
    type: str
    label: str
    connections: List[str]
    data: dict

    @model_validator(mode="after")
    def validate_data(self, model):
        label = self.label
        node_type = self.type
        data = self.data

        # Define the validation logic
        if label == "notion" and node_type == "connection":
            validated_data = ConnectionNotion(**data)
        elif label == "confluence" and node_type == "connection":
            validated_data = ConnectionConfluence(**data)
        elif label == "db" and node_type == "connection":
            validated_data = ConnectionDB(**data)
        elif label == "url" and node_type == "connection":
            validated_data = ConnectionUrl(**data)
        elif label == "s3" and node_type == "connection":
            validated_data = ConnectionS3(**data)
        elif label == "pdf_parser" and node_type == "transform":
            validated_data = TransformPdfParser(**data)
        elif label == "ocr" and node_type == "transform":
            validated_data = TransformOCR(**data)
        elif label == "asr" and node_type == "transform":
            validated_data = TransformASR(**data)
        elif label == "txt_parser" and node_type == "transform":
            validated_data = TransformTextParser(**data)
        elif label == "clip" and node_type == "transform":
            validated_data = TransformClip(**data)
        elif label == "clap" and node_type == "transform":
            pass
        elif label == "chunker" and node_type == "rag":
            validated_data = RagChunker(**data)
        elif label == "embedder" and node_type == "rag":
            validated_data = RagEmbedder(**data)
        elif label == "llm_qa" and node_type == "rag":
            validated_data = RagLLMQa(**data)
        else:
            raise ValueError(f"Unsupported combination of label: {label} and type: {node_type}")

        return self


class StyleSettings(BaseModel):
    title: str
    theme_colour: str
    icon_url: str
    style_css: str


class HostSettings(BaseModel):
    domens: List[str]
    ipaddress: List[str]


class GetAllMyWorkflows(BaseModel):
    id: int
    name: str
    status: EnumWorkflowStatus
    style_settings: StyleSettings
    host_permissions: HostSettings


class UpdateWorkflowAgent(BaseModel):
    style_settings: Optional[StyleSettings]
    host_permissions: Optional[HostSettings]



from pydantic import BaseModel

class TransformTask(BaseModel):
    type: str
    data: dict


class ConnectTask(BaseModel):
    flow_id: int
    type: str
    data: dict
    transforms: list[TransformTask]
    rag_data: str

class Document(BaseModel):
    type: str = ""
    data: str

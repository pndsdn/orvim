from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    s3_path: str

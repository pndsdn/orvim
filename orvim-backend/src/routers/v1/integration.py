from fastapi import APIRouter, Depends, UploadFile
from uuid import uuid4
from models.user import User
from core.db import get_database, Session
from core.auth import get_user
from schemas.integration import FileUploadResponse
from core.s3 import s3_connection

import core.errors as errors
import logging

router = APIRouter()


@router.post("/file/upload",
             response_model=FileUploadResponse,
             responses=errors.with_errors())
async def upload_data_connection(file: UploadFile,
                                 workspace_id: int = 0,
                                 user: User = Depends(get_user),
                                 db: Session = Depends(get_database)) -> FileUploadResponse:
    s3_path = f"connection/{user.id}/{str(uuid4())}_{file.filename}"
    s3_connection.upload_file(file.file.read(), s3_path)
    return FileUploadResponse(s3_path=s3_connection.get_url(s3_path))

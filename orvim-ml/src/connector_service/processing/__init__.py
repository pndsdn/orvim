import logging
from common.workflow import (
    EnumConnectionType,
    ConnectionS3,
    TransformTextParser,
    TransformClip,
)
from common.schema import ConnectTask
from common.models import ConnectionLog
from .process_s3 import process_s3
from common.schema import Document
from pydantic import ValidationError

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

type2connector = {EnumConnectionType.s3: (ConnectionS3, process_s3)}


def process(connector:ConnectTask) -> tuple[list[Document], str]:
    model_v, func_process = type2connector.get(connector.type, (None, None))
    error = ""
    if func_process is None:
        error = error = f"Can't process connector type={connector.type}"
    else:
        try:
            data = model_v.model_validate(connector.data)
            return func_process(data)
        except ValidationError:
            error = "Can't parse connector data"
    return [], error


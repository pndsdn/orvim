import logging
from common.workflow import (
    EnumTransformType,
    TransformTextParser,
    TransformClip,
)
from common.schema import TransformTask
from .process_txt import process_txt
from pydantic import ValidationError

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

type2transform = {EnumTransformType.txt_parser: (TransformTextParser, process_txt)}


def process(transform: TransformTask) -> str:
    model_v, func_process = type2transform.get(transform.type, (None, None))
    error = ""
    if func_process is None:
        error = f"Can't process transform type={transform.type}"
    else:
        try:
            data = model_v.model_validate(transform.data)
            return func_process(transform.document, data,  transform.chunker, transform.embedder, transform.llmqa)
        except ValidationError:
            error = "Can't parse transform data"
    return [], error


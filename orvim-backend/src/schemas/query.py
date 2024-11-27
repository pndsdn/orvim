from typing import List
from pydantic import BaseModel


class BaseQueryResponse(BaseModel):
    answer: str
    full_promt: str
    source_links: List[str]

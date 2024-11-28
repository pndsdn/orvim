from fastapi import APIRouter, Depends
from core.db import get_database, Session
from services.rag import generate_response
from crud.workflow import get_unsafe_workflow_by_id
from schemas.query import BaseQueryResponse
import core.errors as errors


router = APIRouter()


@router.get("/workflow/{workflow_id}",
            response_model=BaseQueryResponse,
            responses=errors.with_errors(errors.workflow_not_found()))
async def get_query_response(query: str,
                             workflow_id: int,
                             db: Session = Depends(get_database)) -> BaseQueryResponse:
    workflow = get_unsafe_workflow_by_id(workflow_id,
                                         db)
    if workflow is None:
        raise errors.workflow_not_found()

    result = generate_response(question=query,
                               prompt_template=workflow.promt_template,
                               llm_name=workflow.rags_data["llm_name"],
                               llm_kwargs=workflow.rags_data["llm_kwargs"],
                               n_results=5,
                               db_id=workflow_id,
                               model_name=workflow.rags_data["embeddings"])
    # Да, формат ответа изменится, тогда я и обновлю все
    return BaseQueryResponse(answer=result[0],
                             full_promt=result[1],
                             source_links=result[2])

from fastapi import APIRouter, Depends
from typing import List
from core.db import get_database, Session
from core.auth import get_user
from models.user import User
from schemas.workflow import (WorkflowGraphSettings, GetAllMyWorkflows, UpdateWorkflowAgent,
                              StyleSettings, HostSettings)
import core.errors as errors
from crud.workflow import (get_all_my_workflows, get_workflow_by_id, update_workflow_by_id,
                           create_workflow, update_workflow_agent, update_workflow_name_by_object,
                           delete_workflow_by_object, clear_workflow_logs)

router = APIRouter()


@router.get("/settings",
            response_model=List[WorkflowGraphSettings],
            responses=errors.with_errors(errors.workflow_not_found()))
async def get_workflow_settings(workflow_id: int,
                                user: User = Depends(get_user),
                                db: Session = Depends(get_database)) -> List[WorkflowGraphSettings]:
    workflow = get_workflow_by_id(workflow_id,
                                  user.id,
                                  db)
    if workflow is None:
        raise errors.workflow_not_found()
    all_nodes = []
    all_nodes.extend(workflow.connectors_data)
    all_nodes.extend(workflow.transformers_data)
    all_nodes.extend([workflow.chunker_data, workflow.embedder_data, workflow.llmqa_data])
    return [WorkflowGraphSettings(id=node["id"],
                                  type=node["type"],
                                  label=node["label"],
                                  connections=node["connections"],
                                  data=node["data"]) for node in all_nodes]


@router.post("/settings",
             status_code=201,
             responses=errors.with_errors())
async def create_workflow_settings(workflow_settings: List[WorkflowGraphSettings],
                                   workflow_name: str = "База знаний",
                                   user: User = Depends(get_user),
                                   db: Session = Depends(get_database)) -> None:
    create_workflow(workflow_name=workflow_name,
                    workspace_id=user.id,
                    node_list=workflow_settings,
                    db=db)


@router.put("/settings",
            status_code=204,
            responses=errors.with_errors(errors.workflow_not_found()))
async def update_workflow_settings(workflow_id: int,
                                   workflow_settings: List[WorkflowGraphSettings],
                                   user: User = Depends(get_user),
                                   db: Session = Depends(get_database)):
    workflow = get_workflow_by_id(workflow_id,
                                  user.id,
                                  db)
    if workflow is None:
        raise errors.workflow_not_found()
    clear_workflow_logs(workflow_id=workflow_id,
                        db=db)
    update_workflow_by_id(workflow_id=workflow_id,
                          node_list=workflow_settings,
                          db=db)


@router.patch("/name",
              status_code=204,
              responses=errors.with_errors())
async def update_workflow_name(workflow_id: int,
                               name: str,
                               user: User = Depends(get_user),
                               db: Session = Depends(get_database)):
    workflow = get_workflow_by_id(workflow_id,
                                  user.id,
                                  db)
    if workflow is None:
        raise errors.workflow_not_found()
    update_workflow_name_by_object(name,
                                   workflow,
                                   db)


@router.put("/agent/settings",
            status_code=204,
            responses=errors.with_errors(errors.workflow_not_found()))
async def set_workflow_agent_settings(workflow_id: int,
                                      update_params: UpdateWorkflowAgent,
                                      user: User = Depends(get_user),
                                      db: Session = Depends(get_database)):
    workflow = get_workflow_by_id(workflow_id,
                                  user.id,
                                  db)
    if workflow is None:
        raise errors.workflow_not_found()
    update_workflow_agent(workflow,
                          update_params.style_settings,
                          update_params.host_permissions,
                          db)


@router.get("/all",
            response_model=List[GetAllMyWorkflows],
            responses=errors.with_errors())
async def get_all_workspace_workflows(user: User = Depends(get_user),
                                      db: Session = Depends(get_database)) -> List[GetAllMyWorkflows]:
    workflows = get_all_my_workflows(user.id,
                                     db)
    return [GetAllMyWorkflows(id=workflow.id,
                              name=workflow.name,
                              status=workflow.status,
                              style_settings=StyleSettings(**workflow.style_settings),
                              host_permissions=HostSettings(**workflow.host_permissions)) for workflow in workflows]


@router.delete("/settings",
               status_code=204,
               responses=errors.with_errors())
async def delete_workflow(workflow_id: int,
                          user: User = Depends(get_user),
                          db: Session = Depends(get_database)):
    workflow = get_workflow_by_id(workflow_id,
                                  user.id,
                                  db)
    if workflow is None:
        raise errors.workflow_not_found()
    delete_workflow_by_object(workflow,
                              db)

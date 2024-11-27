from sqlalchemy.orm import undefer_group
from core.db import Session
from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from models.user import User, UserInfo
from models.workflow import Workflow
from schemas.workflow import WorkflowGraphSettings


def get_all_my_workflows(workspace_id: int,
                         db: Session) -> List[Workflow]:
    workflows = db.query(Workflow).filter(Workflow.workspace_id == workspace_id).all()
    return workflows


def get_workflow_by_id(workflow_id: int,
                       workspace_id: int,
                       db: Session) -> Workflow | None:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id,
                                         Workflow.workspace_id == workspace_id).first()
    return workflow


def get_unsafe_workflow_by_id(workflow_id: int,
                              db: Session) -> Workflow | None:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    return workflow


def update_workflow_by_id(workflow_id: int,
                          db: Session) -> None:
    pass


def create_workflow(workflow_name: str,
                    workspace_id: int,
                    node_list: List[WorkflowGraphSettings],
                    db: Session) -> None:
    workflow = Workflow(name=workflow_name,
                        workspace_id=workspace_id)

    connectors_data, transformers_data, rags_data = [], [], {}
    for node in node_list:
        if node["type"] == "connection":
            connectors_data.append({"id": node.id,
                                    "type": node.type,
                                    "label": node.label,
                                    "connections": node.connections,
                                    "data": node.data})
        elif node["type"] == "transform":
            transformers_data.append({"id": node.id,
                                      "type": node.type,
                                      "label": node.label,
                                      "connections": node.connections,
                                      "data": node.data})
        else:
            workflow.promt_template = node.data["promt"]
            rags_data = {"id": node.id,
                         "type": node.type,
                         "label": node.label,
                         "connections": node.connections,
                         "data": node.data}

    workflow.connectors_data = connectors_data
    workflow.transformers_data = transformers_data
    workflow.rags_data = rags_data

    db.add(workflow)
    db.commit()


def update_workflow_agent(workflow: Workflow,
                          style_settings: str | None,
                          host_permissions: List[str] | None,
                          db: Session) -> None:
    if host_permissions is not None:
        workflow.host_permissions = host_permissions
    if style_settings is not None:
        workflow.style_settings = style_settings
    db.commit()


def update_workflow_name_by_object(new_name: str,
                                   workflow: Workflow,
                                   db: Session):
    workflow.name = new_name
    db.commit()


def delete_workflow_by_object(workflow: Workflow,
                              db: Session) -> None:
    db.delete(workflow)
    db.commit()

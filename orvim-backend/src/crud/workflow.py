from core.db import Session
from sqlalchemy import select, or_, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from models.user import User, UserInfo
from models.workflow import Workflow, ConnectionLog
from schemas.workflow import (WorkflowGraphSettings, UpdateWorkflowAgent, HostSettings, StyleSettings,
                              RagEmbedder, RagChunker, RagLLMQa, EnumConnectionType)

from pydantic import BaseModel


class Transform(BaseModel):
    type: str
    data: dict


class ConnectTask(BaseModel):
    flow_id: int
    type: EnumConnectionType
    data: dict
    transforms: list[Transform]
    embedder: RagEmbedder
    chunker: RagChunker
    llmqa: RagLLMQa


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
                          node_list: List[WorkflowGraphSettings],
                          db: Session) -> List[Any]:
    analytics_data = []
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    connectors_data, transformers_data = [], []
    embedder, chunker, llmqa = {}, {}, {}
    for node in node_list:
        if node.type == "connection":
            connectors_data.append({"id": node.id,
                                    "type": node.type,
                                    "label": node.label,
                                    "connections": node.connections,
                                    "data": node.data})
            analytics_data.append({"flow_id": workflow_id,
                                   "type": node.label,
                                   "data": node.data,
                                   "transforms": node.connections})
        elif node.type == "transform":
            transformers_data.append({"id": node.id,
                                      "type": node.type,
                                      "label": node.label,
                                      "connections": node.connections,
                                      "data": node.data})
        elif node.type == "rag" and node.label == "llm_qa":
            workflow.promt_template = node.data["promt_template"]
            llmqa = {"id": node.id,
                     "type": node.type,
                     "label": node.label,
                     "connections": node.connections,
                     "data": node.data}
        elif node.type == "rag" and node.label == "embedder":
            chunker = {"id": node.id,
                       "type": node.type,
                       "label": node.label,
                       "connections": node.connections,
                       "data": node.data}
        elif node.type == "rag" and node.label == "chunker":
            embedder = {"id": node.id,
                        "type": node.type,
                        "label": node.label,
                        "connections": node.connections,
                        "data": node.data}

    workflow.connectors_data = connectors_data
    workflow.transformers_data = transformers_data
    workflow.embedder_data = embedder
    workflow.chunker_data = chunker
    workflow.llmqa_data = llmqa

    for node in analytics_data:
        node["embedder"] = embedder
        node["chunker"] = chunker
        node["llmqa"] = llmqa
        update_transform = []
        for transform_id in node["transforms"]:
            requested_transform = None
            for transform in transformers_data:
                if transform["id"] == transform_id:
                    requested_transform = transform
                    break
            update_transform.append({"type": requested_transform["label"],
                                     "data": requested_transform["data"]})

    db.commit()

    return analytics_data


def create_workflow(workflow_name: str,
                    workspace_id: int,
                    node_list: List[WorkflowGraphSettings],
                    db: Session) -> List[Any]:
    analytics_data = []
    # счетчик для уникального названия
    counter = db.query(Workflow).filter(Workflow.workspace_id == workspace_id).count()
    workflow = Workflow(name=workflow_name + " " + str(counter),
                        workspace_id=workspace_id)

    connectors_data, transformers_data = [], []
    embedder, chunker, llmqa = {}, {}, {}
    for node in node_list:
        if node.type == "connection":
            connectors_data.append({"id": node.id,
                                    "type": node.type,
                                    "label": node.label,
                                    "connections": node.connections,
                                    "data": node.data})
            # Добавление записи в список для анализа
            analytics_data.append({"flow_id": 0,
                                   "type": node.label,
                                   "data": node.data,
                                   "transforms": node.connections})
        elif node.type == "transform":
            transformers_data.append({"id": node.id,
                                      "type": node.type,
                                      "label": node.label,
                                      "connections": node.connections,
                                      "data": node.data})
        elif node.type == "rag" and node.label == "llm_qa":
            workflow.promt_template = node.data["prompt_template"]
            llmqa = {"id": node.id,
                     "type": node.type,
                     "label": node.label,
                     "connections": node.connections,
                     "data": node.data}
        elif node.type == "rag" and node.label == "embedder":
            chunker = {"id": node.id,
                       "type": node.type,
                       "label": node.label,
                       "connections": node.connections,
                       "data": node.data}
        elif node.type == "rag" and node.label == "chunker":
            embedder = {"id": node.id,
                        "type": node.type,
                        "label": node.label,
                        "connections": node.connections,
                        "data": node.data}

    workflow.connectors_data = connectors_data
    workflow.transformers_data = transformers_data
    workflow.embedder_data = embedder
    workflow.chunker_data = chunker
    workflow.llmqa_data = llmqa
    workflow.host_permissions = {"domens": [],
                                 "ipaddress": []}
    workflow.style_settings = {"title": "",
                               "theme_colour": "",
                               "icon_url": "",
                               "style_css": ""}
    db.add(workflow)
    db.commit()

    for node in analytics_data:
        node["flow_id"] = workflow.id
        node["embedder"] = embedder
        node["chunker"] = chunker
        node["llmqa"] = llmqa
        update_transform = []
        for transform_id in node["transforms"]:
            requested_transform = None
            for transform in transformers_data:
                if transform["id"] == transform_id:
                    requested_transform = transform
                    break
            update_transform.append({"type": requested_transform["label"],
                                     "data": requested_transform["data"]})
    return analytics_data


def update_workflow_agent(workflow: Workflow,
                          style_settings: StyleSettings | None,
                          host_permissions: HostSettings | None,
                          db: Session) -> None:
    if host_permissions is not None:
        workflow.host_permissions = {"domens": host_permissions.domens,
                                     "ipaddress": host_permissions.ipaddress}

    if style_settings is not None:
        workflow.style_settings = {"title": style_settings.title,
                                   "theme_colour": style_settings.theme_colour,
                                   "icon_url": style_settings.icon_url,
                                   "style_css": style_settings.style_css}
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


def clear_workflow_logs(workflow_id: int,
                        db: Session) -> None:
    stmt = delete(ConnectionLog).where(workflow_id == workflow_id)
    db.execute(stmt)

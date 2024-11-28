from sqlalchemy import String, ForeignKey, Boolean, func, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TEXT
from typing import List, Dict, Any

from models.base import Base, apply_workflow_status
from schemas.workflow import EnumWorkflowStatus


class Workflow(Base):
    __tablename__ = "workflow"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, server_default="База знаний")
    promt_template: Mapped[str] = mapped_column(nullable=True)
    workspace_id: Mapped[int] = mapped_column(index=True)
    connectors_data: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB,
                                                                  server_default="{}")
    transformers_data: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB,
                                                                    server_default="{}")
    embedder_data: Mapped[Dict[Any, Any]] = mapped_column(JSONB, server_default="{}")
    chunker_data: Mapped[Dict[Any, Any]] = mapped_column(JSONB, server_default="{}")
    llmqa_data: Mapped[Dict[Any, Any]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[EnumWorkflowStatus] = mapped_column(apply_workflow_status,
                                                       server_default=EnumWorkflowStatus.in_progress)
    style_settings: Mapped[Dict[Any, Any]] = mapped_column(JSONB, server_default="{}")
    host_permissions: Mapped[Dict[Any, Any]] = mapped_column(JSONB, nullable=True,
                                                             server_default="{}")
    connection_all: Mapped[int] = mapped_column(server_default="0")


class ConnectionLog(Base):
    __tablename__ = "connection_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id",
                                                        ondelete="CASCADE"))
    transform_all: Mapped[int] = mapped_column(server_default="0")
    connection_success: Mapped[bool] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(nullable=True)


class TransformLog(Base):
    __tablename__ = "transform_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("connection_log.id",
                                                          ondelete="CASCADE"))
    transform_success: Mapped[bool] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(nullable=True)

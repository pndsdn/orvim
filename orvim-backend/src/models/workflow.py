from sqlalchemy import String, TIMESTAMP, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TEXT
from datetime import datetime
from typing import List, Dict, Any

from models.base import Base, apply_workflow_status
from schemas.workflow import EnumWorkflowStatus


class Workflow(Base):
    __tablename__ = "workflow_settings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, server_default="База знаний")
    promt_template: Mapped[str] = mapped_column(nullable=True)
    workspace_id: Mapped[int] = mapped_column(primary_key=True)  # Он же user_id
    connectors_data: Mapped[List[Dict[Any, Any]]] = mapped_column(ARRAY(JSONB, dimensions=1),
                                                                  server_default="{}")
    transformers_data: Mapped[List[Dict[Any, Any]]] = mapped_column(ARRAY(JSONB, dimensions=1),
                                                                    server_default="{}")
    rags_data: Mapped[Dict[Any, Any]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[EnumWorkflowStatus] = mapped_column(apply_workflow_status,
                                                       server_default=EnumWorkflowStatus.in_progress)
    style_settings: Mapped[str] = mapped_column(nullable=False, server_default="")
    host_permissions: Mapped[List[str]] = mapped_column(ARRAY(String, dimensions=1), nullable=True,
                                                        server_default="{}")

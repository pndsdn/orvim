from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import declarative_base

Base = declarative_base()

apply_workflow_status = ENUM("complete", "in_progress", "error",
                             name="apply_workflow_status",
                             metadata=Base.metadata)

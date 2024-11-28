from sqlalchemy.orm import Session
from sqlalchemy import text

from common.workflow import EnumWorkflowStatus
from common.models import Workflow


def try_finish_workflow(workflow_id: int,
                        db: Session) -> None:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if workflow is None:
        return
    stmt = """SELECT 
                  SUM(CASE WHEN connection_log.connection_success = True THEN 1 ELSE 0 END),
                  SUM(CASE WHEN connection_log.connection_success = FALSE THEN 1 ELSE 0 END)
              FROM connection_log 
              WHERE workflow_id = :workflow_id_1;"""

    res = db.execute(text(stmt), {"workflow_id_1": workflow_id})
    successful_connections, failed_connections = res.fetchall()[0]
    if workflow.connection_all == successful_connections:
        workflow.status = EnumWorkflowStatus.completed
    if failed_connections != 0:
        workflow.status = EnumWorkflowStatus.error
    db.commit()


def try_finish_connection(connection_id: int,
                          db: Session) -> None:
    connection = db.query(Workflow).filter(Workflow.id == connection_id).first()
    if connection is None:
        return
    stmt = """SELECT 
                  SUM(CASE WHEN transform_log.transform_success = True THEN 1 ELSE 0 END),
                  SUM(CASE WHEN transform_log.transform_success = FALSE THEN 1 ELSE 0 END)
              FROM transform_log 
              WHERE connection_id = :connection_id_1;"""

    res = db.execute(text(stmt), {"connection_id_1": connection_id})
    successful_transforms, failed_transforms = res.fetchall()[0]
    if connection.transform_all == successful_transforms:
        connection.connection_success = True
    if failed_transforms != 0:
        connection.connection_success = False
    db.commit()
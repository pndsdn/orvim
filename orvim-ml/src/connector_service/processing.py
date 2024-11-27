from common.db_session import Session


def process_s3_connector(data: str, db: Session, rabbit:str):
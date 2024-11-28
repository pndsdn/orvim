import time

import aio_pika
import asyncio
import logging

from common.settings import settings
from common.schema import ConnectTask, TransformTask
from common.db_session import with_database
from common.models import TransformLog
from processing import process
from common.finish import try_finish_connection, try_finish_workflow


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


async def main(loop):
    connection = await aio_pika.connect_robust(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASS,
        loop=loop,
    )

    async with connection:
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue_read: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            "transform", durable=True
        )
        async with queue_read.iterator() as queue_iter:
            logger.info("Start listening for messages")
            async for message in queue_iter:  # async with message.process():
                with with_database() as db:
                    logger.info("Process new TransformTask")
                    error = ""
                    try:
                        transform = TransformTask.model_validate_json(
                            message.body.decode()
                        )
                        logger.info(f"{transform=}")
                        error = process(transform)
                    except ValueError as e:
                        error = f"Cant parse ConnectorTask with error: {e}"
                    if error:
                        logger.error(error)
                        log = TransformLog(
                            connection_id=transform.connector_id,
                            connection_success=False,
                            error_message=error,
                        )
                    else:
                        log = TransformLog(
                            connection_id=transform.connector_id,
                            connection_success=True,
                        )
                    db.add(log)
                    db.commit()
                    try_finish_connection(transform.connector_id, db)
                    try_finish_workflow(transform.flow_id, db)
                    await message.ack()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()

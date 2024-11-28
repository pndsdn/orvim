import time

import aio_pika
import asyncio
import logging

from common.settings import settings
from common.schema import ConnectTask, ConnectionS3, ConnectionNotion, ConnectionUrl
from common.db_session import with_database
from common.models import ConnectionLog
from connector_service.mapper import type2connector

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
            "connect", durable=True
        )
        # exchange_write = await channel.declare_exchange("transform", type=aio_pika.exchange.ExchangeType.FANOUT)

        async with queue_read.iterator() as queue_iter:
            logger.info("Start listening for messages")
            async for message in queue_iter:  # async with message.process():
                with with_database() as db:
                    logger.info("Process new ConnectTask")
                    error = None
                    transforms = 0
                    try:
                        connector = ConnectTask.model_validate_json(
                            message.body.decode()
                        )
                        logger.info(f"{connector=}")
                        data = type2connector.get(connector.type)
                        if data is None:
                            error = "Can't process connector_type={}"
                        else:

                            pass

                        # exchange_write.publish(
                        #     aio_pika.Message(
                        #         body=TransformTextParser(id=upload_id, **paths).model_dump_json().encode(),
                        #         content_type="application/json",
                        #         content_encoding="utf-8",
                        #         delivery_mode=DeliveryMode.PERSISTENT,
                        #     ),
                        #     "",
                        # )
                        if error is not None:
                            logger.error(error)
                            log = ConnectionLog(
                                workflow_id=connector.flow_id,
                                transform_all=0,
                                connection_success=True,
                                error_message=error,
                            )
                        else:
                            log = ConnectionLog(
                                workflow_id=connector.flow_id,
                                transform_all=transforms,
                                connection_success=not bool(transforms),
                            )
                        db.add(log)
                        db.commit()
                    except ValueError as e:
                        logger.error(f"Cant parse ConnectorTask with error: {e}")
                    await message.ack()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()

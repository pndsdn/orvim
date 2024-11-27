import time

import aio_pika
import asyncio
import logging

from common.settings import settings
from common.schema import ConnectTask, ConnectionS3, ConnectionNotion, ConnectionUrl
from common.db_session import with_database

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main(loop):
    connection = await aio_pika.connect_robust(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASS,
        loop=loop
    )

    async with connection:
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue_read: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            "connect",
            durable=True
        )
        exchange_write = await channel.declare_exchange("transform", type=aio_pika.exchange.ExchangeType.FANOUT)

        async with queue_read.iterator() as queue_iter:
            async for message in queue_iter:# async with message.process():
                with with_database(connection) as db:
                    logger.info("Process new ConnectTask")
                    try:
                        start_time_metric = time.time()
                        connector = ConnectTask.model_validate_json(message.body.decode())
                        print(connector)
                        exchange_write.publish(
                            aio_pika.Message(
                                body=TransformTextParser(id=upload_id, **paths).model_dump_json().encode(),
                                content_type="application/json",
                                content_encoding="utf-8",
                                delivery_mode=DeliveryMode.PERSISTENT,
                            ),
                            "",
                        )
                        await message.ack()
                        logger.info(f"Duration: {time.time() - start_time_metric}")
                    except ValueError:
                        pass



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()

import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI
from settings import settings
from routers import router
from core.db import create_tables as create_postgres_tables
from core.db import create_initial_user
from core.rabbitmq import rabbit_connection

@asynccontextmanager
async def lifespan(application: FastAPI):
    create_postgres_tables()
    create_initial_user()
    await rabbit_connection.connect()
    yield
    await rabbit_connection.close()

app = FastAPI(debug=settings.SERVER_TEST,
              lifespan=lifespan)
app.include_router(router)

app.add_middleware(
    GZipMiddleware,
    minimum_size=2000
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_ADDR,
        workers=settings.SERVER_WORKERS,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_TEST,
        log_level="debug" if settings.SERVER_TEST else "info",
    )

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import chat
from app.routers import liveness, readiness, startup
from .otel_logging import setup_logging

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

setup_logging()

app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(chat.router, prefix="/v1")
app.include_router(liveness.router, prefix="/v1")
app.include_router(readiness.router, prefix="/v1")
app.include_router(startup.router, prefix="/v1")

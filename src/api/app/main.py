import os
import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.otlp_logging import configure_oltp_grpc_tracing
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

import app.temp_logging

from app.routers import chat
from app.routers import liveness, readiness, startup
from app.dependencies import setup_dependencies

@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_dependencies()
    yield

app = FastAPI(lifespan=lifespan, debug=True)

logging.basicConfig(level=logging.DEBUG)
# tracer = configure_oltp_grpc_tracing()
# FastAPIInstrumentor.instrument_app(app)
# logger = logging.getLogger(__name__)

app.include_router(chat.router, prefix="/v1")
app.include_router(liveness.router, prefix="/v1")
app.include_router(readiness.router, prefix="/v1")
app.include_router(startup.router, prefix="/v1")

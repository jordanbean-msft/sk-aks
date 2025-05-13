from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import chat
from app.routers import liveness, readiness, startup
from .logging import set_up_logging, set_up_tracing, set_up_metrics

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

set_up_logging()
set_up_tracing()
set_up_metrics()

app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(chat.router, prefix="/v1")
app.include_router(liveness.router, prefix="/v1")
app.include_router(readiness.router, prefix="/v1")
app.include_router(startup.router, prefix="/v1")

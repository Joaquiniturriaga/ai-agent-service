import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.http_client import close_client
from src.routes.agent_routes import router as agent_router
from src.routes.metrics_routes import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  
    await close_client()  


app = FastAPI(
    title="Valle del Sol — AI Agent Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router,  prefix="/api/agent")
app.include_router(metrics_router, prefix="/api/agent/metrics")


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-agent", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
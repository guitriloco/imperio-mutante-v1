import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from api_mutante.core.config import settings
from api_mutante.routers.generate import router as generate_router
from api_mutante.routers.knowledge import router as knowledge_router
from api_mutante.routers.prompts import router as prompts_router
from api_mutante.routers.rag import router as rag_router
from api_mutante.routers.chat import router as chat_router
from api_mutante.routers.scraper import router as scraper_router
from api_mutante.routers.swarm import router as swarm_router
from api_mutante.routers.mass_ingest import router as mass_ingest_router
from api_mutante.routers.monetization import router as monetization_router
from api_mutante.routers.billing import router as billing_router
from api_mutante.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    interval = int(os.getenv("KNOWLEDGE_SCAN_INTERVAL_SEC", "60"))
    scheduler.start_task(
        name="scan_unindexed_knowledge",
        interval_seconds=interval,
        coro_fn=scheduler.scan_unindexed_knowledge
    )
    yield
    await scheduler.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Motor assíncrono de API para inteligência e automação do Império Mutante.",
    lifespan=lifespan
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rotas
app.include_router(generate_router)
app.include_router(knowledge_router)
app.include_router(prompts_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(scraper_router)
app.include_router(swarm_router)
app.include_router(mass_ingest_router)
app.include_router(monetization_router)
app.include_router(billing_router)

# Caminho do Dashboard
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "interface_dashboard"
if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

@app.get("/", tags=["Health"])
async def root():
    if (DASHBOARD_DIR / "index.html").exists():
        return RedirectResponse(url="/dashboard/")
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.get("/v1/scheduler/status", tags=["Scheduler"])
async def scheduler_status():
    return scheduler.get_status()

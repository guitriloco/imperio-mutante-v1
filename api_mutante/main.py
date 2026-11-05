from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from api_mutante.core.config import settings
from api_mutante.routers.generate import router as generate_router
from api_mutante.routers.knowledge import router as knowledge_router
from api_mutante.routers.prompts import router as prompts_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Motor assíncrono de API para inteligência e automação do Império Mutante."
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rotas da API
app.include_router(generate_router)
app.include_router(knowledge_router)
app.include_router(prompts_router)

# Caminho do Dashboard
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "interface_dashboard"

if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

@app.get("/", tags=["Health"])
async def root():
    # Redireciona raiz diretamente para o Painel Visual
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_mutante.core.config import settings
from api_mutante.routers.generate import router as generate_router
from api_mutante.routers.knowledge import router as knowledge_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Motor assíncrono de API para inteligência e automação do Império Mutante."
)

# Configuração de CORS para permitir chamadas de frontends futuros (Next.js, etc.)
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

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

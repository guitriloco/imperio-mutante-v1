@echo off
TITLE [IMPERIO MUTANTE] - SOVEREIGN FULLSTACK ENGINE
COLOR 0A
cls

echo ===============================================================================
echo            IMPERIO MUTANTE - ORQUESTRADOR FULLSTACK LOCAL
echo ===============================================================================
echo [STATUS] Verificando dependencias e inicializando servicos...
echo.

set "BASE_DIR=%~dp0"
set "FRONT_DIR=%~dp0frontend"

:: 1. Iniciar Backend FastAPI
echo [BACKEND] Iniciando API FastAPI na porta 8000...
start "MUTANTE BACKEND (FastAPI :8000)" cmd /k "cd /d "%BASE_DIR%" && call .venv\Scripts\activate.bat && python -m uvicorn api_mutante.main:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Iniciar Frontend Next.js
echo [FRONTEND] Iniciando Cockpit Next.js na porta 3000...
start "MUTANTE FRONTEND (Next.js :3000)" cmd /k "cd /d "%FRONT_DIR%" && npm run dev -- -p 3000"

echo.
echo ===============================================================================
echo   SERVICOS EM EXECUCAO EM TERMINAIS DEDICADOS:
echo   - Backend FastAPI API:     http://localhost:8000
echo   - Documentacao Swagger:   http://localhost:8000/docs
echo   - Health Endpoint:        http://localhost:8000/health
echo   - Cockpit Next.js UI:     http://localhost:3000
echo ===============================================================================
echo Pressione qualquer tecla para verificar a integridade da API...
pause >nul

echo [HEALTH CHECK] Testando resposta da API...
curl -s http://127.0.0.1:8000/health
echo.
echo.
echo [CONCLUIDO] Servicos ativos. Pressione qualquer tecla para fechar este inicializador.
pause >nul

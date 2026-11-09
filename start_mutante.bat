@echo off
TITLE [IMPERIO MUTANTE] - SOVEREIGN FULLSTACK ENGINE
COLOR 0A
chcp 65001 >nul
cls

echo ===============================================================================
echo            ⚡ IMPERIO MUTANTE - ORQUESTRADOR FULLSTACK LOCAL ⚡
echo ===============================================================================
echo [STATUS] Verificando dependencias e inicializando servicos...
echo.

cd /d "%~dp0"

:: 1. Ativar Virtualenv Python e Iniciar Backend
if exist ".venv\Scripts\activate.bat" (
    echo [BACKEND] Virtualenv detectado (.venv). Ativando...
) else (
    echo [ALERTA] .venv nao encontrado. Usando Python padrao do sistema...
)

echo [BACKEND] Iniciando API FastAPI na porta 8000...
start "MUTANTE BACKEND (FastAPI :8000)" cmd /k "chcp 65001 >nul && call .venv\Scripts\activate.bat && python -m uvicorn api_mutante.main:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Iniciar Frontend Next.js
echo [FRONTEND] Iniciando Cockpit Next.js na porta 3000...
cd frontend
if not exist "node_modules" (
    echo [FRONTEND] Instalando dependencias do frontend pela primeira vez...
    call npm ci
)
start "MUTANTE FRONTEND (Next.js :3000)" cmd /k "chcp 65001 >nul && npm run dev -- -p 3000"

cd /d "%~dp0"

echo.
echo ===============================================================================
echo   🚀 SERVICOS EM EXECUCAO EM TERMINAIS DEDICADOS:
echo   - Backend FastAPI API:     http://localhost:8000
echo   - Documentacao Swagger:   http://localhost:8000/docs
echo   - Health Endpoint:        http://localhost:8000/health
echo   - Cockpit Next.js UI:     http://localhost:3000
echo ===============================================================================
echo Pressione qualquer tecla para verificar a integridade da API...
pause >nul

curl -s http://localhost:8000/health
echo.
echo [CONCLUIDO] Pressione qualquer tecla para fechar este assistente de inicializacao.
pause >nul

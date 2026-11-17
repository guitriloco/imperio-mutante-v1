# Império Mutante

Plataforma experimental de inteligência e automação com uma API assíncrona em **FastAPI**, integração com **Google Gemini** e uma interface web em **Next.js**. A API reúne módulos para geração de conteúdo, chat com recuperação de contexto (RAG), gestão de conhecimento e outras rotas de automação.

> Projeto pessoal em desenvolvimento. Configure suas próprias credenciais e revise os recursos disponíveis antes de usar em produção.

## Tecnologias

- Python 3.11, FastAPI, Pydantic e Uvicorn
- Google Gen AI SDK (Gemini)
- Next.js, React e TypeScript
- Docker e Docker Compose

## Requisitos

- Docker e Docker Compose **ou** Python 3.11+ e Node.js 20+
- Uma chave da API Gemini para usar os recursos que dependem do modelo

## Configuração

Na raiz do projeto, crie um arquivo `.env` e configure sua chave:

```env
GEMINI_API_KEY=sua_chave_gemini
DEFAULT_GEMINI_MODEL=gemini-2.5-flash
API_PORT=8000
FRONTEND_PORT=3000
```

Nunca publique chaves, tokens ou outras credenciais. O arquivo `.env` deve permanecer fora do controle de versão.

## Executar com Docker Compose

Na raiz do repositório, execute:

```bash
docker compose up --build
```

Depois, acesse:

- Interface web: http://localhost:3000
- API: http://localhost:8000
- Documentação interativa da API: http://localhost:8000/docs
- Verificação de saúde: http://localhost:8000/health

Para encerrar os serviços:

```bash
docker compose down
```

## Executar em desenvolvimento

### API

Na raiz do repositório, crie e ative um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Instale os pacotes e inicie a API:

```bash
pip install -r requirements.txt
uvicorn api_mutante.main:app --reload --host 0.0.0.0 --port 8000
```

### Interface web

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

A interface de desenvolvimento estará em http://localhost:3000.

## Rotas e módulos

A API registra módulos para geração, chat, busca RAG, conhecimento, prompts, scraping, swarm, ingestão em lote, monetização e cobrança. Consulte a documentação interativa em `/docs` para ver os caminhos, parâmetros e modelos de requisição disponíveis na versão em execução.

Também há uma rota de status do agendador em `/v1/scheduler/status`. A API verifica sua saúde em `/health`.

## Estrutura do repositório

```text
.
├── api_mutante/          # API FastAPI, serviços, rotas e lógica de conhecimento
├── frontend/             # Aplicação Next.js
├── interface_dashboard/  # Dashboard estático servido pela API, quando presente
├── scripts_brutos/       # Scripts auxiliares
├── main.py               # Exemplo simples de chamada ao Gemini
├── Dockerfile            # Imagem da API
└── docker-compose.yml    # API e frontend
```

## Licença

Uma licença não foi identificada neste repositório. Consulte o proprietário antes de reutilizar ou distribuir o código.

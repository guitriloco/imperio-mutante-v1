---
name: imperio-sync
description: Executa a bateria de testes automatizados, valida o motor de API e sincroniza commits atômicos com o GitHub no padrão Império Mutante.
---

# Império Sync: Protocolo de Automação e Sincronização

Esta skill define o procedimento rigoroso para testar, validar e sincronizar alterações no repositório `imperio_mutante_v1`.

## Quando Utilizar
- Após implementar novas rotas, serviços ou templates de IA.
- Antes de submeter código para branches remotas (`main`).
- Para auditar a integridade dos testes e a comunicação do agendador em segundo plano.

---

## Procedimento de Execução Passo a Passo

### 1. Bateria de Testes Locais
Execute todos os scripts de validação na raiz do projeto:
```powershell
Set-Location "C:\Users\Administrator\ImperioMutante\01_CODIGOS\imperio_mutante_v1"
.\.venv\Scripts\python.exe scripts_brutos\test_api_server.py
.\.venv\Scripts\python.exe scripts_brutos\test_knowledge_ingest.py
.\.venv\Scripts\python.exe scripts_brutos\test_dashboard_integration.py
```
*Critério de Sucesso:* Todos os scripts devem retornar código de saída `0` com status `200 OK`.

### 2. Validação do Agendador de Tarefas
Inicie o servidor de teste ou verifique a rota:
```powershell
.\.venv\Scripts\python.exe scripts_brutos\test_scheduler.py
```

### 3. Consolidação de Git e Commit
Siga as convenções de commit estritas (`feat:`, `fix:`, `chore:`, `refactor:`):
```powershell
git status
git add .
git commit -m "<tipo>: <descricao cirurgica da mudanca>"
git push origin main
```

### 4. Auditoria de Segurança
- Certifique-se de que nenhum arquivo `.env` com chaves reais foi adicionado ao stage do Git.
- O `.gitignore` deve manter `.venv/`, `.env*` e caches ignorados.

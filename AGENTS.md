# Diretrizes Operacionais para Agentes & Contribuidores (Império Mutante)

## 1. Protocolo dos Agentes de IA
- **Execução Cirúrgica:** Toda modificação deve ser atômica, modular e testada antes do commit.
- **Não Rompimento:** Nunca quebre pipelines existentes. Preserve retrocompatibilidade com endpoints e chamadas de API.
- **Segurança Absoluta:** Chaves de API, senhas ou tokens NUNCA devem ser versionados em código ou commits. Use sempre variáveis em `.env`.

## 2. Padrões de Código Python
- **Paradigma:** Assíncrono por padrão (`async/await`, `asyncio`, `httpx`, `client.aio`).
- **Tipagem Estrita:** Uso obrigatório de Type Hints (`typing` / Python 3.10+ unions `X | Y`).
- **SDKs:** Priorizar sempre SDKs modernos e oficiais (ex: `google-genai` para Gemini API, Pydantic v2 para validação de dados).
- **Tratamento de Erros:** Exceções capturadas com mensagens contextuais e logging estruturado.

## 3. Padrão de Commits (Conventional Commits)
- `feat:` Nova funcionalidade ou recurso.
- `fix:` Correção de bug.
- `refactor:` Alteração de código sem mudar comportamento.
- `docs:` Modificações na documentação.
- `chore:` Tarefas de manutenção, dependências ou configurações.
- `perf:` Melhorias de performance.

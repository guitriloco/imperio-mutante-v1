import re
from pathlib import Path
from typing import Dict, Any, Optional

from api_mutante.core.gemini_service import gemini_service
from api_mutante.rag_engine import rag_engine
from api_mutante.agents.sub_agents import TaskPlannerAgent, CodeAuditorAgent, TestRunnerAgent

class SwarmOrchestrator:
    """Orquestrador Central Multi-Agente com Loop de Auto-Cura de Código (Self-Healing)."""

    def __init__(self):
        self.planner = TaskPlannerAgent()
        self.auditor = CodeAuditorAgent()
        self.runner = TestRunnerAgent()

    async def execute_task_with_healing(
        self,
        script_path: str,
        max_healing_cycles: int = 3
    ) -> Dict[str, Any]:
        """Executa um script Python e, se houver falha, aciona o loop de auto-cura até o reparo definitivo."""
        target_file = Path(script_path)
        if not target_file.exists():
            raise FileNotFoundError(f"Arquivo alvo não encontrado: {script_path}")

        healing_history = []
        is_fixed = False

        for cycle in range(1, max_healing_cycles + 1):
            # 1. TestRunnerAgent executa o código
            exec_result = await self.runner.run_code(str(target_file))

            if exec_result["success"]:
                is_fixed = True
                break

            # 2. Falha detectada: Captura traceback e erro
            error_trace = exec_result["stderr"] or exec_result["stdout"]
            original_code = target_file.read_text(encoding="utf-8")

            # 3. Consulta RAGEngine para recuperar contexto e diretrizes do repositório
            rag_hits = await rag_engine.search(query=f"Correção de erro Python: {error_trace[:200]}", top_k=1)
            rag_context = rag_hits[0]["summary"] if rag_hits else "Padrões estritos de Python assíncrono do Império Mutante."

            # 4. Auditoria e Geração do Patch pelo Gemini
            patch_prompt = (
                f"Você é o Self-Healing Engine do Império Mutante.\n"
                f"O seguinte script Python falhou durante a execução:\n\n"
                f"ARQUIVO: {target_file.name}\n"
                f"CÓDIGO ATUAL:\n```python\n{original_code}\n```\n\n"
                f"ERRO OCORRIDO:\n{error_trace}\n\n"
                f"CONTEXTO DO PROJETO:\n{rag_context}\n\n"
                f"Retorne OBRIGATORIAMENTE o código Python COMPLETO corrigido dentro de um bloco ```python ... ``` sem preâmbulos."
            )

            system_inst = "Você é um mestre em depuração de código Python. Corrija o código de forma cirúrgica e limpa."
            patched_output = await gemini_service.generate_async(prompt=patch_prompt, system_instruction=system_inst)

            # 5. Extração do código corrigido
            match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", patched_output.strip())
            patched_code = match.group(1).strip() if match else patched_output.strip()

            # 6. Aplica o patch no arquivo
            target_file.write_text(patched_code, encoding="utf-8")

            healing_history.append({
                "cycle": cycle,
                "error_resolved": error_trace[:300],
                "patch_applied": True
            })

        # Validação final pós-ciclos
        final_run = await self.runner.run_code(str(target_file))

        return {
            "success": final_run["success"],
            "script_path": str(target_file),
            "healing_cycles_used": len(healing_history),
            "healing_history": healing_history,
            "final_stdout": final_run["stdout"],
            "final_stderr": final_run["stderr"]
        }

swarm_orchestrator = SwarmOrchestrator()

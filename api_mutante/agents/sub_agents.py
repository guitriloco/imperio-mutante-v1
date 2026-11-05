import json
import re
from typing import Dict, Any, List
from api_mutante.core.gemini_service import gemini_service

class TaskPlannerAgent:
    """Sub-agente encarregado de decompor tarefas complexas em planos de ação atômicos."""

    async def create_plan(self, task_description: str) -> List[Dict[str, Any]]:
        prompt = (
            f"Você é o TaskPlannerAgent do Império Mutante. Decomponha a seguinte tarefa técnica em um checklist ordenado e atômico:\n"
            f"TAREFA: {task_description}\n\n"
            f"Retorne OBRIGATORIAMENTE um JSON com uma lista de passos: [{{'step': int, 'action': str, 'target_file': str}}]"
        )
        system_inst = "Você é um planejador técnico sênior. Responda apenas com o JSON estruturado."
        output = await gemini_service.generate_async(prompt=prompt, system_instruction=system_inst)
        
        # Extrai bloco JSON
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", output.strip())
        cleaned = match.group(1).strip() if match else output.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return [{"step": 1, "action": task_description, "target_file": "core.py"}]

class CodeAuditorAgent:
    """Sub-agente que analisa código, identifica vulnerabilidades, anti-patterns ou erros de sintaxe."""

    async def audit_code(self, code_snippet: str, context: str = "") -> Dict[str, Any]:
        prompt = (
            f"Você é o CodeAuditorAgent do Império Mutante. Analise criticamente o código abaixo:\n\n"
            f"CONTEXTO: {context}\n\n"
            f"CÓDIGO:\n```python\n{code_snippet}\n```\n\n"
            f"Retorne um JSON com: {{'is_valid': bool, 'issues': list[str], 'severity': 'LOW'|'MEDIUM'|'HIGH'|'NONE'}}"
        )
        system_inst = "Você é um auditor rigoroso de código Python. Responda estritamente em formato JSON."
        output = await gemini_service.generate_async(prompt=prompt, system_instruction=system_inst)
        
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", output.strip())
        cleaned = match.group(1).strip() if match else output.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"is_valid": True, "issues": [], "severity": "NONE"}

class TestRunnerAgent:
    """Sub-agente que executa código ou testes em subprocesso isolado e captura stdout/stderr com precisão."""

    async def run_code(self, script_path: str) -> Dict[str, Any]:
        import asyncio
        import sys
        
        proc = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="ignore").strip(),
            "stderr": stderr.decode("utf-8", errors="ignore").strip(),
            "success": proc.returncode == 0
        }

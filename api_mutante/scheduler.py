import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Coroutine, Dict, Any

from api_mutante.routers.knowledge import KNOWLEDGE_DIR, DATA_DIR, extract_text_from_file, parse_json_from_gemini
from api_mutante.core.gemini_service import gemini_service
from api_mutante.prompts_manager import prompts_manager

logger = logging.getLogger("api_mutante.scheduler")

class AsyncScheduler:
    """Agendador assíncrono nativo para tarefas em segundo plano (Zero-Cost)."""

    def __init__(self):
        self.is_running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self.last_runs: Dict[str, str] = {}
        self.execution_counts: Dict[str, int] = {}

    async def scan_unindexed_knowledge(self) -> int:
        """Varre 02_CONHECIMENTO e processa arquivos que ainda não estão no index.json."""
        if not KNOWLEDGE_DIR.exists():
            return 0

        index_file = DATA_DIR / "index.json"
        indexed_names = set()
        if index_file.exists():
            try:
                import json
                with open(index_file, "r", encoding="utf-8") as f:
                    indexed_names = set(json.load(f).keys())
            except Exception:
                indexed_names = set()

        unindexed_files = [
            f for f in KNOWLEDGE_DIR.glob("*")
            if f.is_file() and f.suffix.lower() in [".txt", ".md", ".pdf"] and f.name not in indexed_names
        ]

        if not unindexed_files:
            return 0

        processed = 0
        for file_path in unindexed_files:
            try:
                raw_text = extract_text_from_file(file_path)
                if not raw_text.strip():
                    continue

                prompt, system_inst = prompts_manager.render(
                    "knowledge_summarizer",
                    content=raw_text[:40000]
                )

                output = await gemini_service.generate_async(
                    prompt=prompt,
                    system_instruction=system_inst
                )

                data = parse_json_from_gemini(output)
                data["source_file"] = file_path.name

                import json
                out_path = DATA_DIR / f"{file_path.stem}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Atualiza índice
                all_index = {}
                if index_file.exists():
                    try:
                        with open(index_file, "r", encoding="utf-8") as f:
                            all_index = json.load(f)
                    except Exception:
                        all_index = {}

                all_index[file_path.name] = {
                    "title": data.get("title", file_path.stem),
                    "summary": data.get("summary", ""),
                    "tags": data.get("tags", []),
                    "json_path": str(out_path)
                }

                with open(index_file, "w", encoding="utf-8") as f:
                    json.dump(all_index, f, indent=2, ensure_ascii=False)

                processed += 1
            except Exception as e:
                logger.error(f"Erro ao processar {file_path.name}: {e}")

        return processed

    async def _periodic_loop(self, name: str, interval_seconds: int, coro_fn: Callable[[], Coroutine[Any, Any, Any]]):
        """Loop infinito de execução periódica com tratamento de exceções."""
        while self.is_running:
            try:
                self.last_runs[name] = datetime.now().isoformat()
                self.execution_counts[name] = self.execution_counts.get(name, 0) + 1
                await coro_fn()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] Erro na tarefa '{name}': {e}")
            
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break

    def start_task(self, name: str, interval_seconds: int, coro_fn: Callable[[], Coroutine[Any, Any, Any]]):
        """Inicia uma tarefa periódica em background."""
        if name in self._tasks and not self._tasks[name].done():
            return
        self.is_running = True
        task = asyncio.create_task(self._periodic_loop(name, interval_seconds, coro_fn))
        self._tasks[name] = task

    async def stop(self):
        """Cancela todas as tarefas em execução limpa."""
        self.is_running = False
        for name, task in self._tasks.items():
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "active_tasks": list(self._tasks.keys()),
            "last_runs": self.last_runs,
            "execution_counts": self.execution_counts
        }

scheduler = AsyncScheduler()

import json
from pathlib import Path
from typing import Any, Dict

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

class PromptsManager:
    """Gerencia templates de prompts e instruções exportados do Google AI Studio e Stitch."""

    def __init__(self, storage_dir: Path = PROMPTS_DIR):
        self.storage_dir = storage_dir
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._load_builtins()
        self.reload_from_disk()

    def _load_builtins(self):
        """Templates nativos de alta performance do Império Mutante."""
        self._templates["knowledge_summarizer"] = {
            "name": "knowledge_summarizer",
            "system_instruction": (
                "Você é a inteligência tática de extração de conhecimento do Império Mutante. "
                "Sua missão é extrair inteligência acionável, estratégias e sínteses cirúrgicas sem enrolação."
            ),
            "template": (
                "Analise o documento abaixo e retorne uma resposta no formato JSON estruturado com os campos:\n"
                "- title (título conciso)\n"
                "- summary (resumo executivo do conteúdo)\n"
                "- key_takeaways (lista dos pontos mais importantes)\n"
                "- actionable_insights (como monetizar ou aplicar este conhecimento na prática)\n"
                "- tags (lista de palavras-chave)\n\n"
                "DOCUMENTO:\n{content}\n"
            )
        }

    def reload_from_disk(self):
        """Carrega arquivos JSON salvos na pasta de prompts."""
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    name = data.get("name", file.stem)
                    self._templates[name] = data
            except Exception as e:
                print(f"[AVISO] Falha ao carregar prompt {file.name}: {e}")

    def save_template(self, name: str, template: str, system_instruction: str = "") -> Path:
        """Salva um template importado do AI Studio ou Stitch."""
        payload = {
            "name": name,
            "system_instruction": system_instruction,
            "template": template
        }
        self._templates[name] = payload
        dest = self.storage_dir / f"{name}.json"
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return dest

    def get_template(self, name: str) -> Dict[str, Any]:
        if name not in self._templates:
            raise KeyError(f"Template '{name}' não encontrado.")
        return self._templates[name]

    def render(self, name: str, **kwargs) -> tuple[str, str]:
        """Retorna (prompt_renderizado, system_instruction)."""
        tmpl = self.get_template(name)
        rendered_prompt = tmpl["template"].format(**kwargs)
        return rendered_prompt, tmpl.get("system_instruction", "")

prompts_manager = PromptsManager()

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from api_mutante.core.gemini_service import gemini_service
from api_mutante.routers.knowledge import KNOWLEDGE_DIR
from api_mutante.rag_engine import rag_engine

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "_", text)[:50]

class AutonomousScraperService:
    """Serviço assíncrono de raspagem e síntese autônoma de conteúdo web com injeção RAG."""

    def __init__(self, timeout_sec: float = 15.0):
        self.timeout = timeout_sec
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 ImperioMutanteBot/1.0"
            )
        }

    async def fetch_and_clean_html(self, url: str) -> Dict[str, str]:
        """Executa requisição HTTP assíncrona e extrai texto limpo e legível do DOM."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Elimina tags ruidosas
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
            tag.decompose()

        # Extrai título da página
        title = soup.title.string.strip() if soup.title and soup.title.string else "Artigo Web"

        # Constrói o texto principal dos parágrafos e cabeçalhos
        body_elements = soup.find_all(["h1", "h2", "h3", "p", "li"])
        cleaned_text = "\n".join([el.get_text(strip=True) for el in body_elements if len(el.get_text(strip=True)) > 20])

        return {
            "title": title,
            "url": url,
            "raw_text": cleaned_text[:35000] # Limite tático de segurança
        }

    async def synthesize_article(self, article_data: Dict[str, str], research_topic: Optional[str] = None) -> str:
        """Sintetiza o conteúdo capturado em formato Markdown estratégico via Gemini."""
        prompt = (
            f"Você é o Agente Autônomo de Pesquisa e Inteligência do Império Mutante.\n"
            f"Analise o texto raspado da URL ({article_data['url']}) e gere um documento executivo em Markdown.\n"
            f"TÓPICO DE FOCO: {research_topic or 'Análise de Inteligência Estratégica'}\n\n"
            f"CONTEÚDO EXTRAÍDO:\n{article_data['raw_text']}\n\n"
            f"ESTRUTURA OBRIGATÓRIA DO MARKDOWN:\n"
            f"# [Título Estratégico]\n"
            f"**Fonte Original:** {article_data['url']}\n"
            f"**Data da Coleta:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## Resumo Executivo\n[3 a 4 parágrafos densos]\n\n"
            f"## Insights Acionáveis & Aplicação Prática\n[Lista com bullet points práticos]\n\n"
            f"## Dados e Fatos Relevantes\n[Lista com pontos-chave quantificáveis]\n"
        )

        system_inst = "Você é um analista de inteligência de elite. Extraia somente valor estratégico de alta densidade sem enrolação."
        return await gemini_service.generate_async(
            prompt=prompt,
            system_instruction=system_inst
        )

    async def research_and_ingest(
        self,
        url: str,
        topic: Optional[str] = None,
        auto_index_rag: bool = True
    ) -> Dict[str, Any]:
        """Pipeline completo: raspagem assíncrona -> síntese Gemini -> gravação em 02_CONHECIMENTO -> indexação RAG."""
        # 1. Raspagem e limpeza
        cleaned = await self.fetch_and_clean_html(url)
        if not cleaned["raw_text"]:
            raise ValueError(f"Nenhum conteúdo legível extraído da URL: {url}")

        # 2. Síntese via IA
        synthesized_md = await self.synthesize_article(cleaned, topic)

        # 3. Gravação em 02_CONHECIMENTO
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"web_{slugify(cleaned['title'])}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        dest_path = KNOWLEDGE_DIR / filename
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(synthesized_md)

        # 4. Disparo opcional de reindexação no RAGEngine
        indexed_count = 0
        if auto_index_rag:
            # O AsyncScheduler ou RAGEngine podem indexar diretamente
            indexed_count = await rag_engine.index_all_documents(force=False)

        return {
            "success": True,
            "url": url,
            "title": cleaned["title"],
            "saved_file": str(dest_path),
            "filename": filename,
            "rag_indexed": auto_index_rag,
            "preview_summary": synthesized_md[:300] + "..."
        }

scraper_service = AutonomousScraperService()

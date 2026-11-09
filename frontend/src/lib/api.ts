export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "model";
  content: string;
}

export interface SourceCitation {
  source_file: string;
  title: string;
  score: number;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  sources: SourceCitation[];
  model_used: string;
}

export interface KnowledgeDocument {
  title: string;
  summary: string;
  tags: string[];
  json_path: string;
}

export interface TierConfig {
  rpm: number;
  daily_tokens: number;
  allowed_models: string[];
}

export interface GeneratedKeyResponse {
  success: boolean;
  api_key: string;
  owner: string;
  tier: string;
  rate_limit_rpm: number;
  allowed_models: string[];
}

export const api = {
  async getHealth(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error("Backend offline");
    return res.json();
  },

  async sendChatMessage(message: string, history: ChatMessage[] = [], apiKey?: string): Promise<ChatResponse> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;

    const res = await fetch(`${API_BASE_URL}/v1/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ message, history: history.slice(-6), top_k: 3 }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha na comunicação RAG");
    }
    return res.json();
  },

  async getDocuments(): Promise<Record<string, KnowledgeDocument>> {
    const res = await fetch(`${API_BASE_URL}/v1/knowledge/documents`);
    if (!res.ok) throw new Error("Falha ao carregar documentos");
    return res.json();
  },

  async triggerKnowledgeIngest(): Promise<{ success: boolean; processed_count: number }> {
    const res = await fetch(`${API_BASE_URL}/v1/knowledge/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (!res.ok) throw new Error("Falha na ingestão");
    return res.json();
  },

  async getTiers(): Promise<Record<string, TierConfig>> {
    const res = await fetch(`${API_BASE_URL}/v1/monetization/tiers`);
    if (!res.ok) throw new Error("Falha ao listar tiers");
    return res.json();
  },

  async generateApiKey(ownerName: string, tier: string): Promise<GeneratedKeyResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/monetization/keys/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ owner_name: ownerName, tier }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao gerar chave");
    }
    return res.json();
  },

  async triggerWebResearch(url: string, topic?: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/v1/research/scrape-and-ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, topic, auto_index_rag: true }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha na pesquisa web");
    }
    return res.json();
  }
};

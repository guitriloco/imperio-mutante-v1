export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface WebSource {
  title: string;
  url: string;
}

export interface TelemetryData {
  prompt_tokens?: number;
  candidates_tokens?: number;
  thoughts_tokens?: number;
  total_tokens?: number;
  estimated_cost_usd?: number;
  latency_ms?: number;
  model_used?: string;
  web_sources?: WebSource[];
}

export interface ChatMessage {
  role: "user" | "model";
  content: string;
  thought?: string;
  telemetry?: TelemetryData;
  web_sources?: WebSource[];
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
  lastSources: SourceCitation[];
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

export interface UploadKnowledgeResponse {
  success: boolean;
  filename: string;
  bytes_saved: number;
  title?: string;
  summary?: string;
  tags: string[];
  rag_indexed: boolean;
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

export interface SwarmAgentInfo {
  role: string;
  state: string;
  model: string;
}

export interface SwarmStatus {
  status: string;
  agents: Record<string, SwarmAgentInfo>;
  healing_engine_active: boolean;
}

export interface PlanStep {
  step: number;
  action: string;
  target_file: string;
}

export interface PlanResponse {
  success: boolean;
  task_description: string;
  plan: PlanStep[];
}

export interface AuditResponse {
  success: boolean;
  is_valid: boolean;
  severity: "NONE" | "LOW" | "MEDIUM" | "HIGH";
  issues: string[];
}

export interface SelfHealingResponse {
  success: boolean;
  script_path: string;
  healing_cycles_used: number;
  healing_history: Array<{ cycle: number; error_resolved: string; patch_applied: boolean }>;
  final_stdout: string;
  final_stderr: string;
}

export interface BillingOrder {
  order_id: string;
  customer_email: string;
  customer_name: string;
  tier: string;
  amount_paid?: number;
  payment_ref?: string;
  api_key_issued?: string;
  timestamp: string;
  status: string;
}

export interface CreateCheckoutRequest {
  customer_name: string;
  customer_email: string;
  tier: string;
  payment_method: string;
}

export interface CheckoutSessionResponse {
  order_id: string;
  status: string;
  tier: string;
  amount: number;
  payment_method: string;
  pix_code?: string;
  qr_code_svg?: string;
  is_sandbox: boolean;
  expires_at: string;
  message: string;
}

export interface OrderStatusResponse {
  order_id: string;
  status: string;
  tier: string;
  amount_paid?: number;
  customer_email: string;
  customer_name: string;
  api_key_issued?: string;
  rate_limit_rpm?: number;
  timestamp: string;
}

export interface ProvisionLicenseRequest {
  customer_email: string;
  customer_name: string;
  tier: string;
  payment_reference: string;
  amount_paid: number;
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

  async streamChatMessage(
    message: string,
    history: ChatMessage[] = [],
    onMeta: (meta: { sources: SourceCitation[]; model_used: string }) => void,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: string) => void,
    options?: {
      apiKey?: string;
      enableSearch?: boolean;
      enableThinking?: boolean;
      thinkingBudget?: number;
      model?: string;
      onThought?: (thought: string) => void;
      onTelemetry?: (telemetry: TelemetryData) => void;
    }
  ): Promise<void> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (options?.apiKey) headers["X-API-Key"] = options.apiKey;

    try {
      const res = await fetch(`${API_BASE_URL}/v1/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message,
          history: history.slice(-6).map((h) => ({ role: h.role, content: h.content })),
          top_k: 3,
          enable_search: options?.enableSearch || false,
          enable_thinking: options?.enableThinking || false,
          thinking_budget: options?.thinkingBudget || 1024,
          model: options?.model || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        onError(err.detail || `HTTP ${res.status}`);
        return;
      }

      if (!res.body) {
        onError("Stream body não disponível");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          if (!block.trim()) continue;
          let currentEvent = "";
          let currentData = "";

          for (const line of block.split("\n")) {
            if (line.startsWith("event:")) {
              currentEvent = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              currentData = line.replace("data:", "").trim();
            }
          }

          if (currentData) {
            try {
              const parsed = JSON.parse(currentData);
              if (currentEvent === "meta") {
                onMeta(parsed);
              } else if (currentEvent === "thought") {
                if (options?.onThought) options.onThought(parsed.thought || "");
              } else if (currentEvent === "token") {
                onToken(parsed.token || "");
              } else if (currentEvent === "telemetry") {
                if (options?.onTelemetry) options.onTelemetry(parsed);
              } else if (currentEvent === "done") {
                onDone();
                return;
              } else if (currentEvent === "error") {
                onError(parsed.error || "Erro no streaming");
                return;
              }
            } catch (e) {
              // ignore parse errors on malformed chunks
            }
          }
        }
      }
      onDone();
    } catch (err: any) {
      onError(err.message || "Erro de conexão com o stream");
    }
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

  async uploadDocument(file: File, autoIndex: boolean = true): Promise<UploadKnowledgeResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/v1/knowledge/upload?auto_index=${autoIndex}`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha no upload do documento");
    }
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
  },

  async getSwarmStatus(): Promise<SwarmStatus> {
    const res = await fetch(`${API_BASE_URL}/v1/swarm/status`);
    if (!res.ok) throw new Error("Falha ao obter status do enxame");
    return res.json();
  },

  async planSwarmMission(taskDescription: string): Promise<PlanResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/swarm/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_description: taskDescription }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha no planejador");
    }
    return res.json();
  },

  async auditCode(codeSnippet: string, context?: string): Promise<AuditResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/swarm/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code_snippet: codeSnippet, context }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha na auditoria");
    }
    return res.json();
  },

  async runTestSandbox(scriptPath: string): Promise<{ success: boolean; exit_code: number; stdout: string; stderr: string }> {
    const res = await fetch(`${API_BASE_URL}/v1/swarm/run-test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script_path: scriptPath }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao executar teste");
    }
    return res.json();
  },

  async triggerSelfHealing(scriptPath: string, maxCycles: number = 3): Promise<SelfHealingResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/swarm/self-heal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script_path: scriptPath, max_healing_cycles: maxCycles }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha no loop de auto-cura");
    }
    return res.json();
  },

  async getBillingOrders(): Promise<BillingOrder[]> {
    const res = await fetch(`${API_BASE_URL}/v1/billing/orders`);
    if (!res.ok) throw new Error("Falha ao carregar ordens financeiras");
    return res.json();
  },

  async createCheckoutSession(req: CreateCheckoutRequest): Promise<CheckoutSessionResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/billing/create-checkout-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao iniciar checkout");
    }
    return res.json();
  },

  async getOrderStatus(orderId: string): Promise<OrderStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/v1/billing/order-status/${encodeURIComponent(orderId)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao verificar status da ordem");
    }
    return res.json();
  },

  async simulatePixPayment(orderId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/v1/billing/simulate-pix-payment/${encodeURIComponent(orderId)}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao simular liquidação PIX");
    }
    return res.json();
  },

  async provisionLicense(req: ProvisionLicenseRequest): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/v1/billing/provision-direct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Falha ao aprovisionar licença");
    }
    return res.json();
  }
};

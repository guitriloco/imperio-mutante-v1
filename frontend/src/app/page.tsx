"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  api,
  ChatMessage,
  SourceCitation,
  KnowledgeDocument,
  TierConfig,
  GeneratedKeyResponse,
} from "@/lib/api";
import {
  Terminal,
  Database,
  Key,
  Shield,
  Send,
  RefreshCw,
  Search,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Zap,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "knowledge" | "monetization">("chat");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [activeApiKey, setActiveApiKey] = useState<string>("");

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "model",
      content: "Império Mutante Online. Base vetorial conectada com embeddings de 3072 dimensões. Digite sua consulta estratégica.",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [lastSources, setLastSources] = useState<SourceCitation[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Knowledge State
  const [documents, setDocuments] = useState<Record<string, KnowledgeDocument>>({});
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [researchUrl, setResearchUrl] = useState("");
  const [researchTopic, setResearchTopic] = useState("");
  const [isResearching, setIsResearching] = useState(false);

  // Monetization State
  const [tiers, setTiers] = useState<Record<string, TierConfig>>({});
  const [ownerName, setOwnerName] = useState("");
  const [selectedTier, setSelectedTier] = useState("PRO");
  const [generatedKey, setGeneratedKey] = useState<GeneratedKeyResponse | null>(null);
  const [isGeneratingKey, setIsGeneratingKey] = useState(false);

  // Check API Health
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  async function checkHealth() {
    try {
      await api.getHealth();
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }

  // Load Tab Data
  useEffect(() => {
    if (activeTab === "knowledge") {
      loadDocuments();
    } else if (activeTab === "monetization") {
      loadTiers();
    }
  }, [activeTab]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadDocuments() {
    setIsLoadingDocs(true);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingDocs(false);
    }
  }

  async function loadTiers() {
    try {
      const data = await api.getTiers();
      setTiers(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleSendMessage(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isSending) return;

    const userText = inputMessage.trim();
    setInputMessage("");

    // Insere mensagem do usuário e reserva balão para streaming da resposta
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userText },
      { role: "model", content: "" }
    ]);
    setIsSending(true);

    try {
      await api.streamChatMessage(
        userText,
        messages,
        (meta) => {
          setLastSources(meta.sources || []);
        },
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === "model") {
              updated[lastIdx] = {
                ...updated[lastIdx],
                content: updated[lastIdx].content + token
              };
            }
            return updated;
          });
        },
        () => {
          setIsSending(false);
        },
        (errMsg) => {
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === "model") {
              const prevContent = updated[lastIdx].content;
              updated[lastIdx] = {
                ...updated[lastIdx],
                content: prevContent ? `${prevContent}\n\n[ERRO]: ${errMsg}` : `[ERRO]: ${errMsg}`
              };
            }
            return updated;
          });
          setIsSending(false);
        },
        activeApiKey || undefined
      );
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "model", content: `[ERRO]: ${err.message}` },
      ]);
      setIsSending(false);
    }
  }

  async function handleTriggerIngest() {
    setIsLoadingDocs(true);
    try {
      await api.triggerKnowledgeIngest();
      await loadDocuments();
    } catch (err: any) {
      alert(`Falha ao sincronizar: ${err.message}`);
    } finally {
      setIsLoadingDocs(false);
    }
  }

  async function handleWebResearch(e: React.FormEvent) {
    e.preventDefault();
    if (!researchUrl.trim() || isResearching) return;
    setIsResearching(true);
    try {
      await api.triggerWebResearch(researchUrl.trim(), researchTopic.trim() || undefined);
      setResearchUrl("");
      setResearchTopic("");
      await loadDocuments();
      alert("Pesquisa web raspada, sintetizada e indexada com sucesso!");
    } catch (err: any) {
      alert(`Falha na pesquisa web: ${err.message}`);
    } finally {
      setIsResearching(false);
    }
  }

  async function handleGenerateKey(e: React.FormEvent) {
    e.preventDefault();
    if (!ownerName.trim() || isGeneratingKey) return;
    setIsGeneratingKey(true);
    try {
      const res = await api.generateApiKey(ownerName.trim(), selectedTier);
      setGeneratedKey(res);
      setOwnerName("");
    } catch (err: any) {
      alert(`Falha ao gerar chave: ${err.message}`);
    } finally {
      setIsGeneratingKey(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] text-[#e5e5e5] flex flex-col font-mono selection:bg-[#00ff66] selection:text-black">
      {/* Top Header */}
      <header className="border-b border-[#1a1a1a] bg-[#0a0a0a] px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-[#00ff66] animate-pulse" />
          <h1 className="text-base font-bold tracking-widest text-white uppercase flex items-center gap-2">
            IMPÉRIO MUTANTE
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#171717] text-[#00e5ff] font-normal border border-[#262626]">
              NEXT.JS APPSUITE
            </span>
          </h1>
        </div>

        {/* Global Controls & Telemetry */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[#666]">BACKEND:</span>
            {apiOnline === null ? (
              <span className="text-[#888]">Checando...</span>
            ) : apiOnline ? (
              <span className="text-[#00ff66] flex items-center gap-1 font-semibold">
                <CheckCircle className="w-3.5 h-3.5" /> 8000 OPERACIONAL
              </span>
            ) : (
              <span className="text-red-500 flex items-center gap-1 font-semibold">
                <AlertCircle className="w-3.5 h-3.5" /> 8000 OFFLINE
              </span>
            )}
          </div>

          <div className="hidden sm:flex items-center gap-2 border-l border-[#222] pl-4">
            <span className="text-[#666]">X-API-KEY:</span>
            <input
              type="text"
              placeholder="mutante_pro_..."
              value={activeApiKey}
              onChange={(e) => setActiveApiKey(e.target.value)}
              className="bg-[#121212] border border-[#222] text-[#00e5ff] rounded px-2.5 py-1 text-[11px] w-40 focus:outline-none focus:border-[#00e5ff]"
            />
          </div>
        </div>
      </header>

      {/* Navigation Sub-header */}
      <nav className="border-b border-[#1a1a1a] bg-[#0c0c0c] px-6 flex gap-2">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center gap-2 px-5 py-3 text-xs uppercase font-bold tracking-wider border-b-2 transition-all ${
            activeTab === "chat"
              ? "border-[#00ff66] text-white bg-[#121212]"
              : "border-transparent text-[#666] hover:text-[#bbb]"
          }`}
        >
          <Terminal className="w-4 h-4 text-[#00ff66]" />
          [1] RAG Chat Studio
        </button>

        <button
          onClick={() => setActiveTab("knowledge")}
          className={`flex items-center gap-2 px-5 py-3 text-xs uppercase font-bold tracking-wider border-b-2 transition-all ${
            activeTab === "knowledge"
              ? "border-[#00e5ff] text-white bg-[#121212]"
              : "border-transparent text-[#666] hover:text-[#bbb]"
          }`}
        >
          <Database className="w-4 h-4 text-[#00e5ff]" />
          [2] Base de Conhecimento
        </button>

        <button
          onClick={() => setActiveTab("monetization")}
          className={`flex items-center gap-2 px-5 py-3 text-xs uppercase font-bold tracking-wider border-b-2 transition-all ${
            activeTab === "monetization"
              ? "border-amber-400 text-white bg-[#121212]"
              : "border-transparent text-[#666] hover:text-[#bbb]"
          }`}
        >
          <Key className="w-4 h-4 text-amber-400" />
          [3] Licenciamento & Tiers
        </button>
      </nav>

      {/* Main Container */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {/* TAB 1: RAG CHAT STUDIO */}
        {activeTab === "chat" && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[720px]">
            {/* Left: Chat Window (3 Cols) */}
            <div className="lg:col-span-3 bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-3 border-b border-[#1f1f1f] bg-[#121212] flex justify-between items-center text-xs">
                <span className="text-[#888] font-bold flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-[#00ff66]" /> CANAL CONVERSACIONAL DIRETO
                </span>
                <span className="text-[#555]">MODELO: gemini-2.5-flash</span>
              </div>

              {/* Messages Display */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                {messages.map((msg, i) => {
                  const isCurrentStreaming = isSending && i === messages.length - 1 && msg.role === "model";
                  return (
                    <div
                      key={i}
                      className={`flex flex-col ${
                        msg.role === "user" ? "items-end" : "items-start"
                      }`}
                    >
                      <span className="text-[10px] text-[#666] uppercase mb-1">
                        {msg.role === "user" ? "OPERADOR" : "AGENTE MUTANTE (RAG STREAM)"}
                      </span>
                      <div
                        className={`max-w-2xl rounded-lg px-4 py-3 text-xs leading-relaxed whitespace-pre-wrap ${
                          msg.role === "user"
                            ? "bg-[#1c1c1c] text-white border border-[#2a2a2a]"
                            : "bg-[#111] text-[#e0e0e0] border border-[#1f1f1f]"
                        }`}
                      >
                        {msg.content === "" && isCurrentStreaming ? (
                          <span className="text-[#00e5ff] animate-pulse flex items-center gap-2">
                            <span className="inline-block w-2 h-2 rounded-full bg-[#00e5ff] animate-ping" />
                            Recuperando fragmentos RAG & sintetizando resposta...
                          </span>
                        ) : (
                          <>
                            {msg.content}
                            {isCurrentStreaming && (
                              <span className="inline-block w-2 h-3.5 bg-[#00ff66] animate-pulse ml-1 align-middle" />
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendMessage} className="p-3 border-t border-[#1f1f1f] bg-[#0c0c0c] flex gap-2">
                <input
                  type="text"
                  placeholder="Envie sua mensagem ou pergunta com RAG..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  className="flex-1 bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white placeholder-[#555] focus:outline-none focus:border-[#00ff66]"
                />
                <button
                  type="submit"
                  disabled={isSending}
                  className="bg-[#00ff66] hover:bg-[#00dd55] text-black font-bold px-5 py-2.5 rounded text-xs uppercase tracking-wider flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" /> Enviar
                </button>
              </form>
            </div>

            {/* Right: Sources & Telemetry (1 Col) */}
            <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-4 flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-bold text-white uppercase border-b border-[#1f1f1f] pb-2 mb-3 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-[#00e5ff]" /> Fontes Citadas (RAG)
                </h3>
                {lastSources.length === 0 ? (
                  <p className="text-[11px] text-[#555] leading-relaxed">
                    Nenhuma fonte recuperada na última resposta. Envie uma consulta que envolva a base em 02_CONHECIMENTO.
                  </p>
                ) : (
                  <div className="space-y-2.5">
                    {lastSources.map((s, idx) => (
                      <div key={idx} className="bg-[#141414] border border-[#222] rounded p-2.5 text-[11px]">
                        <div className="font-bold text-white truncate">{s.title}</div>
                        <div className="text-[#666] text-[10px] truncate mt-0.5">{s.source_file}</div>
                        <div className="mt-1.5 text-[10px] text-[#00ff66]">
                          Similaridade: {(s.score * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-[#1f1f1f] text-[10px] text-[#555] space-y-1">
                <div>DIMENSÕES VETORIAIS: 3072-d</div>
                <div>FRAMEWORK: Next.js + FastAPI</div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: KNOWLEDGE BASE */}
        {activeTab === "knowledge" && (
          <div className="space-y-6">
            {/* Top Toolbar & Web Scraper Input */}
            <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#1f1f1f] pb-4">
                <div>
                  <h2 className="text-sm font-bold text-white uppercase">Acervo de Conhecimento Estruturado</h2>
                  <p className="text-xs text-[#666] mt-0.5">Sincronização contínua de arquivos em 02_CONHECIMENTO</p>
                </div>
                <button
                  onClick={handleTriggerIngest}
                  disabled={isLoadingDocs}
                  className="bg-[#171717] hover:bg-[#222] border border-[#2c2c2c] text-white px-4 py-2 rounded text-xs flex items-center gap-2 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isLoadingDocs ? "animate-spin" : ""}`} />
                  Reindexar Todos os Arquivos
                </button>
              </div>

              {/* Autonomous Web Research Form */}
              <form onSubmit={handleWebResearch} className="pt-2 flex flex-col sm:flex-row gap-2">
                <input
                  type="url"
                  placeholder="https://exemplo.com/artigo-ou-documentacao"
                  value={researchUrl}
                  onChange={(e) => setResearchUrl(e.target.value)}
                  required
                  className="flex-1 bg-[#141414] border border-[#222] rounded px-3.5 py-2 text-xs text-white placeholder-[#555] focus:outline-none focus:border-[#00e5ff]"
                />
                <input
                  type="text"
                  placeholder="Foco de Pesquisa (opcional)"
                  value={researchTopic}
                  onChange={(e) => setResearchTopic(e.target.value)}
                  className="sm:w-60 bg-[#141414] border border-[#222] rounded px-3.5 py-2 text-xs text-white placeholder-[#555] focus:outline-none focus:border-[#00e5ff]"
                />
                <button
                  type="submit"
                  disabled={isResearching}
                  className="bg-[#00e5ff] hover:bg-[#00ccee] text-black font-bold px-4 py-2 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition disabled:opacity-50"
                >
                  <Search className="w-3.5 h-3.5" />
                  {isResearching ? "Raspando..." : "Pesquisar & Ingerir"}
                </button>
              </form>
            </div>

            {/* Document Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.keys(documents).length === 0 ? (
                <div className="col-span-full bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-8 text-center text-xs text-[#666]">
                  Nenhum documento carregado. Clique em &quot;Reindexar Todos os Arquivos&quot; acima.
                </div>
              ) : (
                Object.entries(documents).map(([filename, doc]) => (
                  <div key={filename} className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-4 space-y-3 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start gap-2 mb-1">
                        <h4 className="text-xs font-bold text-white truncate">{doc.title || filename}</h4>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-[#00ff66] border border-emerald-800">
                          INDEXADO
                        </span>
                      </div>
                      <div className="text-[10px] text-[#555] truncate mb-2">{filename}</div>
                      <p className="text-[11px] text-[#aaa] leading-relaxed line-clamp-4">
                        {doc.summary || "Sem resumo disponível."}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-[#1a1a1a] flex flex-wrap gap-1">
                      {(doc.tags || []).slice(0, 4).map((t, idx) => (
                        <span key={idx} className="text-[9px] bg-[#171717] text-[#888] px-2 py-0.5 rounded">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 3: MONETIZATION & TIERS */}
        {activeTab === "monetization" && (
          <div className="space-y-6">
            {/* Tiers Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(tiers).map(([tierName, cfg]) => (
                <div
                  key={tierName}
                  className={`bg-[#0d0d0d] border rounded-lg p-5 space-y-4 ${
                    tierName === "ENTERPRISE"
                      ? "border-amber-500/40"
                      : tierName === "PRO"
                      ? "border-[#00e5ff]/40"
                      : "border-[#1f1f1f]"
                  }`}
                >
                  <div className="flex justify-between items-center border-b border-[#1f1f1f] pb-3">
                    <h3 className="text-sm font-bold text-white uppercase">{tierName}</h3>
                    <span className="text-xs text-[#00ff66] font-bold">
                      {tierName === "FREE" ? "GRATUITO" : tierName === "PRO" ? "R$ 97/mês" : "R$ 497/mês"}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs text-[#888]">
                    <div className="flex justify-between">
                      <span>Rate Limit:</span>
                      <span className="text-white font-bold">{cfg.rpm} RPM</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cota Diária:</span>
                      <span className="text-white font-bold">{cfg.daily_tokens.toLocaleString()} tokens</span>
                    </div>
                    <div>
                      <span>Modelos Liberados:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {cfg.allowed_models.map((m) => (
                          <span key={m} className="text-[10px] bg-[#171717] text-[#00e5ff] px-2 py-0.5 rounded">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Instant Key Issuance Gateway */}
            <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-6 space-y-4">
              <h3 className="text-xs font-bold text-white uppercase border-b border-[#1f1f1f] pb-2">
                Emissão Instantânea de Chave de API Licenciada
              </h3>
              <form onSubmit={handleGenerateKey} className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Nome do Cliente ou Empresa"
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  required
                  className="flex-1 bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white placeholder-[#555] focus:outline-none focus:border-amber-400"
                />
                <select
                  value={selectedTier}
                  onChange={(e) => setSelectedTier(e.target.value)}
                  className="bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
                >
                  <option value="FREE">FREE (5 RPM)</option>
                  <option value="PRO">PRO (60 RPM)</option>
                  <option value="ENTERPRISE">ENTERPRISE (300 RPM)</option>
                </select>
                <button
                  type="submit"
                  disabled={isGeneratingKey}
                  className="bg-amber-400 hover:bg-amber-500 text-black font-bold px-6 py-2.5 rounded text-xs uppercase tracking-wider transition disabled:opacity-50"
                >
                  {isGeneratingKey ? "Gerando..." : "Gerar Chave de Produção"}
                </button>
              </form>

              {/* Key Output Display */}
              {generatedKey && (
                <div className="mt-4 bg-[#111] border border-amber-400/40 rounded-lg p-4 space-y-2">
                  <div className="text-xs text-amber-400 font-bold uppercase">Chave de API Ativada:</div>
                  <div className="bg-[#050505] p-3 rounded text-xs text-[#00ff66] break-all border border-[#222]">
                    {generatedKey.api_key}
                  </div>
                  <div className="text-[11px] text-[#777] flex gap-4">
                    <span>Cliente: {generatedKey.owner}</span>
                    <span>Plano: {generatedKey.tier}</span>
                    <span>Limite: {generatedKey.rate_limit_rpm} RPM</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

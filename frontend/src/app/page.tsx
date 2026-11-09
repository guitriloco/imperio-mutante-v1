"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  api,
  ChatMessage,
  ChatSession,
  SourceCitation,
  KnowledgeDocument,
  TierConfig,
  GeneratedKeyResponse,
  SwarmStatus,
  PlanStep,
  AuditResponse,
  SelfHealingResponse,
  BillingOrder,
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
  Bot,
  Cpu,
  Bug,
  Play,
  ShieldAlert,
  UploadCloud,
  FileUp,
  Plus,
  Trash2,
  Download,
  MessageSquare,
  PanelLeftClose,
  PanelLeft,
  CreditCard,
  QrCode,
  ShoppingBag,
  X,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "knowledge" | "monetization" | "swarm">("chat");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [activeApiKey, setActiveApiKey] = useState<string>("");

  // Chat & Multi-Session State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState<string | null>(null);

  // Monetization State
  const [tiers, setTiers] = useState<Record<string, TierConfig>>({});
  const [ownerName, setOwnerName] = useState("");
  const [selectedTier, setSelectedTier] = useState("PRO");
  const [generatedKey, setGeneratedKey] = useState<GeneratedKeyResponse | null>(null);
  const [isGeneratingKey, setIsGeneratingKey] = useState(false);

  // Checkout & Billing State
  const [orders, setOrders] = useState<BillingOrder[]>([]);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [checkoutTier, setCheckoutTier] = useState<"PRO" | "ENTERPRISE">("PRO");
  const [checkoutAmount, setCheckoutAmount] = useState<number>(97);
  const [checkoutCustomerName, setCheckoutCustomerName] = useState("");
  const [checkoutCustomerEmail, setCheckoutCustomerEmail] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"pix" | "card">("pix");
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [paymentCompletedKey, setPaymentCompletedKey] = useState<string | null>(null);

  // Swarm State
  const [swarmStatus, setSwarmStatus] = useState<SwarmStatus | null>(null);
  const [swarmMode, setSwarmMode] = useState<"heal" | "plan" | "audit">("heal");
  const [missionInput, setMissionInput] = useState("Construir endpoint de rate limiting por sliding-window com persistencia em SQLite");
  const [missionPlan, setMissionPlan] = useState<PlanStep[] | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);

  const [auditCodeInput, setAuditCodeInput] = useState("def process_request(user_input):\n    # Alerta de seguranca proposital\n    return eval(user_input)\n");
  const [auditResult, setAuditResult] = useState<AuditResponse | null>(null);
  const [isAuditing, setIsAuditing] = useState(false);

  const [healScriptPath, setHealScriptPath] = useState("scripts_brutos/test_api_server.py");
  const [healResult, setHealResult] = useState<SelfHealingResponse | null>(null);
  const [isHealing, setIsHealing] = useState(false);
  const [terminalOutput, setTerminalOutput] = useState<string>("");

  // Multi-Session Management
  const DEFAULT_INITIAL_MSG: ChatMessage = {
    role: "model",
    content: "Império Mutante Online. Base vetorial conectada com embeddings de 3072 dimensões. Digite sua consulta estratégica.",
  };

  function createNewSession(title = "Nova Conversa"): ChatSession {
    return {
      id: "session_" + Date.now(),
      title,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [DEFAULT_INITIAL_MSG],
      lastSources: [],
    };
  }

  // Carrega sessões do localStorage na montagem
  useEffect(() => {
    try {
      const stored = localStorage.getItem("mutante_chat_sessions_v1");
      if (stored) {
        const parsed: ChatSession[] = JSON.parse(stored);
        if (parsed.length > 0) {
          setSessions(parsed);
          const activeId = localStorage.getItem("mutante_active_session_id") || parsed[0].id;
          const found = parsed.find((s) => s.id === activeId) || parsed[0];
          setActiveSessionId(found.id);
          setMessages(found.messages);
          setLastSources(found.lastSources || []);
          return;
        }
      }
    } catch (e) {
      console.error(e);
    }
    const initial = createNewSession("Estratégia Inicial");
    setSessions([initial]);
    setActiveSessionId(initial.id);
    setMessages(initial.messages);
    try {
      localStorage.setItem("mutante_chat_sessions_v1", JSON.stringify([initial]));
      localStorage.setItem("mutante_active_session_id", initial.id);
    } catch {}
  }, []);

  function saveSessionsToStorage(updated: ChatSession[]) {
    setSessions(updated);
    try {
      localStorage.setItem("mutante_chat_sessions_v1", JSON.stringify(updated));
    } catch (e) {
      console.error(e);
    }
  }

  function handleNewChat() {
    const fresh = createNewSession(`Conversa #${sessions.length + 1}`);
    const updated = [fresh, ...sessions];
    saveSessionsToStorage(updated);
    setActiveSessionId(fresh.id);
    setMessages(fresh.messages);
    setLastSources([]);
    try {
      localStorage.setItem("mutante_active_session_id", fresh.id);
    } catch {}
  }

  function handleSelectSession(sessionId: string) {
    if (sessionId === activeSessionId) return;
    const target = sessions.find((s) => s.id === sessionId);
    if (!target) return;
    setActiveSessionId(target.id);
    setMessages(target.messages);
    setLastSources(target.lastSources || []);
    try {
      localStorage.setItem("mutante_active_session_id", target.id);
    } catch {}
  }

  function handleDeleteSession(sessionId: string, e: React.MouseEvent) {
    e.stopPropagation();
    const filtered = sessions.filter((s) => s.id !== sessionId);
    if (filtered.length === 0) {
      const fresh = createNewSession("Nova Conversa");
      saveSessionsToStorage([fresh]);
      setActiveSessionId(fresh.id);
      setMessages(fresh.messages);
      setLastSources([]);
      try {
        localStorage.setItem("mutante_active_session_id", fresh.id);
      } catch {}
    } else {
      saveSessionsToStorage(filtered);
      if (activeSessionId === sessionId) {
        setActiveSessionId(filtered[0].id);
        setMessages(filtered[0].messages);
        setLastSources(filtered[0].lastSources || []);
        try {
          localStorage.setItem("mutante_active_session_id", filtered[0].id);
        } catch {}
      }
    }
  }

  function handleExportMarkdown() {
    const currentSession = sessions.find((s) => s.id === activeSessionId);
    const title = currentSession ? currentSession.title : "Conversa Imperio Mutante";
    const dateStr = new Date().toLocaleString("pt-BR");

    let md = `# ${title}\n\n`;
    md += `*Exportado em: ${dateStr}*\n\n---\n\n`;

    messages.forEach((m) => {
      const role = m.role === "user" ? "### 👤 Operador" : "### ⚡ Agente Mutante (RAG)";
      md += `${role}\n\n${m.content}\n\n`;
    });

    if (lastSources && lastSources.length > 0) {
      md += `\n---\n### 📚 Fontes Citadas (RAG)\n\n`;
      lastSources.forEach((s) => {
        md += `- **${s.title}** (\`${s.source_file}\`) - Similaridade: ${(s.score * 100).toFixed(1)}%\n`;
      });
    }

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/[^a-z0-9]/gi, "_")}_transcricao.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Check API Health & Swarm Status
  useEffect(() => {
    checkHealth();
    loadSwarmStatus();
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
      loadBillingOrders();
    } else if (activeTab === "swarm") {
      loadSwarmStatus();
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

  async function loadBillingOrders() {
    try {
      const data = await api.getBillingOrders();
      setOrders(data);
    } catch (e) {
      console.error(e);
    }
  }

  function handleOpenCheckout(tier: "PRO" | "ENTERPRISE", amount: number) {
    setCheckoutTier(tier);
    setCheckoutAmount(amount);
    setPaymentCompletedKey(null);
    setIsCheckoutOpen(true);
  }

  async function handleConfirmPayment(e: React.FormEvent) {
    e.preventDefault();
    if (!checkoutCustomerEmail.trim()) {
      alert("Informe seu e-mail para receber a licença.");
      return;
    }
    setIsProcessingPayment(true);
    try {
      const paymentRef = `pay_${paymentMethod}_${Date.now()}`;
      const res = await api.provisionLicense({
        customer_email: checkoutCustomerEmail.trim(),
        customer_name: checkoutCustomerName.trim() || checkoutCustomerEmail.split("@")[0],
        tier: checkoutTier,
        payment_reference: paymentRef,
        amount_paid: checkoutAmount,
      });

      setPaymentCompletedKey(res.api_key);
      setActiveApiKey(res.api_key);
      await loadBillingOrders();
    } catch (err: any) {
      alert(`Falha no checkout: ${err.message}`);
    } finally {
      setIsProcessingPayment(false);
    }
  }

  async function loadSwarmStatus() {
    try {
      const data = await api.getSwarmStatus();
      setSwarmStatus(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleSendMessage(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isSending) return;

    const userText = inputMessage.trim();
    setInputMessage("");

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
          // Atualiza fontes na sessão ativa
          setSessions((prev) => {
            const updated = prev.map((s) => s.id === activeSessionId ? { ...s, lastSources: meta.sources || [] } : s);
            return updated;
          });
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
          // Persiste histórico na sessão ativa
          setMessages((finalMsgs) => {
            setSessions((prevSess) => {
              const updated = prevSess.map((s) => {
                if (s.id === activeSessionId) {
                  const autoTitle =
                    s.title.startsWith("Conversa #") || s.title === "Nova Conversa" || s.title === "Estratégia Inicial"
                      ? userText.slice(0, 36)
                      : s.title;
                  return {
                    ...s,
                    title: autoTitle,
                    messages: finalMsgs,
                    updatedAt: Date.now(),
                  };
                }
                return s;
              });
              try {
                localStorage.setItem("mutante_chat_sessions_v1", JSON.stringify(updated));
              } catch {}
              return updated;
            });
            return finalMsgs;
          });
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

  async function handleFileUpload(file: File) {
    if (!file) return;
    setIsUploading(true);
    setUploadFeedback(`Enviando e indexando ${file.name}...`);
    try {
      const res = await api.uploadDocument(file, true);
      setUploadFeedback(`✓ ${res.filename} indexado com sucesso (${(res.bytes_saved / 1024).toFixed(1)} KB)`);
      await loadDocuments();
      setTimeout(() => setUploadFeedback(null), 6000);
    } catch (err: any) {
      setUploadFeedback(`✗ Erro no upload: ${err.message}`);
    } finally {
      setIsUploading(false);
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

  async function handlePlanMission(e: React.FormEvent) {
    e.preventDefault();
    if (!missionInput.trim() || isPlanning) return;
    setIsPlanning(true);
    try {
      const res = await api.planSwarmMission(missionInput.trim());
      setMissionPlan(res.plan);
      setTerminalOutput(`[TASK PLANNER] Missão decomposta em ${res.plan.length} etapas atômicas.\n` + JSON.stringify(res.plan, null, 2));
    } catch (err: any) {
      alert(`Falha no planejador: ${err.message}`);
    } finally {
      setIsPlanning(false);
    }
  }

  async function handleAuditCode(e: React.FormEvent) {
    e.preventDefault();
    if (!auditCodeInput.trim() || isAuditing) return;
    setIsAuditing(true);
    try {
      const res = await api.auditCode(auditCodeInput.trim());
      setAuditResult(res);
      setTerminalOutput(
        `[CODE AUDITOR] Análise concluída:\nVálido: ${res.is_valid}\nSeveridade: ${res.severity}\n\nProblemas identificados:\n` +
        (res.issues.length > 0 ? res.issues.map((iss, i) => `  [${i + 1}] ${iss}`).join("\n") : "  Nenhum anti-pattern detectado.")
      );
    } catch (err: any) {
      alert(`Falha na auditoria: ${err.message}`);
    } finally {
      setIsAuditing(false);
    }
  }

  async function handleSelfHeal(e: React.FormEvent) {
    e.preventDefault();
    if (!healScriptPath.trim() || isHealing) return;
    setIsHealing(true);
    setTerminalOutput(`[SWARM ENGINE] Iniciando ciclo de auto-cura no script: ${healScriptPath}...\n`);
    try {
      const res = await api.triggerSelfHealing(healScriptPath.trim(), 3);
      setHealResult(res);
      const logStr = [
        `[STATUS]: ${res.success ? "SUCESSO (CÓDIGO CURADO)" : "FALHA RESIDUAL"}`,
        `[CICLOS DE CURA UTILIZADOS]: ${res.healing_cycles_used}`,
        `--- STDOUT ---`,
        res.final_stdout || "(vazio)",
        `--- STDERR ---`,
        res.final_stderr || "(vazio)"
      ].join("\n");
      setTerminalOutput(logStr);
    } catch (err: any) {
      setTerminalOutput(`[ERRO CRÍTICO NO SWARM]: ${err.message}`);
    } finally {
      setIsHealing(false);
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
      <nav className="border-b border-[#1a1a1a] bg-[#0c0c0c] px-6 flex flex-wrap gap-2">
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

        <button
          onClick={() => {
            setActiveTab("swarm");
            loadSwarmStatus();
          }}
          className={`flex items-center gap-2 px-5 py-3 text-xs uppercase font-bold tracking-wider border-b-2 transition-all ${
            activeTab === "swarm"
              ? "border-purple-500 text-white bg-[#121212]"
              : "border-transparent text-[#666] hover:text-[#bbb]"
          }`}
        >
          <Bot className="w-4 h-4 text-purple-400" />
          [4] Swarm War Room
        </button>
      </nav>

      {/* Main Container */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {/* TAB 1: RAG CHAT STUDIO */}
        {activeTab === "chat" && (
          <div className="flex flex-col lg:flex-row gap-4 h-[740px]">
            {/* 1. Left Sessions Sidebar */}
            {sidebarOpen && (
              <div className="w-full lg:w-64 bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg flex flex-col overflow-hidden shrink-0">
                <div className="p-3 border-b border-[#1f1f1f] space-y-2 bg-[#121212]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white flex items-center gap-1.5 uppercase">
                      <MessageSquare className="w-3.5 h-3.5 text-[#00ff66]" /> SESSÕES ({sessions.length})
                    </span>
                    <button
                      onClick={() => setSidebarOpen(false)}
                      title="Recolher barra lateral"
                      className="text-[#666] hover:text-white"
                    >
                      <PanelLeftClose className="w-4 h-4" />
                    </button>
                  </div>
                  <button
                    onClick={handleNewChat}
                    className="w-full bg-[#181818] hover:bg-[#222] border border-[#2a2a2a] hover:border-[#00ff66]/40 text-white font-bold py-2 rounded text-xs flex items-center justify-center gap-1.5 transition"
                  >
                    <Plus className="w-3.5 h-3.5 text-[#00ff66]" /> Nova Conversa
                  </button>
                </div>

                {/* Sessions List */}
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {sessions.map((sess) => (
                    <div
                      key={sess.id}
                      onClick={() => handleSelectSession(sess.id)}
                      className={`group p-2.5 rounded text-xs cursor-pointer flex items-center justify-between transition ${
                        sess.id === activeSessionId
                          ? "bg-[#181818] border border-[#2e2e2e] text-[#00ff66]"
                          : "text-[#888] hover:bg-[#121212] hover:text-[#ccc]"
                      }`}
                    >
                      <div className="truncate flex-1 pr-2">
                        <div className="font-bold truncate text-[11px]">{sess.title}</div>
                        <div className="text-[9px] text-[#555] font-mono mt-0.5">
                          {new Date(sess.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {sess.messages.length} msgs
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(sess.id, e)}
                        title="Excluir conversa"
                        className="opacity-0 group-hover:opacity-100 text-[#555] hover:text-red-400 p-1 transition"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Sidebar Footer: Export */}
                <div className="p-2.5 border-t border-[#1f1f1f] bg-[#090909]">
                  <button
                    onClick={handleExportMarkdown}
                    className="w-full bg-[#121212] hover:bg-[#1a1a1a] border border-[#262626] text-[#aaa] hover:text-white py-1.5 rounded text-[11px] flex items-center justify-center gap-1.5 transition"
                  >
                    <Download className="w-3.5 h-3.5 text-[#00e5ff]" /> Exportar Chat (.md)
                  </button>
                </div>
              </div>
            )}

            {/* 2. Center: Chat Window */}
            <div className="flex-1 bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-3 border-b border-[#1f1f1f] bg-[#121212] flex justify-between items-center text-xs">
                <div className="flex items-center gap-3">
                  {!sidebarOpen && (
                    <button
                      onClick={() => setSidebarOpen(true)}
                      title="Expandir sessões"
                      className="text-[#666] hover:text-white"
                    >
                      <PanelLeft className="w-4 h-4 text-[#00ff66]" />
                    </button>
                  )}
                  <span className="text-white font-bold flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-[#00ff66]" />
                    {sessions.find((s) => s.id === activeSessionId)?.title || "CANAL CONVERSACIONAL DIRETO"}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleExportMarkdown}
                    title="Exportar Markdown"
                    className="text-[#666] hover:text-[#00e5ff] text-[11px] flex items-center gap-1"
                  >
                    <Download className="w-3 h-3" /> Exportar .md
                  </button>
                  <span className="text-[#555] hidden sm:inline">MODELO: gemini-2.5-flash</span>
                </div>
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

            {/* 3. Right: Sources & Telemetry */}
            <div className="w-full lg:w-72 bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-4 flex flex-col justify-between shrink-0">
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

              {/* Direct File Upload (Drag & Drop Zone) */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFileUpload(e.dataTransfer.files[0]);
                  }
                }}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-all ${
                  isDragging
                    ? "border-[#00ff66] bg-[#00ff66]/10"
                    : "border-[#252525] hover:border-[#00e5ff]/50 bg-[#090909]"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md,.markdown,.json,.csv"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                />
                <div className="flex flex-col items-center justify-center space-y-1.5">
                  <div className="w-9 h-9 rounded-full bg-[#141414] flex items-center justify-center border border-[#222]">
                    {isUploading ? (
                      <RefreshCw className="w-4 h-4 text-[#00e5ff] animate-spin" />
                    ) : (
                      <UploadCloud className="w-4 h-4 text-[#00e5ff]" />
                    )}
                  </div>
                  <div className="text-xs font-bold text-white uppercase tracking-wider">
                    {isUploading ? "PROCESSANDO & INDEXANDO..." : "ARRASTE E SOLTE ARQUIVOS OU CLIQUE PARA ENVIAR"}
                  </div>
                  <p className="text-[10px] text-[#666]">
                    Suporta PDF, Markdown (.md), Texto (.txt), JSON e CSV — Síntese Gemini + Embeddings 3072-d instantâneos
                  </p>
                  {uploadFeedback && (
                    <div className="mt-1 text-xs font-mono font-bold text-[#00ff66] bg-[#00ff66]/10 px-3 py-1 rounded border border-[#00ff66]/30">
                      {uploadFeedback}
                    </div>
                  )}
                </div>
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

                  {tierName === "PRO" && (
                    <button
                      onClick={() => handleOpenCheckout("PRO", 97)}
                      className="w-full mt-3 bg-[#00e5ff] hover:bg-[#00ccee] text-black font-bold py-2 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition"
                    >
                      <ShoppingBag className="w-3.5 h-3.5" /> Adquirir Licença PRO (R$ 97/mês)
                    </button>
                  )}

                  {tierName === "ENTERPRISE" && (
                    <button
                      onClick={() => handleOpenCheckout("ENTERPRISE", 497)}
                      className="w-full mt-3 bg-amber-400 hover:bg-amber-500 text-black font-bold py-2 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition"
                    >
                      <ShoppingBag className="w-3.5 h-3.5" /> Adquirir Licença ENTERPRISE (R$ 497/mês)
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Instant Key Issuance Gateway */}
            <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-6 space-y-4">
              <h3 className="text-xs font-bold text-white uppercase border-b border-[#1f1f1f] pb-2">
                Emissão Instantânea de Chave de API Licenciada (Admin Mode)
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

            {/* Financial Audit / Recent Orders Table */}
            <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1f1f1f] pb-2">
                <h3 className="text-xs font-bold text-white uppercase flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-[#00ff66]" /> Auditoria de Vendas & Licenças Emitidas ({orders.length})
                </h3>
                <button
                  onClick={loadBillingOrders}
                  className="text-[11px] text-[#888] hover:text-white flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Atualizar
                </button>
              </div>

              {orders.length === 0 ? (
                <div className="text-xs text-[#555] py-4 text-center">
                  Nenhuma transação registrada ainda no acervo financeiro.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#222] text-[#666]">
                        <th className="pb-2 font-mono">ORDER ID</th>
                        <th className="pb-2">CLIENTE</th>
                        <th className="pb-2">PLANO</th>
                        <th className="pb-2">VALOR</th>
                        <th className="pb-2">STATUS</th>
                        <th className="pb-2">DATA</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#181818]">
                      {orders.slice(0, 8).map((ord, idx) => (
                        <tr key={idx} className="hover:bg-[#121212]">
                          <td className="py-2.5 font-mono text-[10px] text-[#00e5ff]">{ord.order_id}</td>
                          <td className="py-2.5 text-white font-medium">{ord.customer_name || ord.customer_email}</td>
                          <td className="py-2.5">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#171717] text-white border border-[#2a2a2a] font-bold">
                              {ord.tier}
                            </span>
                          </td>
                          <td className="py-2.5 text-[#00ff66] font-bold">
                            {ord.amount_paid ? `R$ ${ord.amount_paid.toFixed(2)}` : "R$ 0,00"}
                          </td>
                          <td className="py-2.5">
                            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-[#00ff66] border border-emerald-800 font-bold">
                              {ord.status}
                            </span>
                          </td>
                          <td className="py-2.5 text-[#666] font-mono text-[10px]">
                            {new Date(ord.timestamp).toLocaleDateString([], { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Modal de Checkout Flutuante */}
            {isCheckoutOpen && (
              <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="bg-[#0d0d0d] border border-[#262626] rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
                  <button
                    onClick={() => setIsCheckoutOpen(false)}
                    className="absolute top-4 right-4 text-[#666] hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>

                  <div className="border-b border-[#1f1f1f] pb-3">
                    <span className="text-[10px] text-[#00ff66] font-bold uppercase tracking-wider">CHECKOUT SEGURO</span>
                    <h3 className="text-base font-bold text-white uppercase mt-0.5">
                      Licença Império Mutante {checkoutTier}
                    </h3>
                    <div className="text-lg text-[#00ff66] font-bold mt-1 font-mono">
                      R$ {checkoutAmount},00 <span className="text-xs text-[#777] font-normal">/ mês</span>
                    </div>
                  </div>

                  {!paymentCompletedKey ? (
                    <form onSubmit={handleConfirmPayment} className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-[11px] text-[#888] uppercase font-bold block">Seus Dados de Acesso:</label>
                        <input
                          type="text"
                          placeholder="Seu Nome Completo"
                          value={checkoutCustomerName}
                          onChange={(e) => setCheckoutCustomerName(e.target.value)}
                          className="w-full bg-[#141414] border border-[#222] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00e5ff]"
                        />
                        <input
                          type="email"
                          placeholder="seu.email@empresa.com"
                          value={checkoutCustomerEmail}
                          onChange={(e) => setCheckoutCustomerEmail(e.target.value)}
                          required
                          className="w-full bg-[#141414] border border-[#222] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00e5ff]"
                        />
                      </div>

                      {/* Escolha de Método de Pagamento */}
                      <div className="space-y-1.5">
                        <label className="text-[11px] text-[#888] uppercase font-bold block">Forma de Pagamento:</label>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={() => setPaymentMethod("pix")}
                            className={`p-2.5 rounded border text-xs font-bold flex items-center justify-center gap-2 transition ${
                              paymentMethod === "pix"
                                ? "bg-[#00ff66]/10 border-[#00ff66] text-[#00ff66]"
                                : "bg-[#141414] border-[#222] text-[#777]"
                            }`}
                          >
                            <QrCode className="w-4 h-4" /> PIX Instantâneo
                          </button>
                          <button
                            type="button"
                            onClick={() => setPaymentMethod("card")}
                            className={`p-2.5 rounded border text-xs font-bold flex items-center justify-center gap-2 transition ${
                              paymentMethod === "card"
                                ? "bg-[#00e5ff]/10 border-[#00e5ff] text-[#00e5ff]"
                                : "bg-[#141414] border-[#222] text-[#777]"
                            }`}
                          >
                            <CreditCard className="w-4 h-4" /> Cartão de Crédito
                          </button>
                        </div>
                      </div>

                      <div className="p-3 bg-[#121212] rounded border border-[#222] text-[11px] text-[#888] space-y-1">
                        <div className="flex justify-between text-white">
                          <span>Aprovisionamento:</span>
                          <span className="text-[#00ff66] font-bold">Imediato (Zero Delay)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Gateway Webhook:</span>
                          <span className="font-mono text-[10px]">Stripe / Mercado Pago</span>
                        </div>
                      </div>

                      <button
                        type="submit"
                        disabled={isProcessingPayment}
                        className="w-full bg-[#00ff66] hover:bg-[#00dd55] text-black font-bold py-3 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition disabled:opacity-50"
                      >
                        {isProcessingPayment ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Processando Transação...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Confirmar Pagamento & Liberar Chave
                          </>
                        )}
                      </button>
                    </form>
                  ) : (
                    <div className="space-y-4 py-2">
                      <div className="bg-emerald-950/40 border border-emerald-600/40 rounded-lg p-4 text-center space-y-2">
                        <CheckCircle className="w-8 h-8 text-[#00ff66] mx-auto animate-bounce" />
                        <h4 className="text-sm font-bold text-white uppercase">Pagamento Aprovado com Sucesso!</h4>
                        <p className="text-xs text-[#aaa]">
                          Sua licença <span className="text-[#00ff66] font-bold">{checkoutTier}</span> foi provisionada e injetada no seu cockpit.
                        </p>
                      </div>

                      <div className="space-y-1">
                        <span className="text-[10px] text-[#777] uppercase font-bold">Sua Chave de API:</span>
                        <div className="bg-[#050505] p-3 rounded text-xs text-[#00ff66] font-mono break-all border border-[#222]">
                          {paymentCompletedKey}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            if (paymentCompletedKey) navigator.clipboard.writeText(paymentCompletedKey);
                            alert("Chave copiada para a área de transferência!");
                          }}
                          className="flex-1 bg-[#1a1a1a] hover:bg-[#252525] text-white font-bold py-2 rounded text-xs uppercase border border-[#333] transition"
                        >
                          Copiar Chave
                        </button>
                        <button
                          onClick={() => setIsCheckoutOpen(false)}
                          className="flex-1 bg-[#00ff66] hover:bg-[#00dd55] text-black font-bold py-2 rounded text-xs uppercase transition"
                        >
                          Concluir
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: SWARM WAR ROOM */}
        {activeTab === "swarm" && (
          <div className="space-y-6">
            {/* Swarm Agents Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-[#0d0d0d] border border-purple-500/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-purple-400" /> TaskPlannerAgent
                  </span>
                  <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded font-bold">
                    ONLINE
                  </span>
                </div>
                <p className="text-[11px] text-[#777]">Decomposição atômica de objetivos e roteirização</p>
                <div className="text-[10px] text-[#555] font-mono">ENGINE: gemini-2.5-flash</div>
              </div>

              <div className="bg-[#0d0d0d] border border-blue-500/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-blue-400" /> CodeAuditorAgent
                  </span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded font-bold">
                    ONLINE
                  </span>
                </div>
                <p className="text-[11px] text-[#777]">Análise estática, vulnerabilidades e anti-patterns</p>
                <div className="text-[10px] text-[#555] font-mono">ENGINE: gemini-2.5-flash</div>
              </div>

              <div className="bg-[#0d0d0d] border border-emerald-500/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <Play className="w-4 h-4 text-emerald-400" /> TestRunnerAgent
                  </span>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-bold">
                    ONLINE
                  </span>
                </div>
                <p className="text-[11px] text-[#777]">Execução em subprocesso e captura stdout/stderr</p>
                <div className="text-[10px] text-[#555] font-mono">RUNTIME: native-python</div>
              </div>

              <div className="bg-[#0d0d0d] border border-amber-500/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <Bug className="w-4 h-4 text-amber-400" /> SelfHealingCore
                  </span>
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded font-bold animate-pulse">
                    ARMED
                  </span>
                </div>
                <p className="text-[11px] text-[#777]">Loop de regeneração de patches com contexto RAG</p>
                <div className="text-[10px] text-[#555] font-mono">CYCLES: 3 Max Auto-Patch</div>
              </div>
            </div>

            {/* Mode Switcher */}
            <div className="flex gap-2 border-b border-[#1f1f1f] pb-3">
              <button
                onClick={() => setSwarmMode("heal")}
                className={`px-4 py-2 text-xs font-bold uppercase rounded transition ${
                  swarmMode === "heal"
                    ? "bg-amber-400 text-black"
                    : "bg-[#141414] text-[#888] hover:text-white"
                }`}
              >
                [A] Self-Healing Engine
              </button>
              <button
                onClick={() => setSwarmMode("plan")}
                className={`px-4 py-2 text-xs font-bold uppercase rounded transition ${
                  swarmMode === "plan"
                    ? "bg-purple-500 text-white"
                    : "bg-[#141414] text-[#888] hover:text-white"
                }`}
              >
                [B] Task Planner
              </button>
              <button
                onClick={() => setSwarmMode("audit")}
                className={`px-4 py-2 text-xs font-bold uppercase rounded transition ${
                  swarmMode === "audit"
                    ? "bg-blue-500 text-white"
                    : "bg-[#141414] text-[#888] hover:text-white"
                }`}
              >
                [C] Code Auditor
              </button>
            </div>

            {/* Dynamic Mission Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Form Controls */}
              <div className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-lg p-5 space-y-4">
                {swarmMode === "heal" && (
                  <form onSubmit={handleSelfHeal} className="space-y-4">
                    <div>
                      <label className="text-xs text-[#888] font-bold uppercase block mb-1.5">
                        Caminho do Script Python para Execução & Auto-Cura:
                      </label>
                      <input
                        type="text"
                        value={healScriptPath}
                        onChange={(e) => setHealScriptPath(e.target.value)}
                        placeholder="scripts_brutos/test_api_server.py"
                        className="w-full bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isHealing}
                      className="w-full bg-amber-400 hover:bg-amber-500 text-black font-bold py-2.5 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      <Bug className="w-4 h-4" />
                      {isHealing ? "Executando e Auto-Curando..." : "Disparar Loop de Auto-Cura"}
                    </button>
                  </form>
                )}

                {swarmMode === "plan" && (
                  <form onSubmit={handlePlanMission} className="space-y-4">
                    <div>
                      <label className="text-xs text-[#888] font-bold uppercase block mb-1.5">
                        Objetivo Estratégico ou Missão Técnica:
                      </label>
                      <textarea
                        rows={4}
                        value={missionInput}
                        onChange={(e) => setMissionInput(e.target.value)}
                        className="w-full bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white focus:outline-none focus:border-purple-400 resize-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isPlanning}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      <Cpu className="w-4 h-4" />
                      {isPlanning ? "Decompondo Missão..." : "Decompor em Checklist Atômico"}
                    </button>
                  </form>
                )}

                {swarmMode === "audit" && (
                  <form onSubmit={handleAuditCode} className="space-y-4">
                    <div>
                      <label className="text-xs text-[#888] font-bold uppercase block mb-1.5">
                        Código-fonte Python para Auditoria Estática:
                      </label>
                      <textarea
                        rows={6}
                        value={auditCodeInput}
                        onChange={(e) => setAuditCodeInput(e.target.value)}
                        className="w-full bg-[#141414] border border-[#222] rounded px-4 py-2.5 text-xs text-white font-mono focus:outline-none focus:border-blue-400 resize-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isAuditing}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      <ShieldAlert className="w-4 h-4" />
                      {isAuditing ? "Auditoria em Andamento..." : "Executar Auditoria de Segurança"}
                    </button>
                  </form>
                )}

                {/* Structured Result Display */}
                {swarmMode === "plan" && missionPlan && (
                  <div className="mt-4 space-y-2 border-t border-[#1f1f1f] pt-4">
                    <h4 className="text-xs font-bold text-purple-400 uppercase">
                      Checklist Decomposto ({missionPlan.length} passos):
                    </h4>
                    <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
                      {missionPlan.map((p, idx) => (
                        <div key={idx} className="bg-[#111] border border-[#222] p-2.5 rounded text-xs">
                          <div className="flex items-center justify-between text-purple-300 font-bold mb-1">
                            <span>Passo {p.step}</span>
                            <span className="text-[10px] text-[#666] font-mono">{p.target_file}</span>
                          </div>
                          <p className="text-[#ccc] text-[11px]">{p.action}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {swarmMode === "audit" && auditResult && (
                  <div className="mt-4 space-y-2 border-t border-[#1f1f1f] pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase">Diagnóstico do Código:</span>
                      <span
                        className={`text-[10px] px-2.5 py-0.5 rounded font-bold uppercase ${
                          auditResult.severity === "HIGH"
                            ? "bg-red-500/20 text-red-400 border border-red-500/40"
                            : auditResult.severity === "MEDIUM"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                        }`}
                      >
                        Severidade: {auditResult.severity}
                      </span>
                    </div>
                    {auditResult.issues.length > 0 ? (
                      <ul className="space-y-1.5 mt-2">
                        {auditResult.issues.map((iss, i) => (
                          <li key={i} className="text-[11px] text-red-300 bg-red-950/20 border border-red-900/40 p-2 rounded flex items-start gap-1.5">
                            <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
                            <span>{iss}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-emerald-400 bg-emerald-950/20 border border-emerald-900/40 p-3 rounded flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" /> Nenhum anti-pattern crítico detectado.
                      </div>
                    )}
                  </div>
                )}

                {swarmMode === "heal" && healResult && (
                  <div className="mt-4 space-y-2 border-t border-[#1f1f1f] pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase">Resultado do Self-Healing:</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                          healResult.success ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {healResult.success ? "REPARADO COM SUCESSO" : "FALHA RESIDUAL"}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#888]">
                      Ciclos executados: <span className="text-white font-bold">{healResult.healing_cycles_used}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Interactive Vantablack Terminal Console */}
              <div className="bg-[#050505] border border-[#222] rounded-lg overflow-hidden flex flex-col h-[540px]">
                <div className="px-4 py-2.5 bg-[#0e0e0e] border-b border-[#222] flex items-center justify-between text-xs">
                  <span className="text-[#888] font-bold flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-[#00ff66]" />
                    SUBPROCESS & ENGINE CONSOLE
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setTerminalOutput("")}
                      className="text-[10px] text-[#666] hover:text-[#bbb] uppercase"
                    >
                      Limpar
                    </button>
                    <button
                      onClick={() => {
                        if (terminalOutput) navigator.clipboard.writeText(terminalOutput);
                      }}
                      className="text-[10px] text-[#00e5ff] hover:underline uppercase"
                    >
                      Copiar
                    </button>
                  </div>
                </div>

                <div className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-2 selection:bg-purple-900 selection:text-white">
                  <div className="text-[#555]">// Sessão terminal do Enxame Império Mutante ativa.</div>
                  {terminalOutput ? (
                    <pre className="text-[#00ff66] whitespace-pre-wrap leading-relaxed">
                      {terminalOutput}
                    </pre>
                  ) : (
                    <div className="text-[#444] italic mt-4">
                      Aguardando disparo de missão, auditoria ou auto-cura...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

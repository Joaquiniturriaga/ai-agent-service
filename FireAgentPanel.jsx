import { useState, useRef, useEffect, useCallback } from "react";
import "./FireAgentPanel.css";

const GW = import.meta.env.VITE_GATEWAY_URL || "http://localhost:10000";

const RISK_COLOR = { BAJO: "#22c55e", MODERADO: "#eab308", ALTO: "#f97316", EXTREMO: "#dc2626" };
const RISK_BG    = { BAJO: "#f0fdf4", MODERADO: "#fefce8", ALTO: "#fff7ed", EXTREMO: "#fef2f2" };

const QUICK = [
  "¿Cuál es el riesgo de incendio en la zona hoy?",
  "¿Qué brigadas están disponibles?",
  "¿Hay reportes activos?",
  "¿Hay unidades en campo?",
  "Análisis completo de situación",
];

// ── helpers ─────────────────────────────────────────────────────────────────
function RiskBadge({ level }) {
  if (!level || level === "DESCONOCIDO") return null;
  return (
    <span className="fap-badge" style={{
      background: RISK_BG[level] || "#f8fafc",
      color: RISK_COLOR[level] || "#64748b",
      border: `1px solid ${RISK_COLOR[level] || "#e2e8f0"}`,
    }}>
      {level}
    </span>
  );
}

function MetricCard({ icon, label, value, sub }) {
  return (
    <div className="fap-metric-card">
      <span className="fap-metric-icon">{icon}</span>
      <div>
        <p className="fap-metric-label">{label}</p>
        <p className="fap-metric-value">{value ?? "—"}</p>
        {sub && <p className="fap-metric-sub">{sub}</p>}
      </div>
    </div>
  );
}

// ── componente principal ────────────────────────────────────────────────────
export default function FireAgentPanel({ token }) {
  const [tab, setTab]         = useState("chat");   // "chat" | "metrics"
  const [messages, setMessages] = useState([{
    role: "assistant",
    content: "Hola, soy el Agente de Riesgo de Valle del Sol. Puedo evaluar condiciones climáticas, consultar brigadas, revisar emergencias activas y registrar nuevas alertas. ¿En qué te ayudo?",
  }]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [mLoading, setMLoading] = useState(false);
  const [mError, setMError]   = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── fetch metrics ──────────────────────────────────────────────────────
  const fetchMetrics = useCallback(async () => {
    setMLoading(true); setMError(null);
    try {
      const r = await fetch(`${GW}/api/agent/metrics/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setMetrics(await r.json());
    } catch (e) {
      setMError(e.message);
    } finally {
      setMLoading(false);
    }
  }, [token]);

  useEffect(() => { if (tab === "metrics") fetchMetrics(); }, [tab, fetchMetrics]);

  // ── send chat ──────────────────────────────────────────────────────────
  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    const updated = [...messages, { role: "user", content: msg }];
    setMessages(updated); setInput(""); setLoading(true);
    try {
      const r = await fetch(`${GW}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          message: msg,
          history: messages.slice(-10).map(({ role, content }) => ({ role, content })),
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch (e) {
      setMessages([...updated, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally { setLoading(false); }
  };

  // ── render ─────────────────────────────────────────────────────────────
  return (
    <div className="fap-root">
      {/* Header */}
      <div className="fap-header">
        <span className="fap-header-icon">🔥</span>
        <div>
          <h2 className="fap-title">Agente de Riesgo</h2>
          <span className="fap-subtitle">Valle del Sol · IA Operacional</span>
        </div>
        <div className="fap-online"><span className="fap-dot" />En línea</div>
      </div>

      {/* Tabs */}
      <div className="fap-tabs">
        <button className={`fap-tab ${tab === "chat" ? "fap-tab--active" : ""}`} onClick={() => setTab("chat")}>
          💬 Agente
        </button>
        <button className={`fap-tab ${tab === "metrics" ? "fap-tab--active" : ""}`} onClick={() => setTab("metrics")}>
          📊 Métricas
        </button>
      </div>

      {/* ── TAB: CHAT ── */}
      {tab === "chat" && (
        <>
          <div className="fap-quickrow">
            {QUICK.map(q => (
              <button key={q} className="fap-qbtn" onClick={() => send(q)} disabled={loading}>{q}</button>
            ))}
          </div>
          <div className="fap-messages">
            {messages.map((m, i) => {
              const risk = m.role === "assistant" ? (m.content.match(/\b(EXTREMO|ALTO|MODERADO|BAJO)\b/)?.[0]) : null;
              return (
                <div key={i} className={`fap-msg fap-msg--${m.role}`}>
                  {risk && <RiskBadge level={risk} />}
                  <div className={`fap-bubble fap-bubble--${m.role}`}>
                    {m.content.split("\n").map((l, j) => <span key={j}>{l}<br /></span>)}
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="fap-msg fap-msg--assistant">
                <div className="fap-bubble fap-bubble--assistant fap-bubble--loading">
                  <span className="fap-dot-anim" /><span className="fap-dot-anim" style={{animationDelay:"0.2s"}} /><span className="fap-dot-anim" style={{animationDelay:"0.4s"}} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <div className="fap-inputrow">
            <textarea className="fap-input" value={input} rows={2} disabled={loading}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="Escribe tu consulta... (Enter para enviar)" />
            <button className="fap-send" onClick={() => send()} disabled={loading || !input.trim()}>↑</button>
          </div>
        </>
      )}

      {/* ── TAB: MÉTRICAS ── */}
      {tab === "metrics" && (
        <div className="fap-metrics">
          <div className="fap-metrics-header">
            <span className="fap-metrics-ts">{metrics ? `Actualizado: ${new Date(metrics.timestamp).toLocaleTimeString("es-CL")}` : ""}</span>
            <button className="fap-refresh" onClick={fetchMetrics} disabled={mLoading}>
              {mLoading ? "Cargando..." : "↻ Actualizar"}
            </button>
          </div>

          {mError && <p className="fap-error">Error: {mError}</p>}

          {metrics && (
            <>
              {/* Clima */}
              <div className="fap-section">
                <h3 className="fap-section-title">🌡 Clima · {metrics.zona_referencia}</h3>
                <div className="fap-metric-grid">
                  <MetricCard icon="🌡" label="Temperatura" value={`${metrics.clima.temperatura}°C`} />
                  <MetricCard icon="💧" label="Humedad" value={`${metrics.clima.humedad}%`} />
                  <MetricCard icon="💨" label="Viento" value={`${metrics.clima.viento} km/h`} />
                  <MetricCard icon="🌧" label="Precip 24h" value={`${metrics.clima.precipitacion_24h} mm`} />
                </div>
                <div className="fap-risk-row">
                  <span className="fap-risk-label">Nivel de riesgo:</span>
                  <RiskBadge level={metrics.clima.nivel_riesgo} />
                  <span className="fap-risk-score">Score: {metrics.clima.score}/11</span>
                </div>
              </div>

              {/* Operacional */}
              <div className="fap-section">
                <h3 className="fap-section-title">🚒 Situación operacional</h3>
                <div className="fap-metric-grid">
                  <MetricCard icon="🏕" label="Brigadas activas" value={metrics.brigadas.activas} sub={`de ${metrics.brigadas.total} totales`} />
                  <MetricCard icon="🔥" label="Reportes activos" value={metrics.reportes.activos} sub={`de ${metrics.reportes.total} totales`} />
                  <MetricCard icon="🚒" label="Unidades en campo" value={metrics.unidades_desplegadas.total} />
                  <MetricCard icon="🔔" label="Alertas pendientes" value={metrics.alertas.pendientes} sub={`de ${metrics.alertas.total} totales`} />
                </div>
              </div>

              {/* Reportes activos */}
              {metrics.reportes.ultimos_activos?.length > 0 && (
                <div className="fap-section">
                  <h3 className="fap-section-title">📋 Reportes activos recientes</h3>
                  <div className="fap-report-list">
                    {metrics.reportes.ultimos_activos.map(r => (
                      <div key={r.id} className="fap-report-item">
                        <span className="fap-report-tipo">{r.tipo}</span>
                        <span className="fap-report-title">{r.title}</span>
                        <span className="fap-report-date">{r.created_at ? new Date(r.created_at).toLocaleString("es-CL", {dateStyle:"short", timeStyle:"short"}) : "—"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tipos de reporte */}
              {Object.keys(metrics.reportes.por_tipo).length > 0 && (
                <div className="fap-section">
                  <h3 className="fap-section-title">📊 Reportes por tipo</h3>
                  <div className="fap-tipo-grid">
                    {Object.entries(metrics.reportes.por_tipo).map(([tipo, count]) => (
                      <div key={tipo} className="fap-tipo-item">
                        <span className="fap-tipo-name">{tipo}</span>
                        <span className="fap-tipo-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {mLoading && !metrics && (
            <div className="fap-loading-state">
              <div className="fap-spinner" />
              <p>Consultando microservicios...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
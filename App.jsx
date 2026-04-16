import { useState, useEffect, useRef, useCallback } from "react";

const GlobalStyle = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

    :root {
      --bg: #060608;
      --surface: #0d0d12;
      --surface2: #13131a;
      --border: #1e1e2a;
      --border2: #2a2a3a;
      --text: #e8e8f0;
      --muted: #5a5a72;
      --accent: #ff3b3b;
      --accent2: #ff6b3b;
      --safe: #00e5a0;
      --warn: #ffd600;
      --info: #3b8fff;
      --glow: rgba(255,59,59,0.15);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'JetBrains Mono', monospace;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--surface); }
    ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

    input, button { font-family: inherit; }

    @keyframes pulse-red {
      0%, 100% { box-shadow: 0 0 0 0 rgba(255,59,59,0.4); }
      50% { box-shadow: 0 0 0 8px rgba(255,59,59,0); }
    }
    @keyframes scan {
      0% { transform: translateY(-100%); }
      100% { transform: translateY(100vh); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(-12px); }
      to { opacity: 1; transform: translateX(0); }
    }
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
    @keyframes progressPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    @keyframes toastIn {
      from { opacity: 0; transform: translateX(120%); }
      to { opacity: 1; transform: translateX(0); }
    }
    @keyframes toastOut {
      from { opacity: 1; transform: translateX(0); }
      to { opacity: 0; transform: translateX(120%); }
    }

    .fade-in { animation: fadeIn 0.4s ease forwards; }
    .slide-in { animation: slideIn 0.3s ease forwards; }
  `}</style>
);

const API = "http://localhost:8000/api";

const DISASTER_COLORS = {
  "Fire Disaster":         "#ff3b3b",
  "Damaged Infrastructure":"#ff8c3b",
  "Human Damage":          "#ff3b8c",
  "Land Disaster":         "#c47b3b",
  "Water Disaster":        "#3b8fff",
  "Non-Damage":            "#00e5a0",
};

const SEVERITY_COLORS = {
  CRITICAL: "#ff3b3b",
  HIGH:     "#ff6b3b",
  MEDIUM:   "#ffd600",
  LOW:      "#3b8fff",
};

const Badge = ({ label, color }) => (
  <span style={{
    display: "inline-block",
    padding: "2px 8px",
    background: `${color}22`,
    color,
    border: `1px solid ${color}44`,
    borderRadius: 3,
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
  }}>{label}</span>
);

const Dot = ({ active, color = "#00e5a0" }) => (
  <span style={{
    display: "inline-block",
    width: 7, height: 7,
    borderRadius: "50%",
    background: active ? color : "#333",
    boxShadow: active ? `0 0 6px ${color}` : "none",
    animation: active ? "blink 1.4s infinite" : "none",
    flexShrink: 0,
  }} />
);

const ConfBar = ({ value, color }) => (
  <div style={{ position: "relative", height: 4, background: "#1a1a22", borderRadius: 2, overflow: "hidden" }}>
    <div style={{
      position: "absolute", left: 0, top: 0, bottom: 0,
      width: `${(value * 100).toFixed(1)}%`,
      background: color,
      borderRadius: 2,
      transition: "width 0.5s ease",
    }} />
  </div>
);

const Toast = ({ toasts }) => (
  <div style={{ position: "fixed", top: 20, right: 20, zIndex: 9999, display: "flex", flexDirection: "column", gap: 10 }}>
    {toasts.map(t => (
      <div key={t.id} style={{
        padding: "14px 18px",
        background: "#0d0d12",
        border: `1px solid ${t.type === "alert" ? "#ff3b3b" : "#00e5a0"}44`,
        borderLeft: `3px solid ${t.type === "alert" ? "#ff3b3b" : "#00e5a0"}`,
        borderRadius: 6,
        maxWidth: 320,
        animation: t.out ? "toastOut 0.3s ease forwards" : "toastIn 0.3s ease forwards",
        boxShadow: `0 4px 24px rgba(0,0,0,0.6)`,
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: t.type === "alert" ? "#ff3b3b" : "#00e5a0", letterSpacing: 1, marginBottom: 4 }}>
          {t.type === "alert" ? "🚨 DISASTER ALERT" : "✓ SYSTEM"}
        </div>
        <div style={{ fontSize: 12, color: "#c0c0d0", lineHeight: 1.5 }}>{t.message}</div>
      </div>
    ))}
  </div>
);

const AuthPage = ({ onLogin }) => {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = async () => {
    setError(""); setLoading(true);
    try {
      const url = mode === "login" ? `${API}/login` : `${API}/register`;
      const body = mode === "login"
        ? { email: form.email, password: form.password }
        : { email: form.email, password: form.password, name: form.name };

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Auth failed");
      onLogin(data.session_id, data.user);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "var(--bg)",
      backgroundImage: "radial-gradient(ellipse 60% 40% at 50% 0%, #1a0808 0%, transparent 70%)",
    }}>
      <div className="fade-in" style={{ width: 380 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 13, letterSpacing: 6, color: "var(--muted)", textTransform: "uppercase", marginBottom: 10 }}>
            DISASTER.INTEL
          </div>
          <div style={{ fontSize: 32, fontFamily: "Syne, sans-serif", fontWeight: 800, lineHeight: 1 }}>
            <span style={{ color: "#ff3b3b" }}>⬡</span> SENTINEL
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 6 }}>Real-Time Disaster Detection System</div>
        </div>

        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 28,
        }}>
          <div style={{ display: "flex", gap: 0, marginBottom: 24, background: "var(--bg)", borderRadius: 5, padding: 3 }}>
            {["login", "register"].map(m => (
              <button key={m} onClick={() => setMode(m)} style={{
                flex: 1, padding: "8px 0", background: mode === m ? "var(--surface2)" : "transparent",
                border: mode === m ? "1px solid var(--border2)" : "1px solid transparent",
                borderRadius: 4, color: mode === m ? "var(--text)" : "var(--muted)",
                fontSize: 11, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", cursor: "pointer",
                transition: "all 0.2s",
              }}>{m}</button>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {mode === "register" && (
              <input
                placeholder="Full Name"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                style={inputStyle}
              />
            )}
            <input
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              style={inputStyle}
            />
            <input
              placeholder="Password"
              type="password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              style={inputStyle}
              onKeyDown={e => e.key === "Enter" && handle()}
            />

            {error && (
              <div style={{ fontSize: 11, color: "#ff3b3b", padding: "8px 10px", background: "#ff3b3b11", borderRadius: 4, border: "1px solid #ff3b3b22" }}>
                {error}
              </div>
            )}

            <button onClick={handle} disabled={loading} style={{
              marginTop: 4, padding: "12px 0",
              background: loading ? "var(--surface2)" : "#ff3b3b",
              border: "none", borderRadius: 5,
              color: "#fff", fontSize: 12, fontWeight: 700, letterSpacing: 2,
              textTransform: "uppercase", cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}>
              {loading ? "CONNECTING..." : mode === "login" ? "ENTER SYSTEM" : "CREATE ACCOUNT"}
            </button>
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 10, color: "var(--muted)" }}>
          SENTINEL v2.4 · ANTHROPIC INFRASTRUCTURE
        </div>
      </div>
    </div>
  );
};

const inputStyle = {
  width: "100%", padding: "10px 12px",
  background: "var(--bg)", border: "1px solid var(--border2)",
  borderRadius: 5, color: "var(--text)", fontSize: 12,
  outline: "none", transition: "border 0.2s",
};

const Dashboard = ({ session, user, onLogout, pushToast }) => {
  const [videoId, setVideoId]         = useState(null);
  const [videoURL, setVideoURL]       = useState(null);
  const [status, setStatus]           = useState(null);    
  const [predictions, setPredictions] = useState([]);
  const [alerts, setAlerts]           = useState([]);
  const [activeClass, setActiveClass] = useState(null);
  const [activeConf, setActiveConf]   = useState(0);
  const [activeTs, setActiveTs]       = useState(0);
  const [uploading, setUploading]     = useState(false);
  const [seenAlerts, setSeenAlerts]   = useState(new Set());
  const pollRef  = useRef(null);
  const fileRef  = useRef();

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    const fileList = Array.from(files);
    
    setUploading(true);
    setPredictions([]); setAlerts([]); setVideoId(null); setStatus(null);
    setActiveClass(null); setSeenAlerts(new Set());

    setVideoURL(URL.createObjectURL(fileList[0]));

    const fd = new FormData();
    fileList.forEach(file => fd.append("files", file));

    try {
      const res = await fetch(`${API}/upload-media?session_id=${session}`, {
        method: "POST", body: fd,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setVideoId(data.video_id);
      setStatus({ status: "processing", progress: 0 });
    } catch (e) {
      pushToast("error", e.message);
    } finally {
      setUploading(false);
    }
  };

  const poll = useCallback(async (vid) => {
    try {
      const sRes = await fetch(`${API}/process-status/${vid}`);
      const s = await sRes.json();
      setStatus(s);

      if (s.status === "completed" || s.progress > 20) {
        const pRes = await fetch(`${API}/predictions/${vid}`);
        const pData = await pRes.json();
        if (pData.predictions?.length) {
          setPredictions(pData.predictions);
          const disasterFailsafe = [...pData.predictions]
            .filter(p => p.class_name !== "Non-Damage")
            .sort((a,b) => b.confidence - a.confidence)[0];
            
          const last = pData.predictions[pData.predictions.length - 1];
          const best = disasterFailsafe || last;
          
          setActiveClass(best.class_name);
          setActiveConf(best.confidence);
          setActiveTs(best.timestamp);
        }
      }

      if (s.status === "completed") {
        const aRes = await fetch(`${API}/alerts/${vid}`);
        const aData = await aRes.json();
        if (aData.alerts?.length) {
          setAlerts(aData.alerts);

          aData.alerts.forEach(a => {
            if (!seenAlerts.has(a.alert_id)) {
              pushToast("alert", `${a.disaster_type} detected at ${a.start_timestamp}s (${(a.confidence * 100).toFixed(0)}% confidence)`);
              setSeenAlerts(prev => new Set([...prev, a.alert_id]));
            }
          });
        }
        clearInterval(pollRef.current);
      }
    } catch {}
  }, [seenAlerts, pushToast]);

  useEffect(() => {
    if (!videoId) return;
    pollRef.current = setInterval(() => poll(videoId), 2000);
    return () => clearInterval(pollRef.current);
  }, [videoId, poll]);

  const isDanger = activeClass && activeClass !== "Non-Damage";
  const disasterColor = activeClass ? DISASTER_COLORS[activeClass] : "var(--muted)";

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Top bar */}
      <header style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 24px",
        background: "var(--surface)",
        borderBottom: "1px solid var(--border)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontFamily: "Syne", fontWeight: 800, fontSize: 16 }}>
            <span style={{ color: "#ff3b3b" }}>⬡</span> SENTINEL
          </span>
          <span style={{ color: "var(--muted)", fontSize: 10, letterSpacing: 3 }}>DISASTER INTEL</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Dot active={!!videoId && status?.status === "processing"} color="#ffd600" />
          <span style={{ fontSize: 11, color: "var(--muted)" }}>{user.email}</span>
          <button onClick={onLogout} style={{
            padding: "5px 12px", background: "transparent", border: "1px solid var(--border2)",
            borderRadius: 4, color: "var(--muted)", fontSize: 10, letterSpacing: 1, cursor: "pointer",
          }}>LOGOUT</button>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 1, minHeight: "calc(100vh - 49px)" }}>

        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>

          <UploadZone onFile={handleUpload} uploading={uploading} fileRef={fileRef} />

          {videoURL && (
            <div className="fade-in" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Panel title="VIDEO FEED">
                <video src={videoURL} controls style={{ width: "100%", borderRadius: 4, maxHeight: 200, objectFit: "cover" }} />
              </Panel>
              <Panel title="PROCESSING STATUS">
                <StatusPanel status={status} />
              </Panel>
            </div>
          )}

          {activeClass && (
            <div className="fade-in">
              <Panel title="LIVE ANALYSIS" accent={isDanger ? "#ff3b3b" : "#00e5a0"}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                  <StatBox label="CLASS DETECTED" value={activeClass} color={disasterColor} big />
                  <StatBox label="CONFIDENCE" value={`${(activeConf * 100).toFixed(1)}%`} color={disasterColor} big />
                  <StatBox label="TIMESTAMP" value={`${activeTs.toFixed(2)}s`} color="var(--info)" big />
                </div>
                <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 8 }}>
                  <Dot active color={isDanger ? "#ff3b3b" : "#00e5a0"} />
                  <Badge label={isDanger ? "DANGER" : "SAFE"} color={isDanger ? "#ff3b3b" : "#00e5a0"} />
                  <ConfBar value={activeConf} color={disasterColor} />
                </div>
              </Panel>
            </div>
          )}

          {predictions.length > 0 && (
            <div className="fade-in">
              <Panel title={`FRAME PREDICTIONS  [${predictions.length}]`}>
                <PredictionTimeline predictions={predictions} />
              </Panel>
            </div>
          )}
        </div>

        <div style={{
          borderLeft: "1px solid var(--border)",
          background: "var(--surface)",
          padding: 20,
          display: "flex", flexDirection: "column", gap: 12,
          overflowY: "auto", maxHeight: "calc(100vh - 49px)",
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: "var(--muted)" }}>
              ALERT PANEL
            </div>
            {alerts.length > 0 && (
              <Badge label={`${alerts.length} ACTIVE`} color="#ff3b3b" />
            )}
          </div>

          {alerts.length === 0 ? (
            <div style={{
              flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", color: "var(--muted)", gap: 10, paddingTop: 60,
            }}>
              <div style={{ fontSize: 32 }}>◌</div>
              <div style={{ fontSize: 11, letterSpacing: 1 }}>NO ALERTS DETECTED</div>
              <div style={{ fontSize: 10, opacity: 0.5 }}>{videoId ? "Monitoring..." : "Upload a video to begin"}</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {alerts.map((a, i) => <AlertCard key={a.alert_id} alert={a} index={i} />)}
            </div>
          )}

          {alerts.length > 0 && <AlertSummary alerts={alerts} />}
        </div>
      </div>
    </div>
  );
};

const UploadZone = ({ onFile, uploading, fileRef }) => {
  const [drag, setDrag] = useState(false);

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false);
    const fs = e.dataTransfer.files;
    if (fs.length > 0) onFile(fs);
  };

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => fileRef.current?.click()}
      style={{
        border: `1px dashed ${drag ? "#ff3b3b" : "var(--border2)"}`,
        borderRadius: 6, padding: "20px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        cursor: "pointer", transition: "all 0.2s",
        background: drag ? "#ff3b3b08" : "transparent",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{ fontSize: 22 }}>{uploading ? "⏳" : "📹"}</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>
            {uploading ? "Uploading video..." : "Upload CCTV Footage"}
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
            Drag & drop or click · MP4, AVI, MOV supported
          </div>
        </div>
      </div>
      <Badge label={uploading ? "UPLOADING" : "SELECT FILES"} color={uploading ? "#ffd600" : "#3b8fff"} />
      <input ref={fileRef} type="file" accept="video/*,image/*" multiple style={{ display: "none" }}
        onChange={e => e.target.files.length > 0 && onFile(e.target.files)} />
    </div>
  );
};

const Panel = ({ title, children, accent }) => (
  <div style={{
    background: "var(--surface)",
    border: `1px solid ${accent ? accent + "44" : "var(--border)"}`,
    borderRadius: 6, overflow: "hidden",
  }}>
    <div style={{
      padding: "8px 14px", borderBottom: `1px solid ${accent ? accent + "33" : "var(--border)"}`,
      fontSize: 10, letterSpacing: 2, color: accent || "var(--muted)", fontWeight: 700,
      background: accent ? `${accent}08` : "transparent",
    }}>{title}</div>
    <div style={{ padding: 14 }}>{children}</div>
  </div>
);

// ─── STATUS PANEL ─────────────────────────────────────────────────────────────
const StatusPanel = ({ status }) => {
  if (!status) return <div style={{ color: "var(--muted)", fontSize: 12 }}>Waiting...</div>;
  const pct = status.progress || 0;
  const color = status.status === "completed" ? "#00e5a0" : status.status === "failed" ? "#ff3b3b" : "#ffd600";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Badge label={status.status?.toUpperCase()} color={color} />
        <span style={{ fontSize: 16, fontWeight: 700, color, fontFamily: "Syne" }}>{pct}%</span>
      </div>
      <div style={{ height: 6, background: "var(--bg)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${pct}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          borderRadius: 3, transition: "width 0.4s ease",
          animation: status.status === "processing" ? "progressPulse 1.5s infinite" : "none",
        }} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        <MiniStat label="Frames Extracted" value={status.total_frames || "—"} />
        <MiniStat label="Frames Processed" value={status.processed_frames || "—"} />
      </div>
      {status.error && <div style={{ fontSize: 10, color: "#ff3b3b" }}>Error: {status.error}</div>}
    </div>
  );
};

// ─── STAT BOXES ───────────────────────────────────────────────────────────────
const StatBox = ({ label, value, color, big }) => (
  <div style={{
    background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 5, padding: "10px 12px",
  }}>
    <div style={{ fontSize: 9, color: "var(--muted)", letterSpacing: 1.5, marginBottom: 5 }}>{label}</div>
    <div style={{ fontSize: big ? 14 : 12, fontWeight: 700, color: color || "var(--text)", fontFamily: "Syne", lineHeight: 1.2 }}>{value}</div>
  </div>
);

const MiniStat = ({ label, value }) => (
  <div style={{ background: "var(--bg)", borderRadius: 4, padding: "7px 10px" }}>
    <div style={{ fontSize: 9, color: "var(--muted)", marginBottom: 3 }}>{label}</div>
    <div style={{ fontSize: 13, fontWeight: 700, fontFamily: "Syne" }}>{value}</div>
  </div>
);

// ─── PREDICTION TIMELINE ──────────────────────────────────────────────────────
const PredictionTimeline = ({ predictions }) => {
  const last20 = predictions.slice(-40);
  return (
    <div style={{ overflowX: "auto" }}>
      <div style={{ display: "flex", gap: 3, minWidth: "max-content", paddingBottom: 6 }}>
        {last20.map((p, i) => {
          const c = DISASTER_COLORS[p.class_name] || "#888";
          return (
            <div key={i} title={`${p.class_name} ${(p.confidence * 100).toFixed(0)}% @ ${p.timestamp}s`}
              style={{
                width: 18, height: 18, borderRadius: 3,
                background: `${c}${p.class_name === "Non-Damage" ? "44" : "cc"}`,
                border: `1px solid ${c}44`,
                cursor: "default",
                flexShrink: 0,
              }} />
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
        {Object.entries(DISASTER_COLORS).map(([k, v]) => (
          <div key={k} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 9, color: "var(--muted)" }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: v }} />
            {k}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── ALERT CARD ───────────────────────────────────────────────────────────────
const AlertCard = ({ alert, index }) => {
  const color = DISASTER_COLORS[alert.disaster_type] || "#ff3b3b";
  const sColor = SEVERITY_COLORS[alert.severity] || "#ff3b3b";

  return (
    <div className="slide-in" style={{
      background: "var(--bg)",
      border: `1px solid ${color}44`,
      borderLeft: `3px solid ${color}`,
      borderRadius: 5, padding: 12,
      animation: `slideIn 0.3s ease ${index * 0.05}s both`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color, fontFamily: "Syne" }}>
          {alert.disaster_type}
        </div>
        <Badge label={alert.severity} color={sColor} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 5, marginBottom: 8 }}>
        <MiniStat label="CONFIDENCE" value={`${(alert.confidence * 100).toFixed(1)}%`} />
        <MiniStat label="TIMESTAMP" value={`${alert.start_timestamp.toFixed(1)}s`} />
      </div>

      <ConfBar value={alert.confidence} color={color} />

      <div style={{ marginTop: 8, fontSize: 9, color: "var(--muted)" }}>
        Frames {alert.start_frame}–{alert.end_frame} · {alert.consecutive_detections} consecutive detections
      </div>

      {/* Simulated email */}
      <div style={{
        marginTop: 8, padding: "5px 8px",
        background: "#00e5a011", border: "1px solid #00e5a022",
        borderRadius: 3, fontSize: 9, color: "#00e5a0",
      }}>
        Alert notification sended!!!
      </div>
    </div>
  );
};

// ─── ALERT SUMMARY ────────────────────────────────────────────────────────────
const AlertSummary = ({ alerts }) => {
  const total = alerts.length;
  const criticals = alerts.filter(a => a.severity === "CRITICAL").length;
  const avgConf = (alerts.reduce((s, a) => s + a.confidence, 0) / total * 100).toFixed(1);

  return (
    <div style={{
      borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 4,
    }}>
      <div style={{ fontSize: 10, letterSpacing: 2, color: "var(--muted)", marginBottom: 8, fontWeight: 700 }}>SUMMARY</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <SumRow label="Total Alerts" value={total} color="var(--text)" />
        <SumRow label="Critical" value={criticals} color="#ff3b3b" />
        <SumRow label="Avg Confidence" value={`${avgConf}%`} color="#ffd600" />
      </div>
    </div>
  );
};

const SumRow = ({ label, value, color }) => (
  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
    <span style={{ color: "var(--muted)" }}>{label}</span>
    <span style={{ color, fontWeight: 700 }}>{value}</span>
  </div>
);

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [session, setSession] = useState(null);
  const [user, setUser]       = useState(null);
  const [toasts, setToasts]   = useState([]);
  const toastRef = useRef(0);

  const pushToast = useCallback((type, message) => {
    const id = ++toastRef.current;
    setToasts(prev => [...prev, { id, type, message, out: false }]);
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, out: true } : t));
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 400);
    }, 5000);
  }, []);

  const handleLogin = (sid, u) => { setSession(sid); setUser(u); };
  const handleLogout = () => { setSession(null); setUser(null); };

  return (
    <>
      <GlobalStyle />
      <Toast toasts={toasts} />
      {!session
        ? <AuthPage onLogin={handleLogin} />
        : <Dashboard session={session} user={user} onLogout={handleLogout} pushToast={pushToast} />
      }
    </>
  );
}

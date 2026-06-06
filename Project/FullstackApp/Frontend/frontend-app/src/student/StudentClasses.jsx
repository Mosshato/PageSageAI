import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";

function EnrollModal({ onClose, onEnrolled, token }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) { setError("Please enter a class code."); return; }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/classes/enroll/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ code: trimmed }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || "Failed to enroll."); return; }
      onEnrolled(data);
      onClose();
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200, backdropFilter: "blur(4px)" }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", width: "100%", maxWidth: "400px", padding: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <h3 style={{ color: "#fff", margin: 0, fontSize: "18px", fontFamily: "'Georgia', serif", fontWeight: 700 }}>Enroll in a Class</h3>
          <span onClick={onClose} style={{ color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "20px", lineHeight: 1 }}>×</span>
        </div>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Class Code</label>
            <input
              autoFocus value={code}
              onChange={e => { setCode(e.target.value); setError(""); }}
              placeholder="e.g. DEMO01"
              style={{ width: "100%", padding: "12px 14px", background: "rgba(255,255,255,0.03)", border: `1px solid ${error ? "#ef4444" : "rgba(255,255,255,0.1)"}`, color: "#fff", fontSize: "14px", fontFamily: "monospace", outline: "none", boxSizing: "border-box", borderRadius: "4px", letterSpacing: "0.1em" }}
            />
            {error && <div style={{ marginTop: "6px", fontSize: "11px", fontFamily: "monospace", color: "#ef4444" }}>{error}</div>}
          </div>
          <div style={{ fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.25)", lineHeight: 1.6 }}>Ask your teacher for the class code to join their class.</div>
          <button type="submit" disabled={loading} style={{ padding: "13px", background: "#f97316", color: "#000", border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", cursor: loading ? "not-allowed" : "pointer", borderRadius: "4px", opacity: loading ? 0.7 : 1 }}>
            {loading ? "Joining..." : "Join Class"}
          </button>
        </form>
      </div>
    </div>
  );
}

function ClassCard({ cls, onQuit }) {
  const [hovered, setHovered] = useState(false);
  const [confirmQuit, setConfirmQuit] = useState(false);
  const navigate = useNavigate();
  const pending = cls.pending_count ?? 0;

  function handleQuitClick(e) {
    e.stopPropagation();
    setConfirmQuit(true);
  }

  return (
    <>
      <div
        onClick={() => navigate(`/student/classes/${cls.id}`)}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{ position: "relative", background: `linear-gradient(135deg, ${cls.color}0f, ${cls.color}1e)`, border: `1px solid ${hovered ? cls.color : cls.color + "33"}`, borderRadius: "10px", padding: "20px", display: "flex", flexDirection: "column", gap: "12px", cursor: "pointer", transition: "border-color 0.2s ease, transform 0.15s ease", transform: hovered ? "translateY(-2px)" : "translateY(0)" }}
      >
        {hovered && (
          <button
            onClick={handleQuitClick}
            title="Leave class"
            style={{ position: "absolute", top: "10px", right: "10px", width: "22px", height: "22px", borderRadius: "50%", background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", color: "#ef4444", fontSize: "14px", lineHeight: 1, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", padding: 0 }}
          >×</button>
        )}
        <div style={{ width: "42px", height: "42px", borderRadius: "8px", background: cls.color + "22", border: `1px solid ${cls.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
          {cls.icon}
        </div>
        <div>
          <div style={{ color: "#fff", fontWeight: 700, fontSize: "15px", marginBottom: "3px", fontFamily: "'Georgia', serif" }}>{cls.name}</div>
          <div style={{ color: "rgba(255,255,255,0.45)", fontSize: "11px", fontFamily: "monospace" }}>{cls.teacher_name}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.12em", color: cls.color, background: cls.color + "1a", border: `1px solid ${cls.color}33`, padding: "3px 8px", borderRadius: "4px" }}>
            {cls.code}
          </span>
          {pending > 0 && (
            <span style={{ background: cls.color, color: "#000", fontSize: "10px", fontWeight: 700, fontFamily: "monospace", padding: "2px 8px", borderRadius: "10px" }}>
              {pending} due
            </span>
          )}
        </div>
      </div>

      {confirmQuit && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 300, backdropFilter: "blur(4px)" }} onClick={() => setConfirmQuit(false)}>
          <div onClick={e => e.stopPropagation()} style={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", padding: "28px", maxWidth: "360px", width: "100%" }}>
            <h3 style={{ color: "#fff", margin: "0 0 10px 0", fontSize: "17px", fontFamily: "'Georgia', serif" }}>Leave "{cls.name}"?</h3>
            <p style={{ color: "rgba(255,255,255,0.45)", fontSize: "13px", fontFamily: "monospace", margin: "0 0 24px 0", lineHeight: 1.6 }}>You will lose access to all assignments and lectures. You can re-enroll later with the class code.</p>
            <div style={{ display: "flex", gap: "10px" }}>
              <button onClick={() => setConfirmQuit(false)} style={{ flex: 1, padding: "11px", background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.6)", fontSize: "12px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}>Cancel</button>
              <button onClick={() => { setConfirmQuit(false); onQuit(cls.id); }} style={{ flex: 1, padding: "11px", background: "#ef4444", border: "none", color: "#fff", fontSize: "12px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}>Leave Class</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function EmptyState({ onEnroll }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "20px", padding: "60px 24px" }}>
      <div style={{ width: "72px", height: "72px", borderRadius: "16px", background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "30px" }}>✦</div>
      <div style={{ textAlign: "center" }}>
        <div style={{ color: "#fff", fontWeight: 700, fontSize: "17px", fontFamily: "'Georgia', serif", marginBottom: "8px" }}>No classes yet</div>
        <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "13px", fontFamily: "monospace", lineHeight: 1.7, maxWidth: "300px" }}>Enter a class code from your teacher to enroll and start tracking your work.</div>
      </div>
      <button onClick={onEnroll} style={{ padding: "12px 28px", background: "#f97316", color: "#000", border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
        onMouseEnter={e => { e.currentTarget.style.opacity = "0.85"; }}
        onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
      >+ Enroll in a Class</button>
    </div>
  );
}

export default function StudentClasses() {
  const { token } = useAuth();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  async function handleQuit(classId) {
    try {
      await fetch(`${API}/classes/${classId}/quit/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setClasses(prev => prev.filter(c => c.id !== classId));
    } catch {
      // silently ignore network errors
    }
  }

  useEffect(() => {
    fetch(`${API}/classes/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(setClasses)
      .catch(() => setClasses([]))
      .finally(() => setLoading(false));
  }, [token]);

  const totalDue = classes.reduce((acc, c) => acc + (c.pending_count ?? 0), 0);

  return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "32px 24px" }}>

        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "32px" }}>
          <div>
            <h1 style={{ color: "#fff", fontWeight: 700, fontSize: "24px", margin: "0 0 6px 0" }}>My Classes</h1>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>
              {loading ? "Loading..." : `${classes.length} enrolled${classes.length > 0 ? ` · ${totalDue} assignments due` : ""}`}
            </div>
          </div>
          {classes.length > 0 && (
            <button onClick={() => setShowModal(true)} style={{ padding: "9px 18px", background: "transparent", color: "#f97316", border: "1px solid #f97316", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px", transition: "all 0.2s ease" }}
              onMouseEnter={e => { e.currentTarget.style.background = "#f97316"; e.currentTarget.style.color = "#000"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#f97316"; }}
            >+ Enroll</button>
          )}
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "80px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading classes...</div>
        ) : classes.length === 0 ? (
          <EmptyState onEnroll={() => setShowModal(true)} />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "16px" }}>
            {classes.map(cls => <ClassCard key={cls.id} cls={cls} onQuit={handleQuit} />)}
          </div>
        )}
      </div>

      {showModal && (
        <EnrollModal
          token={token}
          onClose={() => setShowModal(false)}
          onEnrolled={newCls => setClasses(prev => [...prev, newCls])}
        />
      )}
    </div>
  );
}

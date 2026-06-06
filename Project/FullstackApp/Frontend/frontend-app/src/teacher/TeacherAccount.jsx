import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";

function AccountDropdown({ user, onClose, onLogout, onAccount }) {
  const ref = useRef(null);
  useEffect(() => {
    function h(e) { if (ref.current && !ref.current.contains(e.target)) onClose(); }
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [onClose]);
  const initials = `${user.firstName?.[0] ?? ""}${user.lastName?.[0] ?? ""}`.toUpperCase();
  return (
    <div ref={ref} style={{ position: "absolute", top: "calc(100% + 10px)", right: 0, background: "#161616", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", width: "240px", zIndex: 300, boxShadow: "0 16px 40px rgba(0,0,0,0.6)", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: "-6px", right: "13px", width: "10px", height: "10px", background: "#161616", border: "1px solid rgba(255,255,255,0.1)", borderRight: "none", borderBottom: "none", transform: "rotate(45deg)" }} />
      <div style={{ padding: "16px 18px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "38px", height: "38px", borderRadius: "50%", background: "linear-gradient(135deg, #f97316, #ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, color: "#000", fontFamily: "monospace", flexShrink: 0 }}>{initials}</div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, fontFamily: "'Georgia', serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{user.firstName} {user.lastName}</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{user.email}</div>
          </div>
        </div>
        <div style={{ marginTop: "10px" }}>
          <span style={{ background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.25)", color: "#f97316", padding: "2px 8px", borderRadius: "10px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase" }}>teacher</span>
        </div>
      </div>
      <div style={{ padding: "8px" }}>
        <button onClick={onAccount} style={{ width: "100%", textAlign: "left", padding: "9px 12px", background: "transparent", border: "none", color: "rgba(255,255,255,0.6)", fontSize: "12px", fontFamily: "monospace", cursor: "pointer", borderRadius: "6px", display: "flex", alignItems: "center", gap: "10px" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.color = "#fff"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.6)"; }}
        ><span style={{ opacity: 0.5 }}>◉</span> My Account</button>
        <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", margin: "6px 0" }} />
        <button onClick={onLogout} style={{ width: "100%", textAlign: "left", padding: "9px 12px", background: "transparent", border: "none", color: "rgba(239,68,68,0.7)", fontSize: "12px", fontFamily: "monospace", cursor: "pointer", borderRadius: "6px", display: "flex", alignItems: "center", gap: "10px" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(239,68,68,0.08)"; e.currentTarget.style.color = "#ef4444"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(239,68,68,0.7)"; }}
        ><span style={{ opacity: 0.7 }}>→</span> Log out</button>
      </div>
    </div>
  );
}

export function TeacherHeader({ user }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const initials = `${user?.firstName?.[0] ?? ""}${user?.lastName?.[0] ?? ""}`.toUpperCase();
  const NAV = [
    { label: "Home",     path: "/teacher" },
    { label: "Classes",  path: "/teacher/classes" },
    { label: "Students", path: "/teacher/students" },
  ];
  function handleLogout() { logout(); navigate("/login"); }
  return (
    <header style={{ background: "#111111", borderBottom: "1px solid rgba(255,255,255,0.07)", padding: "0 24px", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
      <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
        <div onClick={() => navigate("/teacher")} style={{ cursor: "pointer" }}>
          <span style={{ color: "#fff", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>Page</span>
          <span style={{ color: "#f97316", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>Sage</span>
          <span style={{ color: "#fff", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>AI</span>
        </div>
        <nav style={{ display: "flex", gap: "4px" }}>
          {NAV.map(item => {
            const active = location.pathname === item.path;
            return (
              <button key={item.label} onClick={() => navigate(item.path)} style={{ background: active ? "rgba(249,115,22,0.1)" : "transparent", color: active ? "#f97316" : "rgba(255,255,255,0.45)", border: "none", padding: "6px 14px", fontSize: "13px", fontFamily: "monospace", cursor: "pointer", borderRadius: "4px" }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.color = "#fff"; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.45)"; }}
              >{item.label}</button>
            );
          })}
        </nav>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em", background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)", padding: "4px 10px", borderRadius: "3px" }}>TEACHER</div>
        <div style={{ position: "relative" }}>
          <div onClick={() => setDropdownOpen(o => !o)} style={{ width: "32px", height: "32px", borderRadius: "50%", background: dropdownOpen ? "linear-gradient(135deg,#ea580c,#c2410c)" : "linear-gradient(135deg,#f97316,#ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 700, color: "#000", cursor: "pointer", fontFamily: "monospace", outline: dropdownOpen ? "2px solid rgba(249,115,22,0.4)" : "none", outlineOffset: "2px" }}>
            {initials}
          </div>
          {dropdownOpen && user && (
            <AccountDropdown user={user} onClose={() => setDropdownOpen(false)} onLogout={handleLogout} onAccount={() => { navigate("/teacher/account"); setDropdownOpen(false); }} />
          )}
        </div>
      </div>
    </header>
  );
}

function StatCard({ label, value, sub, color = "#f97316", icon }) {
  return (
    <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "24px 28px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
        <div style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>{label}</div>
        <div style={{ fontSize: "20px", opacity: 0.6 }}>{icon}</div>
      </div>
      <div style={{ fontSize: "38px", fontWeight: 900, color, fontFamily: "monospace", letterSpacing: "-1px" }}>{value ?? "—"}</div>
      {sub && <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginTop: "8px" }}>{sub}</div>}
    </div>
  );
}

export default function TeacherAccount() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/teacher/stats/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setStats).catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, [token]);

  const initials = `${user?.firstName?.[0] ?? ""}${user?.lastName?.[0] ?? ""}`.toUpperCase();
  const joinDate = new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" });

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <TeacherHeader user={user} />
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "40px 24px" }}>

        {/* Profile header */}
        <div style={{ display: "flex", alignItems: "center", gap: "24px", marginBottom: "40px", padding: "28px 32px", background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px" }}>
          <div style={{ width: "64px", height: "64px", borderRadius: "50%", background: "linear-gradient(135deg, #f97316, #ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "22px", fontWeight: 700, color: "#000", fontFamily: "monospace", flexShrink: 0 }}>
            {initials}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#fff", fontSize: "20px", fontWeight: 700, marginBottom: "4px" }}>{user?.firstName} {user?.lastName}</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>{user?.email}</div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px" }}>
              <span style={{ background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.3)", color: "#f97316", padding: "2px 8px", borderRadius: "10px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase" }}>teacher</span>
              <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "11px", fontFamily: "monospace" }}>Member since {joinDate}</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "60px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading stats...</div>
        ) : stats && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
              <StatCard label="Classes Created" value={stats.total_classes} sub="active classes" color="#f97316" icon="📚" />
              <StatCard label="Total Students" value={stats.total_students} sub="unique enrolled students" color="#3b82f6" icon="👥" />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
              <StatCard label="Assignments Created" value={stats.total_assignments} sub="across all classes" color="#8b5cf6" icon="📝" />
              <StatCard label="Submissions Received" value={stats.total_submissions} sub="from all students" color="#10b981" icon="📨" />
              <StatCard label="Awaiting Grades" value={stats.awaiting_grades} sub={stats.awaiting_grades === 0 ? "all caught up!" : "need your attention"} color={stats.awaiting_grades > 0 ? "#ef4444" : "#10b981"} icon="⏳" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

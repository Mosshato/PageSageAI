import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { TeacherHeader } from "./TeacherAccount";

const API = "http://localhost:8000/api";

const ICONS = ["📚","💻","📐","⚛️","📖","🎨","🌍","🔬","🎵","🏛️","📊","🤖"];
const COLORS = ["#f97316","#3b82f6","#8b5cf6","#10b981","#ef4444","#f59e0b","#ec4899","#06b6d4"];


function CreateClassModal({ onClose, onCreated, token, user }) {
  const [name, setName] = useState("");
  const [teacherName, setTeacherName] = useState(user ? `${user.firstName} ${user.lastName}`.trim() : "");
  const [color, setColor] = useState(COLORS[0]);
  const [icon, setIcon] = useState(ICONS[0]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) { setError("Class name is required."); return; }
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API}/teacher/classes/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name: name.trim(), teacher_name: teacherName.trim(), color, icon }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || "Failed to create class."); return; }
      onCreated(data);
      onClose();
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = { width: "100%", padding: "11px 14px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "14px", fontFamily: "monospace", outline: "none", boxSizing: "border-box", borderRadius: "4px" };
  const labelStyle = { display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200, backdropFilter: "blur(4px)" }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", width: "100%", maxWidth: "440px", padding: "28px", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <h3 style={{ color: "#fff", margin: 0, fontSize: "18px", fontFamily: "'Georgia', serif", fontWeight: 700 }}>Create Class</h3>
          <span onClick={onClose} style={{ color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "20px", lineHeight: 1 }}>×</span>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={labelStyle}>Class Name</label>
            <input value={name} onChange={e => { setName(e.target.value); setError(""); }} placeholder="e.g. Mathematics" style={{ ...inputStyle, borderColor: error ? "#ef4444" : "rgba(255,255,255,0.1)" }}
              onFocus={e => e.currentTarget.style.borderColor = "#f97316"}
              onBlur={e => e.currentTarget.style.borderColor = error ? "#ef4444" : "rgba(255,255,255,0.1)"}
            />
            {error && <div style={{ marginTop: "5px", fontSize: "11px", fontFamily: "monospace", color: "#ef4444" }}>{error}</div>}
          </div>

          <div>
            <label style={labelStyle}>Teacher Name</label>
            <input value={teacherName} onChange={e => setTeacherName(e.target.value)} placeholder="e.g. Dr. Smith" style={inputStyle}
              onFocus={e => e.currentTarget.style.borderColor = "#f97316"}
              onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
            />
          </div>

          <div>
            <label style={labelStyle}>Icon</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {ICONS.map(ic => (
                <div key={ic} onClick={() => setIcon(ic)} style={{ width: "38px", height: "38px", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", cursor: "pointer", background: icon === ic ? color + "33" : "rgba(255,255,255,0.04)", border: `2px solid ${icon === ic ? color : "rgba(255,255,255,0.08)"}`, transition: "all 0.15s ease" }}>
                  {ic}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label style={labelStyle}>Theme Color</label>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {COLORS.map(c => (
                <div key={c} onClick={() => setColor(c)} style={{ width: "30px", height: "30px", borderRadius: "50%", background: c, cursor: "pointer", border: `3px solid ${color === c ? "#fff" : "transparent"}`, transition: "border 0.15s ease" }} />
              ))}
            </div>
          </div>

          <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "14px 16px", display: "flex", alignItems: "center", gap: "14px" }}>
            <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: color + "22", border: `1px solid ${color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px" }}>{icon}</div>
            <div>
              <div style={{ color: "#fff", fontSize: "14px", fontWeight: 700, fontFamily: "'Georgia', serif" }}>{name || "Class Name"}</div>
              <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "2px" }}>{teacherName || "Teacher Name"}</div>
            </div>
          </div>

          <button type="submit" disabled={loading} style={{ padding: "13px", background: loading ? "rgba(255,255,255,0.06)" : "#f97316", color: loading ? "rgba(255,255,255,0.3)" : "#000", border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace", letterSpacing: "0.2em", textTransform: "uppercase", cursor: loading ? "not-allowed" : "pointer", borderRadius: "4px" }}>
            {loading ? "Creating..." : "Create Class"}
          </button>
        </form>
      </div>
    </div>
  );
}

function ClassCard({ cls, onOpen }) {
  const [hovered, setHovered] = useState(false);
  const total = cls.student_count ?? 0;
  const awaiting = cls.awaiting_grades ?? 0;

  return (
    <div onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{ background: "#111111", border: `1px solid ${hovered ? cls.color : "rgba(255,255,255,0.07)"}`, borderRadius: "8px", overflow: "hidden", cursor: "pointer", transition: "border 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease", transform: hovered ? "translateY(-2px)" : "translateY(0)", boxShadow: hovered ? "0 8px 30px rgba(0,0,0,0.4)" : "none" }}
      onClick={onOpen}
    >
      <div style={{ height: "90px", background: `linear-gradient(135deg, ${cls.color}22, ${cls.color}44)`, borderBottom: `1px solid ${cls.color}33`, padding: "14px 16px", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ color: "#fff", fontWeight: 700, fontSize: "16px", fontFamily: "'Georgia', serif" }}>{cls.name}</div>
          <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px", fontFamily: "monospace", marginTop: "4px", letterSpacing: "0.1em" }}>
            Code: <span style={{ color: cls.color }}>{cls.code}</span>
          </div>
        </div>
        <div style={{ fontSize: "26px", opacity: 0.4 }}>{cls.icon}</div>
      </div>
      <div style={{ padding: "14px 16px" }}>
        <div style={{ display: "flex", justifyContent: "space-around", marginBottom: "12px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: "20px", fontFamily: "monospace" }}>{total}</div>
            <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em" }}>STUDENTS</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: awaiting > 0 ? "#f97316" : "#10b981", fontWeight: 700, fontSize: "20px", fontFamily: "monospace" }}>{awaiting}</div>
            <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em" }}>TO GRADE</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "6px", marginTop: "4px" }}>
          {["Stream", "Classwork", "People", "Grades"].map(tab => (
            <span key={tab} onClick={e => e.stopPropagation()} style={{ flex: 1, textAlign: "center", fontSize: "9px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", cursor: "pointer", padding: "4px 0", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "3px", transition: "all 0.15s ease" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = cls.color; e.currentTarget.style.color = cls.color; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)"; e.currentTarget.style.color = "rgba(255,255,255,0.3)"; }}
            >{tab}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function TeacherDashboard() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      fetch(`${API}/teacher/classes/`, { headers }).then(r => r.json()),
      fetch(`${API}/teacher/stats/`,   { headers }).then(r => r.json()),
    ]).then(([cls, st]) => {
      setClasses(cls);
      setStats(st);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  const statCards = [
    { label: "Total Classes",   value: stats?.total_classes  ?? 0, color: "#f97316" },
    { label: "Total Students",  value: stats?.total_students ?? 0, color: "#3b82f6" },
    { label: "Awaiting Grades", value: stats?.awaiting_grades ?? 0, color: "#8b5cf6" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <TeacherHeader user={user} />
      <main style={{ maxWidth: "1100px", margin: "0 auto", padding: "40px 24px" }}>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "40px" }}>
          {statCards.map(stat => (
            <div key={stat.label} style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: "6px" }}>{stat.label}</div>
                <div style={{ color: "#fff", fontSize: "32px", fontWeight: 900, fontFamily: "monospace" }}>
                  {loading ? "—" : stat.value}
                </div>
              </div>
              <div style={{ width: "4px", height: "48px", background: stat.color, borderRadius: "2px", opacity: 0.6 }} />
            </div>
          ))}
        </div>

        {/* Classes header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
          <div>
            <h1 style={{ color: "#fff", margin: "0 0 4px", fontSize: "26px", fontWeight: 900, letterSpacing: "-0.5px" }}>My Classes</h1>
            <p style={{ color: "rgba(255,255,255,0.35)", margin: 0, fontSize: "13px", fontFamily: "monospace" }}>
              {loading ? "Loading..." : `${classes.length} active class${classes.length !== 1 ? "es" : ""}`}
            </p>
          </div>
          <button onClick={() => setShowModal(true)} style={{ padding: "10px 22px", background: "#f97316", color: "#000", border: "none", fontSize: "12px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px", transition: "opacity 0.2s ease" }}
            onMouseEnter={e => e.currentTarget.style.opacity = "0.85"}
            onMouseLeave={e => e.currentTarget.style.opacity = "1"}
          >+ Create Class</button>
        </div>

        {/* Class grid */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "80px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading classes...</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" }}>
            {classes.map(cls => <ClassCard key={cls.id} cls={cls} onOpen={() => navigate(`/teacher/classes/${cls.id}`)} />)}
            <div onClick={() => setShowModal(true)} style={{ background: "transparent", border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "8px", minHeight: "200px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", cursor: "pointer", gap: "8px", transition: "border 0.2s ease" }}
              onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(249,115,22,0.4)"}
              onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
            >
              <div style={{ fontSize: "28px", color: "rgba(255,255,255,0.15)" }}>+</div>
              <div style={{ fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.2)", letterSpacing: "0.1em" }}>Create a new class</div>
            </div>
          </div>
        )}
      </main>

      {showModal && (
        <CreateClassModal
          token={token}
          user={user}
          onClose={() => setShowModal(false)}
          onCreated={cls => {
            setClasses(prev => [...prev, cls]);
            setStats(prev => prev ? { ...prev, total_classes: prev.total_classes + 1 } : prev);
          }}
        />
      )}
    </div>
  );
}

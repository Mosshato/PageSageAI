import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { TeacherHeader } from "./TeacherAccount";

const API = "http://localhost:8000/api";

function colorFor(str) {
  const COLORS = ["#f97316","#3b82f6","#8b5cf6","#10b981","#ef4444","#f59e0b","#ec4899","#06b6d4"];
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h + str.charCodeAt(i)) % COLORS.length;
  return COLORS[h];
}

export default function TeacherStudents() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch(`${API}/teacher/students/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setStudents).catch(() => setStudents([]))
      .finally(() => setLoading(false));
  }, [token]);

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <TeacherHeader user={user} />
      <div style={{ maxWidth: "900px", margin: "0 auto", padding: "32px 24px" }}>

        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: "28px" }}>
          <div>
            <h1 style={{ color: "#fff", fontWeight: 700, fontSize: "24px", margin: "0 0 6px" }}>Students</h1>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>
              {loading ? "Loading..." : `${students.length} student${students.length !== 1 ? "s" : ""} across all your classes`}
            </div>
          </div>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or email..."
            style={{ padding: "9px 14px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "12px", fontFamily: "monospace", outline: "none", borderRadius: "6px", width: "260px" }}
            onFocus={e => e.currentTarget.style.borderColor = "#f97316"}
            onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
          />
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "80px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading students...</div>
        ) : filtered.length === 0 ? (
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "60px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontFamily: "monospace", fontSize: "13px" }}>
            {search ? "No students match your search." : "No students enrolled in your classes yet."}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {filtered.map(s => {
              const color = colorFor(s.email);
              const initials = s.name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
              return (
                <div key={s.email} style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "16px 20px", display: "flex", alignItems: "center", gap: "16px", transition: "border-color 0.15s" }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"}
                  onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)"}
                >
                  <div style={{ width: "40px", height: "40px", borderRadius: "50%", flexShrink: 0, background: color + "22", border: `1px solid ${color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, color, fontFamily: "monospace" }}>
                    {initials}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: "#fff", fontSize: "14px", fontWeight: 600 }}>{s.name}</div>
                    <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "2px" }}>{s.email}</div>
                  </div>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                    {s.classes.map(cls => (
                      <span
                        key={cls.id}
                        onClick={() => navigate(`/teacher/classes/${cls.id}`)}
                        style={{ display: "inline-flex", alignItems: "center", gap: "5px", fontSize: "10px", fontFamily: "monospace", color: cls.color, background: cls.color + "18", border: `1px solid ${cls.color}33`, padding: "3px 9px", borderRadius: "4px", cursor: "pointer", transition: "background 0.15s" }}
                        onMouseEnter={e => e.currentTarget.style.background = cls.color + "33"}
                        onMouseLeave={e => e.currentTarget.style.background = cls.color + "18"}
                      >
                        {cls.icon} {cls.name}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

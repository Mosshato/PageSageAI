import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";

// ── Helpers ────────────────────────────────────────────────────────────────

function relDue(isoDate) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(isoDate); due.setHours(0, 0, 0, 0);
  const diff = Math.round((due - today) / 86400000);
  if (diff < 0) return `${Math.abs(diff)}d overdue`;
  if (diff === 0) return "Due today";
  if (diff === 1) return "Tomorrow";
  return `In ${diff} days`;
}

function isDueUrgent(isoDate) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(isoDate); due.setHours(0, 0, 0, 0);
  return Math.round((due - today) / 86400000) <= 1;
}

// ── Enroll Modal ───────────────────────────────────────────────────────────

function EnrollModal({ onClose, onEnrolled, token }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) { setError("Please enter a class code."); return; }
    setLoading(true); setError("");
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

// ── Calendar Widget ────────────────────────────────────────────────────────

function CalendarWidget({ assignments }) {
  const today = new Date();
  const [current, setCurrent] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const year = current.getFullYear();
  const month = current.getMonth();
  const monthName = current.toLocaleString("default", { month: "long" });
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Build map of day → [class_color, ...]
  const dotMap = useMemo(() => {
    const map = {};
    assignments.filter(a => !a.my_submission && a.status === "pending").forEach(a => {
      if (!a.due_date) return;
      const [y, m, d] = a.due_date.split("-").map(Number);
      if (y === year && m - 1 === month) {
        if (!map[d]) map[d] = [];
        map[d].push(a.class_color);
      }
    });
    return map;
  }, [assignments, year, month]);

  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);
  while (days.length % 7 !== 0) days.push(null);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px", flexShrink: 0 }}>
        <button onClick={() => setCurrent(new Date(year, month - 1, 1))} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer", padding: "2px 10px", fontFamily: "monospace", fontSize: "14px", borderRadius: "4px" }}>‹</button>
        <div style={{ color: "#fff", fontWeight: 700, fontSize: "13px", fontFamily: "monospace", letterSpacing: "0.1em" }}>{monthName} {year}</div>
        <button onClick={() => setCurrent(new Date(year, month + 1, 1))} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer", padding: "2px 10px", fontFamily: "monospace", fontSize: "14px", borderRadius: "4px" }}>›</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "2px", marginBottom: "4px", flexShrink: 0 }}>
        {["S","M","T","W","T","F","S"].map((d, i) => (
          <div key={i} style={{ textAlign: "center", fontSize: "9px", fontFamily: "monospace", color: "rgba(255,255,255,0.25)", padding: "2px 0" }}>{d}</div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gridTemplateRows: `repeat(${days.length / 7}, 1fr)`, gap: "2px", flex: 1 }}>
        {days.map((day, i) => {
          const isToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear();
          const dots = dotMap[day] ?? [];
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", borderRadius: "5px", background: isToday ? "#f97316" : "transparent", border: dots.length > 0 && !isToday ? "1px solid rgba(255,255,255,0.1)" : "1px solid transparent", transition: "background 0.15s ease" }}
              onMouseEnter={e => { if (day && !isToday) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={e => { if (day && !isToday) e.currentTarget.style.background = "transparent"; }}
            >
              {day && (
                <>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", color: isToday ? "#000" : "#fff", fontWeight: isToday ? 700 : 400 }}>{day}</span>
                  {dots.length > 0 && (
                    <div style={{ display: "flex", gap: "1px", marginTop: "1px" }}>
                      {dots.slice(0, 3).map((color, j) => (
                        <div key={j} style={{ width: "3px", height: "3px", borderRadius: "50%", background: isToday ? "#000" : color }} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Empty state helper ─────────────────────────────────────────────────────

function EmptyPane({ icon, text }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "10px", opacity: 0.35 }}>
      <div style={{ fontSize: "26px" }}>{icon}</div>
      <div style={{ color: "rgba(255,255,255,0.6)", fontSize: "11px", fontFamily: "monospace", textAlign: "center", lineHeight: 1.6 }}>{text}</div>
    </div>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────

export default function StudentDashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [classes, setClasses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingAssignments, setLoadingAssignments] = useState(true);

  function fetchData() {
    fetch(`${API}/classes/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setClasses).catch(() => setClasses([]))
      .finally(() => setLoadingClasses(false));
    fetch(`${API}/assignments/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setAssignments).catch(() => setAssignments([]))
      .finally(() => setLoadingAssignments(false));
  }

  useEffect(() => {
    fetchData();
    window.addEventListener("focus", fetchData);
    return () => window.removeEventListener("focus", fetchData);
  }, [token]);

  // Upcoming: no submission, not graded, sorted by due_date asc, first 5
  const upcoming = useMemo(() => {
    return assignments
      .filter(a => !a.my_submission && a.status !== "graded")
      .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
      .slice(0, 5);
  }, [assignments]);

  // Recent grades: has submission with a grade, sorted by due_date desc, first 5
  const recentGrades = useMemo(() => {
    return assignments
      .filter(a => a.my_submission?.grade != null)
      .sort((a, b) => new Date(b.due_date) - new Date(a.due_date))
      .slice(0, 5);
  }, [assignments]);

  const totalDue = classes.reduce((acc, c) => acc + (c.pending_count ?? 0), 0);

  const PAD = 24, GAP = 16, HEADER_H = 60;

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <main style={{ padding: `${PAD}px`, height: `calc(100vh - ${HEADER_H}px)`, boxSizing: "border-box", overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: `${GAP}px`, height: "100%" }}>

          {/* TOP LEFT — Classes */}
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexShrink: 0 }}>
              <div>
                <div style={{ color: "#fff", fontWeight: 700, fontSize: "16px" }}>My Classes</div>
                <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "2px" }}>
                  {loadingClasses ? "Loading..." : `${classes.length} enrolled · ${totalDue} due`}
                </div>
              </div>
              <button onClick={() => setShowModal(true)} style={{ padding: "7px 14px", background: "transparent", color: "#f97316", border: "1px solid #f97316", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
                onMouseEnter={e => { e.currentTarget.style.background = "#f97316"; e.currentTarget.style.color = "#000"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#f97316"; }}
              >+ Add</button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", overflowY: "auto", flex: 1 }}>
              {loadingClasses ? null : classes.length === 0 ? (
                <EmptyPane icon="📚" text={"No classes yet.\nUse + Add to enroll."} />
              ) : classes.map(cls => (
                <div key={cls.id}
                  onClick={() => navigate(`/student/classes/${cls.id}`)}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: `linear-gradient(135deg, ${cls.color}11, ${cls.color}22)`, border: `1px solid ${cls.color}33`, borderRadius: "6px", cursor: "pointer", transition: "border 0.2s ease" }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = cls.color}
                  onMouseLeave={e => e.currentTarget.style.borderColor = `${cls.color}33`}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "16px", opacity: 0.7 }}>{cls.icon}</span>
                    <div>
                      <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600 }}>{cls.name}</div>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px", fontFamily: "monospace" }}>{cls.teacher_name}</div>
                    </div>
                  </div>
                  {(cls.pending_count ?? 0) > 0 && (
                    <div style={{ background: cls.color, color: "#000", fontSize: "10px", fontWeight: 700, fontFamily: "monospace", padding: "2px 7px", borderRadius: "10px" }}>{cls.pending_count} due</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* TOP RIGHT — Upcoming */}
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: "16px", marginBottom: "4px", flexShrink: 0 }}>Upcoming</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginBottom: "16px", flexShrink: 0 }}>Assignments due soon</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", overflowY: "auto", flex: 1 }}>
              {loadingAssignments ? null : upcoming.length === 0 ? (
                <EmptyPane icon="✓" text={"No pending assignments.\nYou're all caught up!"} />
              ) : upcoming.map(a => (
                <div key={a.id}
                  onClick={() => navigate(`/student/classes/${a.class_obj}`)}
                  style={{ background: "#0a0a0a", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", padding: "12px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", transition: "border 0.2s ease" }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"}
                  onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)"}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ width: "3px", height: "28px", background: a.class_color, borderRadius: "2px", flexShrink: 0 }} />
                    <div>
                      <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "160px" }}>{a.title}</div>
                      <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>{a.class_name}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: "11px", fontFamily: "monospace", color: isDueUrgent(a.due_date) ? "#f97316" : "rgba(255,255,255,0.3)", flexShrink: 0 }}>
                    {relDue(a.due_date)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* BOTTOM LEFT — Recent Grades */}
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: "16px", marginBottom: "4px", flexShrink: 0 }}>Recent Grades</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginBottom: "16px", flexShrink: 0 }}>Last graded assignments</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", overflowY: "auto", flex: 1 }}>
              {loadingAssignments ? null : recentGrades.length === 0 ? (
                <EmptyPane icon="🎓" text={"No graded assignments yet.\nCheck back after submission."} />
              ) : recentGrades.map(a => (
                <div key={a.id}
                  onClick={() => navigate(`/student/classes/${a.class_obj}`)}
                  style={{ background: "#0a0a0a", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", padding: "12px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", transition: "border 0.2s ease" }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"}
                  onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)"}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ width: "3px", height: "28px", background: a.class_color, borderRadius: "2px", flexShrink: 0 }} />
                    <div>
                      <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "160px" }}>{a.title}</div>
                      <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>{a.class_name}</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: "60px", height: "3px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${a.my_submission.grade}%`, background: a.class_color, borderRadius: "2px" }} />
                    </div>
                    <div style={{ fontSize: "13px", fontWeight: 700, fontFamily: "monospace", color: a.class_color, minWidth: "36px", textAlign: "right" }}>{a.my_submission.grade}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* BOTTOM RIGHT — Calendar */}
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: "16px", marginBottom: "4px", flexShrink: 0 }}>Calendar</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginBottom: "12px", flexShrink: 0 }}>Your schedule</div>
            <div style={{ flex: 1, display: "flex", justifyContent: "center", minHeight: 0 }}>
              <div style={{ width: "100%", maxWidth: "340px", display: "flex", flexDirection: "column" }}>
                <CalendarWidget assignments={assignments} />
              </div>
            </div>
          </div>

        </div>
      </main>

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

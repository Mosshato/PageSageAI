import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SubmitModal from "./SubmitModal";

const API = "http://localhost:8000/api";

const COLORS = ["#f97316","#10b981","#3b82f6","#8b5cf6","#ec4899","#eab308"];
function colorFor(str) { return COLORS[Math.abs(str.split("").reduce((a,c)=>a+c.charCodeAt(0),0)) % COLORS.length]; }
function initials(name) { return name.split(" ").map(w=>w[0]).join("").slice(0,2).toUpperCase(); }
function fmtDate(iso) { return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" }); }
function fmtDue(iso) {
  const d = new Date(iso), now = new Date();
  const diff = Math.round((d - now) / 86400000);
  if (diff < 0) return `${Math.abs(diff)}d ago`;
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  return `${d.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
}

// ─── Sidebar ────────────────────────────────────────────────────────────────

function Sidebar({ classes, activeId }) {
  const navigate = useNavigate();
  return (
    <aside style={{ width: "220px", flexShrink: 0, background: "#111111", borderRight: "1px solid rgba(255,255,255,0.07)", display: "flex", flexDirection: "column", overflowY: "auto" }}>
      <div style={{ padding: "20px 16px 12px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.18em", color: "rgba(255,255,255,0.25)", textTransform: "uppercase", flexShrink: 0 }}>My Classes</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "2px", padding: "0 8px 16px" }}>
        {classes.map(cls => {
          const active = cls.id === activeId;
          return (
            <button key={cls.id} onClick={() => navigate(`/student/classes/${cls.id}`)} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "9px 10px", borderRadius: "6px", background: active ? cls.color + "18" : "transparent", border: `1px solid ${active ? cls.color + "44" : "transparent"}`, cursor: "pointer", textAlign: "left", width: "100%", transition: "all 0.15s ease" }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
            >
              <span style={{ width: "28px", height: "28px", borderRadius: "6px", flexShrink: 0, background: cls.color + "22", border: `1px solid ${cls.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px" }}>{cls.icon}</span>
              <div style={{ minWidth: 0 }}>
                <div style={{ color: active ? "#fff" : "rgba(255,255,255,0.55)", fontSize: "12px", fontWeight: active ? 700 : 400, fontFamily: "monospace", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{cls.name}</div>
                {(cls.pending_count ?? 0) > 0 && <div style={{ fontSize: "10px", color: cls.color, fontFamily: "monospace", marginTop: "1px" }}>{cls.pending_count} due</div>}
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

// ─── Tab bar ────────────────────────────────────────────────────────────────

function TabBar({ active, onChange, color }) {
  return (
    <div style={{ display: "flex", gap: "4px", borderBottom: "1px solid rgba(255,255,255,0.07)", padding: "0 28px", background: "#111111", flexShrink: 0 }}>
      {["Dashboard", "Assignments", "Lectures", "Classmates"].map(tab => (
        <button key={tab} onClick={() => onChange(tab)} style={{ background: "transparent", border: "none", borderBottom: `2px solid ${active === tab ? color : "transparent"}`, color: active === tab ? "#fff" : "rgba(255,255,255,0.4)", padding: "14px 16px 12px", fontSize: "12px", fontFamily: "monospace", fontWeight: active === tab ? 700 : 400, letterSpacing: "0.08em", cursor: "pointer", transition: "color 0.15s ease" }}
          onMouseEnter={e => { if (active !== tab) e.currentTarget.style.color = "rgba(255,255,255,0.75)"; }}
          onMouseLeave={e => { if (active !== tab) e.currentTarget.style.color = "rgba(255,255,255,0.4)"; }}
        >{tab}</button>
      ))}
    </div>
  );
}

// ─── Dashboard tab ──────────────────────────────────────────────────────────

function AnnouncementCard({ item, teacherName, color }) {
  const letter = teacherName.split(" ").pop()[0].toUpperCase();
  return (
    <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px 22px", display: "flex", flexDirection: "column", gap: "12px" }}>
      {item.pinned && (
        <div style={{ display: "inline-flex", alignItems: "center", gap: "5px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.12em", color, background: color + "18", border: `1px solid ${color}33`, padding: "2px 8px", borderRadius: "4px", alignSelf: "flex-start" }}>↑ PINNED</div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{ width: "34px", height: "34px", borderRadius: "50%", flexShrink: 0, background: `linear-gradient(135deg, ${color}, ${color}aa)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, color: "#000", fontFamily: "monospace" }}>{letter}</div>
        <div>
          <div style={{ color: "#fff", fontSize: "13px", fontWeight: 700, fontFamily: "'Georgia', serif" }}>{teacherName}</div>
          <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>{fmtDate(item.created_at)}</div>
        </div>
      </div>
      <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "14px", lineHeight: 1.7, margin: 0, fontFamily: "'Georgia', serif" }}>{item.body}</p>
    </div>
  );
}

function DashboardTab({ cls }) {
  const pending = (cls.assignments ?? []).filter(a => a.status === "pending");
  const announcements = [...(cls.announcements ?? [])].sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

  return (
    <div style={{ display: "flex", gap: "24px", alignItems: "flex-start" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "24px", minWidth: 0 }}>

        {/* Hero */}
        <div style={{ background: `linear-gradient(135deg, ${cls.color}18, ${cls.color}08)`, border: `1px solid ${cls.color}33`, borderRadius: "12px", padding: "28px 28px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ width: "52px", height: "52px", borderRadius: "10px", background: cls.color + "22", border: `1px solid ${cls.color}55`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "22px" }}>{cls.icon}</div>
            <div>
              <h1 style={{ color: "#fff", margin: 0, fontSize: "26px", fontWeight: 700, fontFamily: "'Georgia', serif" }}>{cls.name}</h1>
              <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "12px", fontFamily: "monospace", marginTop: "4px" }}>
                {cls.teacher_name} · <span style={{ color: cls.color }}>{cls.code}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Announcements */}
        <div>
          <div style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "12px" }}>Announcements</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {announcements.length === 0 ? (
              <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "32px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontSize: "13px", fontFamily: "monospace" }}>No announcements yet.</div>
            ) : announcements.map(item => (
              <AnnouncementCard key={item.id} item={item} teacherName={cls.teacher_name} color={cls.color} />
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming work */}
      <div style={{ width: "280px", flexShrink: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "4px" }}>Upcoming Work</div>
        {pending.length === 0 ? (
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "20px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontSize: "12px", fontFamily: "monospace" }}>All caught up!</div>
        ) : pending.map(a => (
          <div key={a.id} style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "8px", padding: "14px 16px", cursor: "pointer", transition: "border-color 0.15s ease" }}
            onMouseEnter={e => e.currentTarget.style.borderColor = cls.color + "66"}
            onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)"}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
              <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, fontFamily: "'Georgia', serif" }}>{a.title}</div>
              <div style={{ fontSize: "10px", fontFamily: "monospace", color: cls.color, flexShrink: 0 }}>{a.points}pts</div>
            </div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", marginTop: "4px" }}>Due {fmtDue(a.due_date)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Assignments tab ─────────────────────────────────────────────────────────

const STATUS_STYLES = {
  pending:   { label: "Pending",   color: "#f97316" },
  submitted: { label: "Submitted", color: "#3b82f6" },
  graded:    { label: "Graded",    color: "#10b981" },
};

function FileChip({ name }) {
  const ICONS = { pdf:{icon:"PDF",color:"#ef4444"}, doc:{icon:"DOC",color:"#3b82f6"}, docx:{icon:"DOC",color:"#3b82f6"}, zip:{icon:"ZIP",color:"#eab308"}, png:{icon:"IMG",color:"#8b5cf6"}, jpg:{icon:"IMG",color:"#8b5cf6"}, py:{icon:"PY",color:"#10b981"}, js:{icon:"JS",color:"#f97316"}, ipynb:{icon:"NB",color:"#f97316"}, csv:{icon:"CSV",color:"#10b981"} };
  const ext = name.split(".").pop().toLowerCase();
  const { icon, color: c } = ICONS[ext] ?? { icon: ext.toUpperCase().slice(0,3), color: "rgba(255,255,255,0.4)" };
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "7px", background: c + "18", border: `1px solid ${c}33`, borderRadius: "5px", padding: "4px 10px 4px 6px" }}>
      <span style={{ fontSize: "9px", fontWeight: 700, fontFamily: "monospace", color: c, letterSpacing: "0.05em" }}>{icon}</span>
      <span style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.6)" }}>{name}</span>
    </div>
  );
}

function SubmissionPanel({ submission, accentColor, onUnsubmit, onResubmit }) {
  const date = new Date(submission.submitted_at).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  const graded = submission.grade != null;
  return (
    <div style={{ marginTop: "14px", background: graded ? "#10b98108" : "#3b82f608", border: `1px solid ${graded ? "#10b98133" : "#3b82f633"}`, borderRadius: "8px", padding: "14px 16px", display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", color: graded ? "#10b981" : "#3b82f6", fontFamily: "monospace", fontWeight: 700 }}>
            {graded ? "✓ Graded" : "✓ Submitted"}
          </span>
          <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)", fontFamily: "monospace" }}>{date}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {graded && (
            <span style={{ fontSize: "13px", fontWeight: 700, fontFamily: "monospace", color: "#10b981", background: "#10b98118", border: "1px solid #10b98133", padding: "3px 10px", borderRadius: "4px" }}>
              {submission.grade}%
            </span>
          )}
          <button onClick={onResubmit} style={{ padding: "5px 12px", background: "transparent", border: `1px solid ${accentColor}`, color: accentColor, fontSize: "10px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
            onMouseEnter={e => { e.currentTarget.style.background = accentColor; e.currentTarget.style.color = "#000"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = accentColor; }}
          >Change</button>
          <button onClick={onUnsubmit} style={{ padding: "5px 12px", background: "transparent", border: "1px solid rgba(239,68,68,0.4)", color: "rgba(239,68,68,0.7)", fontSize: "10px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "#ef4444"; e.currentTarget.style.color = "#ef4444"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(239,68,68,0.4)"; e.currentTarget.style.color = "rgba(239,68,68,0.7)"; }}
          >Unsubmit</button>
        </div>
      </div>
      {submission.note && (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", padding: "10px 13px" }}>
          <div style={{ fontSize: "9px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.25)", textTransform: "uppercase", marginBottom: "5px" }}>Teacher's note</div>
          <div style={{ fontSize: "13px", color: "rgba(255,255,255,0.65)", fontFamily: "'Georgia', serif", lineHeight: 1.6 }}>{submission.note}</div>
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
        {(submission.files ?? []).map((f, i) => f.url ? <a key={i} href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><FileChip name={f.name} /></a> : <FileChip key={i} name={f.name} />)}
      </div>
    </div>
  );
}

function AssignmentsTab({ assignments, color, token }) {
  const [expanded, setExpanded] = useState(null);
  const [submitFor, setSubmitFor] = useState(null);
  // localAssignments mirrors API data; my_submission per assignment vine din API
  const [localAssignments, setLocalAssignments] = useState(assignments);

  useEffect(() => { setLocalAssignments(assignments); }, [assignments]);

  async function handleSubmit(files) {
    const fd = new FormData();
    files.forEach(f => fd.append("files", f));
    const res = await fetch(`${API}/assignments/${submitFor.id}/submit/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (!res.ok) return;
    const submission = await res.json();
    setLocalAssignments(prev => prev.map(a =>
      a.id === submitFor.id ? { ...a, my_submission: submission } : a
    ));
    setSubmitFor(null);
  }

  async function handleUnsubmit(id) {
    await fetch(`${API}/assignments/${id}/unsubmit/`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    setLocalAssignments(prev => prev.map(a =>
      a.id === id ? { ...a, my_submission: null } : a
    ));
  }

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {localAssignments.map(a => {
          const sub = a.my_submission;
          const displayStatus = a.status === "graded" ? "graded" : sub ? "submitted" : "pending";
          const s = STATUS_STYLES[displayStatus] ?? STATUS_STYLES.pending;
          const open = expanded === a.id;
          const atts = a.attachments ?? [];
          return (
            <div key={a.id} style={{ background: "#111111", border: `1px solid ${open ? color + "55" : "rgba(255,255,255,0.07)"}`, borderRadius: "10px", overflow: "hidden", transition: "border-color 0.15s ease" }}>
              <div onClick={() => setExpanded(open ? null : a.id)} style={{ display: "flex", alignItems: "center", gap: "16px", padding: "16px 20px", cursor: "pointer" }}>
                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: s.color, flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: "#fff", fontSize: "14px", fontWeight: 600, fontFamily: "'Georgia', serif" }}>{a.title}</div>
                  <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "3px" }}>
                    Due {fmtDue(a.due_date)} · {a.points} pts{atts.length > 0 ? ` · ${atts.length} file${atts.length > 1 ? "s" : ""}` : ""}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0 }}>
                  {a.my_submission?.grade != null && <div style={{ fontSize: "13px", fontWeight: 700, fontFamily: "monospace", color: s.color }}>{a.my_submission.grade}%</div>}
                  <span style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", color: s.color, background: s.color + "18", border: `1px solid ${s.color}33`, padding: "3px 9px", borderRadius: "4px" }}>{s.label}</span>
                  <span style={{ color: "rgba(255,255,255,0.25)", fontSize: "14px", transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s ease", display: "inline-block" }}>▾</span>
                </div>
              </div>
              {open && (
                <div style={{ padding: "0 20px 18px 44px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                  {a.description && <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px", fontFamily: "'Georgia', serif", lineHeight: 1.7, margin: "14px 0 0" }}>{a.description}</p>}
                  {atts.length > 0 && (
                    <div style={{ marginTop: "14px" }}>
                      <div style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.25)", textTransform: "uppercase", marginBottom: "8px" }}>Attached Files</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>{atts.map((f, i) => f.url ? <a key={i} href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><FileChip name={f.name} /></a> : <FileChip key={i} name={f.name} />)}</div>
                    </div>
                  )}
                  {!sub && a.status !== "graded" && (
                    <button onClick={() => setSubmitFor(a)} style={{ marginTop: "14px", padding: "9px 20px", background: color, color: "#000", border: "none", fontSize: "11px", fontWeight: 700, fontFamily: "monospace", letterSpacing: "0.12em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
                      onMouseEnter={e => { e.currentTarget.style.opacity = "0.8"; }}
                      onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
                    >Submit Work</button>
                  )}
                  {sub && (
                    <SubmissionPanel submission={sub} accentColor={color} onUnsubmit={() => handleUnsubmit(a.id)} onResubmit={() => setSubmitFor(a)} />
                  )}
                </div>
              )}
            </div>
          );
        })}
        {localAssignments.length === 0 && (
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "48px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontSize: "13px", fontFamily: "monospace" }}>No assignments yet.</div>
        )}
      </div>
      {submitFor && (
        <SubmitModal assignment={submitFor} color={color} onClose={() => setSubmitFor(null)} onSubmit={handleSubmit} />
      )}
    </>
  );
}

// ─── Lectures tab — unified view ─────────────────────────────────────────────

function LecturesTab({ color, classId, token }) {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    function load() {
      fetch(`${API}/ai-courses/class/${classId}/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => { if (Array.isArray(data)) setCourses(data); })
        .catch(() => {});
    }
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [classId, token]);

  if (courses.length === 0) return (
    <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "48px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontSize: "13px", fontFamily: "monospace" }}>
      No courses available yet.
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      {courses.map(course => (
        <div key={course.id} style={{ background: "#111111", border: `1px solid ${course.status === "READY" ? color + "44" : "rgba(255,255,255,0.07)"}`, borderRadius: "12px", padding: "18px 20px", display: "flex", alignItems: "center", gap: "16px", transition: "border-color 0.4s" }}>

          {/* Icon */}
          <div style={{ width: "42px", height: "42px", borderRadius: "8px", flexShrink: 0, background: color + "18", border: `1px solid ${color}33`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>📄</div>

          {/* Info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: "#fff", fontSize: "14px", fontWeight: 700, fontFamily: "'Georgia', serif", marginBottom: "5px" }}>{course.title}</div>

            {course.status === "PROCESSING" && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontFamily: "monospace", color: "#f59e0b" }}>
                <span style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", border: "2px solid #f59e0b", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
                AI assistant is preparing the lecture...
              </div>
            )}
            {course.status === "READY" && (
              <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#10b981" }}>✓ AI lecture ready</div>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: "8px", flexShrink: 0, alignItems: "center" }}>
            {/* Download PDF — mereu disponibil */}
            {course.pdf_url && (
              <a href={course.pdf_url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
                <button style={{ padding: "7px 14px", background: "transparent", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.15)", fontSize: "10px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "5px" }}
                  onMouseEnter={e => { e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.4)"; }}
                  onMouseLeave={e => { e.currentTarget.style.color = "rgba(255,255,255,0.5)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"; }}
                >↓ PDF</button>
              </a>
            )}

            {/* Teach using AI — apare doar când READY */}
            {course.status === "READY" ? (
              <button onClick={() => navigate(`/student/ai-teach/${course.id}`)}
                style={{ padding: "8px 18px", background: `linear-gradient(135deg, #6366f1, #8b5cf6)`, color: "#fff", border: "none", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", borderRadius: "5px", boxShadow: "0 0 20px #6366f133" }}
                onMouseEnter={e => e.currentTarget.style.opacity = "0.85"}
                onMouseLeave={e => e.currentTarget.style.opacity = "1"}
              >🎓 Teach using AI</button>
            ) : (
              <button disabled title="Lecția audio se pregătește în fundal..."
                style={{ padding: "8px 18px", background: "rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.18)", border: "1px solid rgba(255,255,255,0.07)", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "not-allowed", borderRadius: "5px" }}
              >🎓 Teach using AI</button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Classmates tab ──────────────────────────────────────────────────────────

function ClassmatesTab({ classmates, teacherName, color }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div>
        <div style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "10px" }}>Teacher</div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "12px", background: "#111111", border: `1px solid ${color}33`, borderRadius: "8px", padding: "12px 16px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: `linear-gradient(135deg, ${color}, ${color}aa)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px", fontWeight: 700, color: "#000", fontFamily: "monospace" }}>
            {initials(teacherName)}
          </div>
          <div>
            <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, fontFamily: "'Georgia', serif" }}>{teacherName}</div>
            <div style={{ color, fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>Instructor</div>
          </div>
        </div>
      </div>
      <div>
        <div style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "10px" }}>Students · {classmates.length}</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "8px" }}>
          {classmates.map(s => {
            const c = colorFor(s.student_email);
            const ini = initials(s.student_name);
            return (
              <div key={s.id} style={{ display: "flex", alignItems: "center", gap: "10px", background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "8px", padding: "12px 14px", transition: "border-color 0.15s ease" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)"}
              >
                <div style={{ width: "32px", height: "32px", borderRadius: "50%", flexShrink: 0, background: c + "33", border: `1px solid ${c}55`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700, color: c, fontFamily: "monospace" }}>{ini}</div>
                <div style={{ color: "rgba(255,255,255,0.75)", fontSize: "13px", fontFamily: "'Georgia', serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{s.student_name}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Main ────────────────────────────────────────────────────────────────────

export default function ClassDashboard() {
  const { classId } = useParams();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [cls, setCls] = useState(null);
  const [allClasses, setAllClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/classes/${classId}/`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch(`${API}/classes/`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([detail, list]) => {
      setCls(detail);
      setAllClasses(list);
    }).finally(() => setLoading(false));
  }, [classId, token]);

  if (loading) return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "13px" }}>Loading...</div>
  );

  if (!cls || cls.error) return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,0.3)", fontFamily: "monospace", fontSize: "14px" }}>Class not found.</div>
  );

  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)", background: "#0a0a0a", overflow: "hidden" }}>
      <Sidebar classes={allClasses} activeId={cls.id} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <TabBar active={activeTab} onChange={setActiveTab} color={cls.color} />
        <div style={{ flex: 1, overflowY: "auto", padding: "28px" }}>
          {activeTab === "Dashboard"   && <DashboardTab cls={cls} />}
          {activeTab === "Assignments" && <AssignmentsTab assignments={cls.assignments ?? []} color={cls.color} token={token} />}
          {activeTab === "Lectures"    && <LecturesTab color={cls.color} classId={cls.id} token={token} />}
          {activeTab === "Classmates"  && <ClassmatesTab classmates={cls.classmates ?? []} teacherName={cls.teacher_name} color={cls.color} />}
        </div>
      </div>
    </div>
  );
}

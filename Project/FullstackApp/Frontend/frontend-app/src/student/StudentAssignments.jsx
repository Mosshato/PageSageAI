import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SubmitModal from "./SubmitModal";

const API = "http://localhost:8000/api";
const FILTERS = ["All", "Pending", "Submitted", "Graded"];

function visibleStatus(a) {
  if (a.status === "graded") return "graded";
  if (a.my_submission) return "submitted";
  return "pending";
}

const STATUS_STYLES = {
  pending:   { label: "Pending",   color: "#f97316" },
  submitted: { label: "Submitted", color: "#3b82f6" },
  graded:    { label: "Graded",    color: "#10b981" },
};

function fmtDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}, ${y}`;
}

const FILE_ICONS = { pdf: { icon: "PDF", color: "#ef4444" }, doc: { icon: "DOC", color: "#3b82f6" }, docx: { icon: "DOC", color: "#3b82f6" }, zip: { icon: "ZIP", color: "#eab308" }, png: { icon: "IMG", color: "#8b5cf6" }, jpg: { icon: "IMG", color: "#8b5cf6" }, py: { icon: "PY", color: "#10b981" }, js: { icon: "JS", color: "#f97316" }, xlsx: { icon: "XLS", color: "#10b981" } };

function FileChip({ name }) {
  const e = name.split(".").pop().toLowerCase();
  const { icon, color: c } = FILE_ICONS[e] ?? { icon: e.toUpperCase().slice(0, 3), color: "rgba(255,255,255,0.4)" };
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "7px", background: c + "18", border: `1px solid ${c}33`, borderRadius: "5px", padding: "4px 10px 4px 6px" }}>
      <span style={{ fontSize: "9px", fontWeight: 700, fontFamily: "monospace", color: c, letterSpacing: "0.05em" }}>{icon}</span>
      <span style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.6)" }}>{name}</span>
    </div>
  );
}

function SubmissionPanel({ submission, accentColor, onUnsubmit, onResubmit }) {
  const ts = submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : "";
  const graded = submission.grade != null;
  return (
    <div style={{ marginTop: "14px", background: graded ? "#10b98108" : "#3b82f608", border: `1px solid ${graded ? "#10b98133" : "#3b82f633"}`, borderRadius: "8px", padding: "14px 16px", display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", color: graded ? "#10b981" : "#3b82f6", fontFamily: "monospace", fontWeight: 700 }}>
            {graded ? "✓ Graded" : "✓ Submitted"}
          </span>
          {ts && <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)", fontFamily: "monospace" }}>{ts}</span>}
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
      {(submission.files ?? []).length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          {submission.files.map((f, i) => (
            f.url
              ? <a key={i} href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><FileChip name={f.name} /></a>
              : <FileChip key={i} name={f.name} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function StudentAssignments() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("All");
  const [expanded, setExpanded] = useState(null);
  const [submitFor, setSubmitFor] = useState(null);

  useEffect(() => {
    fetch(`${API}/assignments/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setAssignments).catch(() => setAssignments([]))
      .finally(() => setLoading(false));
  }, [token]);

  const enriched = useMemo(() =>
    assignments.map(a => ({ ...a, _status: visibleStatus(a) }))
      .sort((a, b) => {
        const order = { pending: 0, submitted: 1, graded: 2 };
        return order[a._status] - order[b._status] || new Date(a.due_date) - new Date(b.due_date);
      }),
    [assignments]
  );

  const counts = useMemo(() => ({
    All: enriched.length,
    Pending: enriched.filter(a => a._status === "pending").length,
    Submitted: enriched.filter(a => a._status === "submitted").length,
    Graded: enriched.filter(a => a._status === "graded").length,
  }), [enriched]);

  const visible = filter === "All" ? enriched : enriched.filter(a => a._status === filter.toLowerCase());

  async function handleSubmit(files) {
    if (!submitFor) return;
    const fd = new FormData();
    files.forEach(f => fd.append("files", f));
    const res = await fetch(`${API}/assignments/${submitFor.id}/submit/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (!res.ok) return;
    const submission = await res.json();
    setAssignments(prev => prev.map(a => a.id === submitFor.id ? { ...a, my_submission: submission } : a));
    setSubmitFor(null);
  }

  async function handleUnsubmit(assignmentId) {
    const res = await fetch(`${API}/assignments/${assignmentId}/unsubmit/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    setAssignments(prev => prev.map(a => a.id === assignmentId ? { ...a, my_submission: null } : a));
  }

  return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "32px 24px" }}>

        <div style={{ marginBottom: "28px" }}>
          <h1 style={{ color: "#fff", fontWeight: 700, fontSize: "24px", margin: "0 0 6px 0" }}>Assignments</h1>
          <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>
            {loading ? "Loading..." : `${counts.Pending} pending · ${counts.Submitted} submitted · ${counts.Graded} graded`}
          </div>
        </div>

        {/* Filter tabs */}
        <div style={{ display: "flex", gap: "4px", borderBottom: "1px solid rgba(255,255,255,0.07)", marginBottom: "20px" }}>
          {FILTERS.map(f => (
            <button key={f} onClick={() => { setFilter(f); setExpanded(null); }} style={{ background: "transparent", border: "none", borderBottom: `2px solid ${filter === f ? "#f97316" : "transparent"}`, color: filter === f ? "#fff" : "rgba(255,255,255,0.4)", padding: "10px 16px 8px", fontSize: "12px", fontFamily: "monospace", fontWeight: filter === f ? 700 : 400, letterSpacing: "0.08em", cursor: "pointer", transition: "color 0.15s ease" }}
              onMouseEnter={e => { if (filter !== f) e.currentTarget.style.color = "rgba(255,255,255,0.75)"; }}
              onMouseLeave={e => { if (filter !== f) e.currentTarget.style.color = "rgba(255,255,255,0.4)"; }}
            >
              {f}
              <span style={{ marginLeft: "6px", fontSize: "10px", color: filter === f ? "#f97316" : "rgba(255,255,255,0.25)" }}>{counts[f]}</span>
            </button>
          ))}
        </div>

        {/* List */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "80px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading assignments...</div>
        ) : visible.length === 0 ? (
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "48px", textAlign: "center", color: "rgba(255,255,255,0.25)", fontSize: "13px", fontFamily: "monospace" }}>
            No {filter.toLowerCase()} assignments.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {visible.map(a => {
              const st = a._status;
              const s = STATUS_STYLES[st];
              const open = expanded === a.id;
              const color = a.class_color ?? "#f97316";
              return (
                <div key={a.id} style={{ background: "#111111", border: `1px solid ${open ? color + "55" : "rgba(255,255,255,0.07)"}`, borderRadius: "10px", overflow: "hidden", transition: "border-color 0.15s ease" }}>
                  <div onClick={() => setExpanded(open ? null : a.id)} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "15px 18px", cursor: "pointer" }}>
                    <div style={{ width: "3px", height: "36px", borderRadius: "2px", background: color, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: "#fff", fontSize: "14px", fontWeight: 600 }}>{a.title}</div>
                      <div style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "3px" }}>
                        <span onClick={e => { e.stopPropagation(); navigate(`/student/classes/${a.class_obj}`); }} style={{ color, fontSize: "10px", fontFamily: "monospace", cursor: "pointer" }}
                          onMouseEnter={e => { e.currentTarget.style.textDecoration = "underline"; }}
                          onMouseLeave={e => { e.currentTarget.style.textDecoration = "none"; }}
                        >{a.class_name}</span>
                        <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "10px", fontFamily: "monospace" }}>·</span>
                        <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace" }}>Due {fmtDate(a.due_date)} · {a.points} pts</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
                      {st === "graded" && a.my_submission?.grade != null && <div style={{ fontSize: "13px", fontWeight: 700, fontFamily: "monospace", color: s.color }}>{a.my_submission.grade}%</div>}
                      <span style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", color: s.color, background: s.color + "18", border: `1px solid ${s.color}33`, padding: "3px 9px", borderRadius: "4px" }}>{s.label}</span>
                      <span style={{ color: "rgba(255,255,255,0.25)", fontSize: "14px", transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s ease", display: "inline-block" }}>▾</span>
                    </div>
                  </div>

                  {open && (
                    <div style={{ padding: "0 18px 16px 35px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                      {a.description && <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px", lineHeight: 1.7, margin: "14px 0 0" }}>{a.description}</p>}

                      {(a.attachments ?? []).length > 0 && (
                        <div style={{ marginTop: "14px" }}>
                          <div style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.25)", textTransform: "uppercase", marginBottom: "8px" }}>Attached Files</div>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                            {a.attachments.map((f, i) => (
                            f.url
                              ? <a key={i} href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><FileChip name={f.name} /></a>
                              : <FileChip key={i} name={f.name} />
                          ))}
                          </div>
                        </div>
                      )}

                      {st === "pending" && (
                        <button onClick={() => setSubmitFor(a)} style={{ marginTop: "14px", padding: "9px 20px", background: color, color: "#000", border: "none", fontSize: "11px", fontWeight: 700, fontFamily: "monospace", letterSpacing: "0.12em", textTransform: "uppercase", cursor: "pointer", borderRadius: "4px" }}
                          onMouseEnter={e => { e.currentTarget.style.opacity = "0.8"; }}
                          onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
                        >Submit Work</button>
                      )}

                      {st === "submitted" && a.my_submission && (
                        <SubmissionPanel
                          submission={a.my_submission}
                          accentColor={color}
                          onUnsubmit={() => handleUnsubmit(a.id)}
                          onResubmit={() => setSubmitFor(a)}
                        />
                      )}

                      {st === "graded" && a.my_submission && (
                        <SubmissionPanel
                          submission={a.my_submission}
                          accentColor={s.color}
                          onUnsubmit={() => handleUnsubmit(a.id)}
                          onResubmit={() => setSubmitFor(a)}
                        />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {submitFor && (
        <SubmitModal
          assignment={{ ...submitFor, due: fmtDate(submitFor.due_date) }}
          color={submitFor.class_color ?? "#f97316"}
          onClose={() => setSubmitFor(null)}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}

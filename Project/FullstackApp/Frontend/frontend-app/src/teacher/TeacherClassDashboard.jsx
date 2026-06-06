import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { TeacherHeader } from "./TeacherAccount";

const API = "http://localhost:8000/api";
const ICONS  = ["📚","💻","📐","⚛️","📖","🎨","🌍","🔬","🎵","🏛️","📊","🤖"];
const COLORS = ["#f97316","#3b82f6","#8b5cf6","#10b981","#ef4444","#f59e0b","#ec4899","#06b6d4"];

// ── Primitives ─────────────────────────────────────────────────────────────

function SectionTitle({ children }) {
  return <div style={{ fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "12px" }}>{children}</div>;
}

function Btn({ children, onClick, color = "#f97316", outline = false, danger = false, small = false, disabled = false }) {
  const bg  = outline ? "transparent" : danger ? "#ef4444" : color;
  const fg  = outline ? (danger ? "#ef4444" : color) : danger ? "#fff" : "#000";
  const bdr = outline ? `1px solid ${danger ? "rgba(239,68,68,0.5)" : color + "88"}` : "none";
  return (
    <button onClick={onClick} disabled={disabled} style={{ padding: small ? "5px 12px" : "9px 18px", background: disabled ? "rgba(255,255,255,0.05)" : bg, color: disabled ? "rgba(255,255,255,0.2)" : fg, border: bdr, fontSize: small ? "10px" : "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: disabled ? "not-allowed" : "pointer", borderRadius: "4px", transition: "opacity 0.15s", whiteSpace: "nowrap" }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.opacity = "0.8"; }}
      onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
    >{children}</button>
  );
}

function Input({ value, onChange, placeholder, type = "text", multiline = false, rows = 3 }) {
  const base = { width: "100%", padding: "10px 13px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px", fontFamily: "monospace", outline: "none", boxSizing: "border-box", borderRadius: "4px", resize: multiline ? "vertical" : undefined };
  return multiline
    ? <textarea value={value} onChange={onChange} placeholder={placeholder} rows={rows} style={base} onFocus={e => e.currentTarget.style.borderColor="#f97316"} onBlur={e => e.currentTarget.style.borderColor="rgba(255,255,255,0.1)"} />
    : <input value={value} onChange={onChange} placeholder={placeholder} type={type} style={base} onFocus={e => e.currentTarget.style.borderColor="#f97316"} onBlur={e => e.currentTarget.style.borderColor="rgba(255,255,255,0.1)"} />;
}

function Modal({ title, onClose, children, maxWidth = "480px" }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 300, backdropFilter: "blur(4px)" }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", width: "100%", maxWidth, padding: "28px", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "22px" }}>
          <h3 style={{ color: "#fff", margin: 0, fontSize: "17px", fontFamily: "'Georgia', serif", fontWeight: 700 }}>{title}</h3>
          <span onClick={onClose} style={{ color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "22px", lineHeight: 1 }}>×</span>
        </div>
        {children}
      </div>
    </div>
  );
}

// Inline confirm prompt replaces the delete button
function ConfirmDelete({ label, onConfirm, onCancel }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <span style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.45)" }}>{label}</span>
      <Btn onClick={onConfirm} danger small>Yes, delete</Btn>
      <Btn onClick={onCancel} outline small>Cancel</Btn>
    </div>
  );
}

// Real file upload input
function FileUploadInput({ files, onChange, color = "#f97316" }) {
  const inputRef = useState(null);
  const ref = { current: null };

  function handlePick(e) {
    const picked = Array.from(e.target.files);
    const existing = new Set(files.map(f => f.name));
    onChange([...files, ...picked.filter(f => !existing.has(f.name))]);
    e.target.value = "";
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div
        onClick={() => ref.current && ref.current.click()}
        style={{ border: `2px dashed ${color}44`, borderRadius: "8px", padding: "18px", textAlign: "center", cursor: "pointer", background: "rgba(255,255,255,0.01)", transition: "border-color 0.15s" }}
        onMouseEnter={e => e.currentTarget.style.borderColor = color + "99"}
        onMouseLeave={e => e.currentTarget.style.borderColor = color + "44"}
      >
        <div style={{ fontSize: "20px", opacity: 0.5, marginBottom: "4px" }}>↑</div>
        <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.4)" }}>
          Click to browse files
        </div>
        <input ref={el => ref.current = el} type="file" multiple style={{ display: "none" }} onChange={handlePick} />
      </div>
      {files.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          {files.map((f, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "5px", padding: "6px 10px" }}>
              <span style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.6)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</span>
              <span style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.25)", flexShrink: 0 }}>{(f.size / 1024).toFixed(0)} KB</span>
              <span onClick={() => onChange(files.filter((_, j) => j !== i))} style={{ color: "rgba(255,255,255,0.25)", cursor: "pointer", fontSize: "16px", lineHeight: 1, flexShrink: 0 }}
                onMouseEnter={e => e.currentTarget.style.color = "#ef4444"}
                onMouseLeave={e => e.currentTarget.style.color = "rgba(255,255,255,0.25)"}
              >×</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Stream tab ─────────────────────────────────────────────────────────────

function StreamTab({ cls, token, onUpdate }) {
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [pinned, setPinned] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmId, setConfirmId] = useState(null);

  const announcements = [...(cls.announcements ?? [])].sort((a, b) => b.pinned - a.pinned);

  async function handleAdd() {
    if (!title.trim() || !body.trim()) return;
    setSaving(true);
    const res = await fetch(`${API}/teacher/classes/${cls.id}/announcements/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ title, body, pinned }),
    });
    if (res.ok) {
      const ann = await res.json();
      onUpdate(prev => ({ ...prev, announcements: [ann, ...(prev.announcements ?? [])] }));
      setTitle(""); setBody(""); setPinned(false); setShowForm(false);
    }
    setSaving(false);
  }

  async function handleDelete(id) {
    await fetch(`${API}/teacher/classes/${cls.id}/announcements/${id}/`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    onUpdate(prev => ({ ...prev, announcements: prev.announcements.filter(a => a.id !== id) }));
    setConfirmId(null);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Btn onClick={() => setShowForm(v => !v)}>{showForm ? "Cancel" : "+ Add Announcement"}</Btn>
      </div>

      {showForm && (
        <div style={{ background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" />
          <Input value={body} onChange={e => setBody(e.target.value)} placeholder="Body" multiline rows={4} />
          <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}>
            <input type="checkbox" checked={pinned} onChange={e => setPinned(e.target.checked)} />
            Pin announcement
          </label>
          <Btn onClick={handleAdd} disabled={saving}>{saving ? "Posting..." : "Post"}</Btn>
        </div>
      )}

      {announcements.length === 0 && !showForm && (
        <div style={{ textAlign: "center", padding: "48px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>No announcements yet.</div>
      )}

      {announcements.map(a => (
        <div key={a.id} style={{ background: "#111", border: `1px solid ${a.pinned ? cls.color + "44" : "rgba(255,255,255,0.07)"}`, borderRadius: "10px", padding: "18px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                {a.pinned && <span style={{ fontSize: "9px", fontFamily: "monospace", color: cls.color, background: cls.color + "18", border: `1px solid ${cls.color}33`, padding: "2px 7px", borderRadius: "3px" }}>PINNED</span>}
                <div style={{ color: "#fff", fontWeight: 700, fontSize: "14px", fontFamily: "'Georgia', serif" }}>{a.title}</div>
              </div>
              <div style={{ color: "rgba(255,255,255,0.55)", fontSize: "13px", lineHeight: 1.7 }}>{a.body}</div>
              <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "10px", fontFamily: "monospace", marginTop: "10px" }}>{new Date(a.created_at).toLocaleDateString()}</div>
            </div>
            <div style={{ flexShrink: 0 }}>
              {confirmId === a.id
                ? <ConfirmDelete label="Delete this announcement?" onConfirm={() => handleDelete(a.id)} onCancel={() => setConfirmId(null)} />
                : <Btn onClick={() => setConfirmId(a.id)} danger outline small>Delete</Btn>
              }
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Classwork tab ──────────────────────────────────────────────────────────

function GradePanel({ submission, classId, token, color, onGraded }) {
  const [grade, setGrade] = useState(submission.grade ?? "");
  const [note, setNote] = useState(submission.note ?? "");
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    const res = await fetch(`${API}/teacher/classes/${classId}/submissions/${submission.id}/grade/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ grade: grade === "" ? null : parseInt(grade), note }),
    });
    if (res.ok) { const data = await res.json(); onGraded(data); }
    setSaving(false);
  }

  return (
    <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: color + "22", border: `1px solid ${color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700, color, fontFamily: "monospace", flexShrink: 0 }}>
          {(submission.student_name ?? submission.student_email)?.[0]?.toUpperCase()}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600 }}>{submission.student_name ?? submission.student_email}</div>
          <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace" }}>{submission.student_email} · {new Date(submission.submitted_at).toLocaleString()}</div>
        </div>
        {submission.grade != null && (
          <span style={{ fontSize: "12px", fontFamily: "monospace", fontWeight: 700, color: "#10b981", background: "#10b98118", border: "1px solid #10b98133", padding: "3px 9px", borderRadius: "4px" }}>{submission.grade}%</span>
        )}
      </div>

      {(submission.files ?? []).length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          {submission.files.map((f, i) => (
            <a key={i} href={f.url ?? "#"} target="_blank" rel="noreferrer" style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.5)", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "3px 8px", borderRadius: "4px", textDecoration: "none" }} onMouseEnter={e => e.currentTarget.style.color="#fff"} onMouseLeave={e => e.currentTarget.style.color="rgba(255,255,255,0.5)"}>{f.name}</a>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
        <input value={grade} onChange={e => setGrade(e.target.value)} placeholder="Grade 0–100" type="number" min="0" max="100"
          style={{ width: "130px", padding: "7px 10px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "12px", fontFamily: "monospace", outline: "none", borderRadius: "4px" }}
          onFocus={e => e.currentTarget.style.borderColor = color}
          onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
        />
        <textarea value={note} onChange={e => setNote(e.target.value)} placeholder="Leave a note (optional)" rows={2}
          style={{ flex: 1, padding: "7px 10px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "12px", fontFamily: "monospace", outline: "none", borderRadius: "4px", resize: "none" }}
          onFocus={e => e.currentTarget.style.borderColor = color}
          onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
        />
        <Btn onClick={save} disabled={saving} small>{saving ? "..." : "Save Grade"}</Btn>
      </div>
    </div>
  );
}

function AssignmentFormFields({ form, onChange, color }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <Input value={form.title} onChange={e => onChange({ ...form, title: e.target.value })} placeholder="Title" />
      <Input value={form.description} onChange={e => onChange({ ...form, description: e.target.value })} placeholder="Description (optional)" multiline />
      <div style={{ display: "flex", gap: "10px" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>DUE DATE</div>
          <Input value={form.due_date} onChange={e => onChange({ ...form, due_date: e.target.value })} type="date" />
        </div>
        <div style={{ width: "120px" }}>
          <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>POINTS</div>
          <Input value={form.points} onChange={e => onChange({ ...form, points: e.target.value })} placeholder="100" type="number" />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>ATTACHMENTS (visible to students)</div>
        <FileUploadInput files={form.files} onChange={files => onChange({ ...form, files })} color={color} />
      </div>
    </div>
  );
}

function EditAssignmentModal({ assignment, classId, color, token, onClose, onSaved }) {
  const [form, setForm] = useState({
    title: assignment.title,
    description: assignment.description ?? "",
    due_date: assignment.due_date,
    points: String(assignment.points),
    files: [],
  });
  const [existingAttachments, setExistingAttachments] = useState(assignment.attachments ?? []);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    const fd = new FormData();
    fd.append("title", form.title);
    fd.append("description", form.description);
    fd.append("due_date", form.due_date);
    fd.append("points", parseInt(form.points) || 100);
    existingAttachments.forEach(a => fd.append("keep_ids", a.id));
    form.files.forEach(f => fd.append("files", f));
    const res = await fetch(`${API}/teacher/classes/${classId}/assignments/${assignment.id}/edit/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (res.ok) { const data = await res.json(); onSaved(data); onClose(); }
    setSaving(false);
  }

  return (
    <Modal title="Edit Assignment" onClose={onClose} maxWidth="520px">
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Title" />
        <Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Description (optional)" multiline />
        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>DUE DATE</div>
            <Input value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} type="date" />
          </div>
          <div style={{ width: "120px" }}>
            <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>POINTS</div>
            <Input value={form.points} onChange={e => setForm(f => ({ ...f, points: e.target.value }))} placeholder="100" type="number" />
          </div>
        </div>

        {existingAttachments.length > 0 && (
          <div>
            <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "6px", letterSpacing: "0.1em" }}>EXISTING FILES</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
              {existingAttachments.map(a => (
                <div key={a.id} style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "5px", padding: "6px 10px" }}>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.6)", flex: 1 }}>{a.name}</span>
                  <span onClick={() => setExistingAttachments(prev => prev.filter(x => x.id !== a.id))} style={{ color: "rgba(255,255,255,0.25)", cursor: "pointer", fontSize: "16px", lineHeight: 1 }}
                    onMouseEnter={e => e.currentTarget.style.color = "#ef4444"}
                    onMouseLeave={e => e.currentTarget.style.color = "rgba(255,255,255,0.25)"}
                  >×</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginBottom: "5px", letterSpacing: "0.1em" }}>ADD NEW FILES</div>
          <FileUploadInput files={form.files} onChange={files => setForm(f => ({ ...f, files }))} color={color} />
        </div>

        <Btn onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save Changes"}</Btn>
      </div>
    </Modal>
  );
}

function ClassworkTab({ cls, token, onUpdate }) {
  const [expanded, setExpanded] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editAssignment, setEditAssignment] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const emptyForm = { title: "", description: "", due_date: "", points: "100", files: [] };
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  async function handleAdd() {
    if (!form.title.trim() || !form.due_date) return;
    setSaving(true);
    const fd = new FormData();
    fd.append("title", form.title);
    fd.append("description", form.description);
    fd.append("due_date", form.due_date);
    fd.append("points", parseInt(form.points) || 100);
    form.files.forEach(f => fd.append("files", f));
    const res = await fetch(`${API}/teacher/classes/${cls.id}/assignments/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (res.ok) {
      const a = await res.json();
      onUpdate(prev => ({ ...prev, assignments: [...(prev.assignments ?? []), a] }));
      setForm(emptyForm); setShowForm(false);
    }
    setSaving(false);
  }

  async function handleDelete(id) {
    await fetch(`${API}/teacher/classes/${cls.id}/assignments/${id}/`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    onUpdate(prev => ({ ...prev, assignments: prev.assignments.filter(a => a.id !== id) }));
    setExpanded(null); setConfirmDeleteId(null);
  }

  function handleGraded(assignmentId, updatedSub) {
    onUpdate(prev => ({
      ...prev,
      assignments: prev.assignments.map(a => a.id !== assignmentId ? a : {
        ...a,
        submissions: a.submissions.map(s => s.id === updatedSub.id ? updatedSub : s),
      }),
    }));
  }

  function handleEdited(updated) {
    onUpdate(prev => ({
      ...prev,
      assignments: prev.assignments.map(a => a.id === updated.id ? { ...a, ...updated } : a),
    }));
  }

  const assignments = cls.assignments ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Btn onClick={() => setShowForm(v => !v)}>{showForm ? "Cancel" : "+ Add Assignment"}</Btn>
      </div>

      {showForm && (
        <div style={{ background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
          <AssignmentFormFields form={form} onChange={setForm} color={cls.color} />
          <Btn onClick={handleAdd} disabled={saving}>{saving ? "Creating..." : "Create Assignment"}</Btn>
        </div>
      )}

      {assignments.length === 0 && !showForm && (
        <div style={{ textAlign: "center", padding: "48px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>No assignments yet.</div>
      )}

      {assignments.map(a => {
        const open = expanded === a.id;
        const subCount = (a.submissions ?? []).length;
        const gradedCount = (a.submissions ?? []).filter(s => s.grade != null).length;
        return (
          <div key={a.id} style={{ background: "#111", border: `1px solid ${open ? cls.color + "55" : "rgba(255,255,255,0.07)"}`, borderRadius: "10px", overflow: "hidden", transition: "border-color 0.15s" }}>
            <div onClick={() => setExpanded(open ? null : a.id)} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "15px 18px", cursor: "pointer" }}>
              <div style={{ width: "3px", height: "36px", borderRadius: "2px", background: cls.color, flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ color: "#fff", fontSize: "14px", fontWeight: 600 }}>{a.title}</div>
                <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", marginTop: "3px" }}>
                  Due {a.due_date} · {a.points} pts · {subCount} submission{subCount !== 1 ? "s" : ""} · {gradedCount} graded
                </div>
              </div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <span style={{ fontSize: "10px", fontFamily: "monospace", color: a.status === "graded" ? "#10b981" : "#f97316", background: a.status === "graded" ? "#10b98118" : "#f9731618", border: `1px solid ${a.status === "graded" ? "#10b98133" : "#f9731633"}`, padding: "3px 8px", borderRadius: "4px" }}>{a.status}</span>
                <span style={{ color: "rgba(255,255,255,0.25)", fontSize: "14px", transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s", display: "inline-block" }}>▾</span>
              </div>
            </div>

            {open && (
              <div style={{ padding: "0 18px 18px 35px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                {a.description && <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "13px", lineHeight: 1.7, margin: "14px 0" }}>{a.description}</p>}

                {(a.attachments ?? []).length > 0 && (
                  <div style={{ marginBottom: "14px" }}>
                    <SectionTitle>Attachments</SectionTitle>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {a.attachments.map((f, i) => (
                        <a key={i} href={f.url ?? "#"} target="_blank" rel="noreferrer" style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.5)", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "3px 8px", borderRadius: "4px", textDecoration: "none" }} onMouseEnter={e => e.currentTarget.style.color="#fff"} onMouseLeave={e => e.currentTarget.style.color="rgba(255,255,255,0.5)"}>{f.name}</a>
                      ))}
                    </div>
                  </div>
                )}

                <SectionTitle>Submissions ({subCount})</SectionTitle>
                {subCount === 0 ? (
                  <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px", fontFamily: "monospace", marginBottom: "14px" }}>No submissions yet.</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
                    {a.submissions.map(sub => (
                      <GradePanel key={sub.id} submission={sub} classId={cls.id} token={token} color={cls.color} onGraded={updated => handleGraded(a.id, updated)} />
                    ))}
                  </div>
                )}

                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "8px", flexWrap: "wrap" }}>
                  <Btn onClick={() => setEditAssignment(a)} outline small>Edit Assignment</Btn>
                  {confirmDeleteId === a.id
                    ? <ConfirmDelete label="Delete this assignment?" onConfirm={() => handleDelete(a.id)} onCancel={() => setConfirmDeleteId(null)} />
                    : <Btn onClick={() => setConfirmDeleteId(a.id)} danger outline small>Delete Assignment</Btn>
                  }
                </div>
              </div>
            )}
          </div>
        );
      })}

      {editAssignment && (
        <EditAssignmentModal assignment={editAssignment} classId={cls.id} color={cls.color} token={token}
          onClose={() => setEditAssignment(null)}
          onSaved={updated => { handleEdited(updated); setEditAssignment(null); }}
        />
      )}
    </div>
  );
}

// ── People tab ─────────────────────────────────────────────────────────────

function PeopleTab({ cls, token, onUpdate }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [confirmRemoveId, setConfirmRemoveId] = useState(null);

  async function handleAdd() {
    if (!email.trim()) return;
    setAdding(true); setError("");
    const res = await fetch(`${API}/teacher/classes/${cls.id}/students/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ email: email.trim() }),
    });
    const data = await res.json();
    if (!res.ok) { setError(data.error || "Failed to add student."); }
    else { onUpdate(prev => ({ ...prev, enrollments: [...(prev.enrollments ?? []), data] })); setEmail(""); }
    setAdding(false);
  }

  async function handleRemove(enrollmentId) {
    await fetch(`${API}/teacher/classes/${cls.id}/students/${enrollmentId}/`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    onUpdate(prev => ({ ...prev, enrollments: prev.enrollments.filter(e => e.id !== enrollmentId) }));
    setConfirmRemoveId(null);
  }

  const enrollments = cls.enrollments ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "18px" }}>
        <SectionTitle>Add Student by Email</SectionTitle>
        <div style={{ display: "flex", gap: "8px" }}>
          <div style={{ flex: 1 }}>
            <Input value={email} onChange={e => { setEmail(e.target.value); setError(""); }} placeholder="student@email.com" type="email" />
          </div>
          <Btn onClick={handleAdd} disabled={adding}>{adding ? "Adding..." : "Add"}</Btn>
        </div>
        {error && <div style={{ marginTop: "8px", fontSize: "11px", fontFamily: "monospace", color: "#ef4444" }}>{error}</div>}
      </div>

      <div>
        <SectionTitle>{enrollments.length} Student{enrollments.length !== 1 ? "s" : ""}</SectionTitle>
        {enrollments.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>No students enrolled yet.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {enrollments.map(e => (
              <div key={e.id} style={{ background: "#111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "8px", padding: "12px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px" }}>
                <div>
                  <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600 }}>{e.student_name}</div>
                  <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "2px" }}>{e.student_email}</div>
                </div>
                <div style={{ flexShrink: 0 }}>
                  {confirmRemoveId === e.id
                    ? <ConfirmDelete label="Remove this student?" onConfirm={() => handleRemove(e.id)} onCancel={() => setConfirmRemoveId(null)} />
                    : <Btn onClick={() => setConfirmRemoveId(e.id)} danger outline small>Remove</Btn>
                  }
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── AI Status badge (top-level to avoid "component created during render") ────

function AIStatusBadge({ status }) {
  if (status === "PROCESSING") return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", fontSize: "10px", fontFamily: "monospace", color: "#f59e0b", background: "#f59e0b18", border: "1px solid #f59e0b33", padding: "3px 9px", borderRadius: "4px" }}>
      <span style={{ display: "inline-block", width: "7px", height: "7px", borderRadius: "50%", border: "2px solid #f59e0b", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
      PROCESSING
    </span>
  );
  if (status === "READY") return (
    <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#10b981", background: "#10b98118", border: "1px solid #10b98133", padding: "3px 9px", borderRadius: "4px" }}>✓ READY</span>
  );
  return <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#ef4444" }}>ERROR</span>;
}

// ── Single course row with delete ─────────────────────────────────────────

function CourseRow({ course, cls, token, onDeleted }) {
  const [confirm, setConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    await fetch(`${API}/teacher/classes/${cls.id}/ai-courses/${course.id}/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    onDeleted();
  }

  return (
    <div style={{ background: "#0d0d0d", border: `1px solid ${course.status === "READY" ? cls.color + "44" : "rgba(255,255,255,0.07)"}`, borderRadius: "10px", padding: "16px 20px", display: "flex", alignItems: "center", gap: "16px", transition: "border-color 0.3s" }}>
      <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: cls.color + "18", border: `1px solid ${cls.color}33`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", flexShrink: 0 }}>
        📄
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: "#fff", fontSize: "14px", fontWeight: 700, fontFamily: "'Georgia', serif", marginBottom: "4px" }}>{course.title}</div>
        <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace" }}>{course.filename}</div>
        {course.status === "PROCESSING" && (
          <div style={{ fontSize: "10px", fontFamily: "monospace", color: "#f59e0b", marginTop: "5px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", border: "2px solid #f59e0b", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
            AI assistant is preparing the lecture...
          </div>
        )}
        {course.status === "READY" && (
          <div style={{ fontSize: "10px", fontFamily: "monospace", color: "#10b981", marginTop: "5px" }}>
            ✓ Ready — {course.total_pages} pages processed
          </div>
        )}
      </div>
      <AIStatusBadge status={course.status} />
      <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
        {confirm ? (
          <>
            <span style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.4)" }}>Delete?</span>
            <button onClick={handleDelete} disabled={deleting}
              style={{ padding: "4px 10px", background: "#ef4444", color: "#fff", border: "none", fontSize: "9px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: deleting ? "not-allowed" : "pointer", borderRadius: "3px" }}>
              {deleting ? "..." : "Yes"}
            </button>
            <button onClick={() => setConfirm(false)}
              style={{ padding: "4px 10px", background: "transparent", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.15)", fontSize: "9px", fontFamily: "monospace", fontWeight: 700, cursor: "pointer", borderRadius: "3px", textTransform: "uppercase" }}>
              No
            </button>
          </>
        ) : (
          <button onClick={() => setConfirm(true)}
            style={{ padding: "4px 10px", background: "transparent", color: "rgba(239,68,68,0.5)", border: "1px solid rgba(239,68,68,0.25)", fontSize: "9px", fontFamily: "monospace", fontWeight: 700, cursor: "pointer", borderRadius: "3px", textTransform: "uppercase", transition: "all 0.15s" }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(239,68,68,0.12)"; e.currentTarget.style.color = "#ef4444"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(239,68,68,0.5)"; }}>
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

// ── Lectures tab — unified upload ──────────────────────────────────────────

function LecturesTab({ cls, token }) {
  const [courses, setCourses]     = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver]   = useState(false);
  const fileInputRef              = useRef(null);

  useEffect(() => {
    function load() {
      fetch(`${API}/ai-courses/class/${cls.id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => { if (Array.isArray(data)) setCourses(data); })
        .catch(() => {});
    }
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [cls.id, token]);

  async function uploadFile(file) {
    if (!file || !file.name.endsWith(".pdf")) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", file.name.replace(/\.pdf$/i, "").replace(/_/g, " "));
    const res = await fetch(`${API}/teacher/classes/${cls.id}/ai-courses/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (res.ok) {
      const course = await res.json();
      setCourses(prev => [course, ...prev]);
    }
    setUploading(false);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Hidden file input — always present */}
      <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={e => { uploadFile(e.target.files[0]); e.target.value = ""; }} disabled={uploading} />

      {courses.length === 0 ? (
        /* Full drag-and-drop zone when no courses yet */
        <div
          onDrop={e => { e.preventDefault(); setDragOver(false); uploadFile(e.dataTransfer.files[0]); }}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => !uploading && fileInputRef.current?.click()}
          style={{ border: `2px dashed ${dragOver ? cls.color : cls.color + "44"}`, borderRadius: "12px", padding: "32px", textAlign: "center", cursor: uploading ? "not-allowed" : "pointer", background: dragOver ? cls.color + "08" : "transparent", transition: "all 0.15s ease" }}
        >
          <div style={{ fontSize: "32px", marginBottom: "10px", opacity: 0.5 }}>📄</div>
          <div style={{ fontSize: "13px", fontFamily: "monospace", fontWeight: 700, color: uploading ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.6)", marginBottom: "4px" }}>
            {uploading ? "Uploading and starting AI processing..." : "Upload Course"}
          </div>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.2)" }}>
            {uploading ? "" : "Drag & drop a PDF or click to select"}
          </div>
        </div>
      ) : (
        /* Compact upload button when courses already exist */
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em" }}>
            {courses.length} COURSE{courses.length !== 1 ? "S" : ""}
          </span>
          <button
            onClick={() => !uploading && fileInputRef.current?.click()}
            disabled={uploading}
            style={{ display: "flex", alignItems: "center", gap: "7px", padding: "7px 14px", background: "transparent", border: `1px solid ${cls.color}66`, borderRadius: "7px", color: uploading ? "rgba(255,255,255,0.2)" : cls.color, fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.08em", cursor: uploading ? "not-allowed" : "pointer", transition: "background 0.15s" }}
            onMouseEnter={e => { if (!uploading) e.currentTarget.style.background = cls.color + "18"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
          >
            <span style={{ fontSize: "14px" }}>＋</span>
            {uploading ? "Uploading..." : "Upload Another Course"}
          </button>
        </div>
      )}

      {courses.map(course => (
        <CourseRow key={course.id} course={course} cls={cls} token={token}
          onDeleted={() => setCourses(prev => prev.filter(c => c.id !== course.id))}
        />
      ))}
    </div>
  );
}

// ── Edit Class Modal ───────────────────────────────────────────────────────

function EditClassModal({ cls, token, onClose, onSaved }) {
  const [name, setName] = useState(cls.name);
  const [teacherName, setTeacherName] = useState(cls.teacher_name);
  const [color, setColor] = useState(cls.color);
  const [icon, setIcon] = useState(cls.icon);
  const [saving, setSaving] = useState(false);
  const labelStyle = { fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", display: "block", marginBottom: "6px" };

  async function handleSave() {
    setSaving(true);
    const res = await fetch(`${API}/teacher/classes/${cls.id}/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name, teacher_name: teacherName, color, icon }),
    });
    if (res.ok) { const data = await res.json(); onSaved(data); onClose(); }
    setSaving(false);
  }

  return (
    <Modal title="Edit Class" onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div><label style={labelStyle}>Class Name</label><Input value={name} onChange={e => setName(e.target.value)} placeholder="Class Name" /></div>
        <div><label style={labelStyle}>Teacher Name</label><Input value={teacherName} onChange={e => setTeacherName(e.target.value)} placeholder="Teacher Name" /></div>
        <div>
          <label style={labelStyle}>Icon</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {ICONS.map(ic => <div key={ic} onClick={() => setIcon(ic)} style={{ width: "36px", height: "36px", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", cursor: "pointer", background: icon === ic ? color + "33" : "rgba(255,255,255,0.04)", border: `2px solid ${icon === ic ? color : "rgba(255,255,255,0.08)"}` }}>{ic}</div>)}
          </div>
        </div>
        <div>
          <label style={labelStyle}>Color</label>
          <div style={{ display: "flex", gap: "8px" }}>
            {COLORS.map(c => <div key={c} onClick={() => setColor(c)} style={{ width: "28px", height: "28px", borderRadius: "50%", background: c, cursor: "pointer", border: `3px solid ${color === c ? "#fff" : "transparent"}` }} />)}
          </div>
        </div>
        <Btn onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save Changes"}</Btn>
      </div>
    </Modal>
  );
}

// ── Quiz Tab ───────────────────────────────────────────────────────────────

function QuizTab({ cls, token }) {
  const [courses, setCourses]           = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [quizData, setQuizData]         = useState({});
  const pollTimers                      = useRef({});

  useEffect(() => {
    fetch(`${API}/ai-courses/class/${cls.id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          const ready = data.filter(c => c.status === "READY");
          setCourses(ready);
          ready.forEach(course => fetchQuizData(course.id));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingCourses(false));

    return () => { Object.values(pollTimers.current).forEach(clearInterval); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cls.id]);

  async function fetchQuizData(courseId) {
    try {
      const res = await fetch(
        `${API}/teacher/classes/${cls.id}/ai-courses/${courseId}/quiz-results/`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      setQuizData(prev => ({ ...prev, [courseId]: data }));
    } catch { /* silent */ }
  }

  async function handleGenerateQuiz(courseId) {
    setQuizData(prev => ({ ...prev, [courseId]: { ...prev[courseId], status: "GENERATING" } }));
    try {
      await fetch(
        `${API}/teacher/classes/${cls.id}/ai-courses/${courseId}/generate-quiz/`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } }
      );
    } catch { return; }

    pollTimers.current[courseId] = setInterval(async () => {
      await fetchQuizData(courseId);
      const current = await fetch(
        `${API}/teacher/classes/${cls.id}/ai-courses/${courseId}/quiz-results/`,
        { headers: { Authorization: `Bearer ${token}` } }
      ).then(r => r.json()).catch(() => null);
      if (current && (current.status === "READY" || current.status === "ERROR")) {
        clearInterval(pollTimers.current[courseId]);
        setQuizData(prev => ({ ...prev, [courseId]: current }));
      }
    }, 4000);
  }

  if (loadingCourses) {
    return (
      <div style={{ textAlign: "center", padding: "48px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>
        Loading courses...
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "48px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px", lineHeight: 1.8 }}>
        No ready AI courses in this class yet.<br />
        Upload and process a lecture PDF in the Lectures tab first.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {courses.map(course => {
        const qd = quizData[course.id];
        const isGenerating = qd?.status === "GENERATING" || qd?.status === "PENDING";
        const isReady      = qd?.status === "READY";
        const isError      = qd?.status === "ERROR";
        const notGenerated = !qd || qd.status === "NOT_GENERATED";
        const attempts     = qd?.attempts ?? [];

        return (
          <div key={course.id} style={{ background: "#111", border: `1px solid ${isReady ? cls.color + "33" : "rgba(255,255,255,0.07)"}`, borderRadius: "12px", overflow: "hidden" }}>

            {/* Course header */}
            <div style={{ padding: "16px 20px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px" }}>
              <div>
                <div style={{ color: "#fff", fontSize: "15px", fontWeight: 700, fontFamily: "'Georgia', serif", marginBottom: "3px" }}>{course.title}</div>
                <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>{course.total_pages} pages</div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
                {isReady && (
                  <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#10b981", background: "#10b98118", border: "1px solid #10b98133", padding: "3px 9px", borderRadius: "4px" }}>✓ QUIZ READY</span>
                )}
                {isGenerating && (
                  <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#f59e0b", background: "#f59e0b18", border: "1px solid #f59e0b33", padding: "3px 9px", borderRadius: "4px" }}>⏳ GENERATING...</span>
                )}
                {isError && (
                  <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#ef4444", background: "#ef444418", border: "1px solid #ef444433", padding: "3px 9px", borderRadius: "4px" }}>✗ ERROR</span>
                )}
                {(notGenerated || isError) && (
                  <Btn onClick={() => handleGenerateQuiz(course.id)} small color={cls.color}>
                    {isError ? "↻ Retry Quiz" : "⊕ Generate Quiz"}
                  </Btn>
                )}
                {isReady && (
                  <Btn onClick={() => handleGenerateQuiz(course.id)} small outline color={cls.color}>↻ Regenerate</Btn>
                )}
              </div>
            </div>

            {/* Attempts table */}
            {isReady && (
              <div style={{ padding: "16px 20px" }}>
                <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", letterSpacing: "0.15em", marginBottom: "12px" }}>
                  STUDENT RESULTS — {attempts.length} ATTEMPT{attempts.length !== 1 ? "S" : ""}
                </div>
                {attempts.length === 0 ? (
                  <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px", fontFamily: "monospace", textAlign: "center", padding: "24px" }}>
                    No students have taken the quiz yet.
                  </div>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", fontFamily: "monospace" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                          {["Student", "Email", "Score", "Correct", "Date"].map(h => (
                            <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: "9px", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", fontWeight: 700, textTransform: "uppercase" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {attempts.map((a, i) => (
                          <tr key={a.attempt_id} style={{ borderBottom: i < attempts.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)" }}>
                            <td style={{ padding: "10px 12px", color: "#fff" }}>{a.student_name}</td>
                            <td style={{ padding: "10px 12px", color: "rgba(255,255,255,0.4)" }}>{a.student_email}</td>
                            <td style={{ padding: "10px 12px" }}>
                              <span style={{ fontWeight: 700, color: a.score >= 70 ? "#10b981" : a.score >= 50 ? "#f59e0b" : "#ef4444" }}>{a.score}%</span>
                            </td>
                            <td style={{ padding: "10px 12px", color: "rgba(255,255,255,0.5)" }}>{a.correct_count} / {a.total}</td>
                            <td style={{ padding: "10px 12px", color: "rgba(255,255,255,0.35)" }}>
                              {new Date(a.completed_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {notGenerated && (
              <div style={{ padding: "20px", color: "rgba(255,255,255,0.2)", fontSize: "11px", fontFamily: "monospace", textAlign: "center" }}>
                No quiz generated yet. Click "Generate Quiz" to create one from this lecture&apos;s content.
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────

const TABS = ["Stream", "Classwork", "People", "Lectures", "Quiz"];

export default function TeacherClassDashboard() {
  const { classId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [cls, setCls] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("Stream");
  const [showEdit, setShowEdit] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetch(`${API}/teacher/classes/${classId}/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setCls(data); })
      .finally(() => setLoading(false));
  }, [classId, token]);

  async function handleDeleteClass() {
    setDeleting(true);
    await fetch(`${API}/teacher/classes/${classId}/`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
    navigate("/teacher/classes");
  }

  if (loading) return <div style={{ minHeight: "100vh", background: "#0a0a0a" }}><TeacherHeader user={user} /><div style={{ textAlign: "center", padding: "120px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Loading...</div></div>;
  if (!cls) return <div style={{ minHeight: "100vh", background: "#0a0a0a" }}><TeacherHeader user={user} /><div style={{ textAlign: "center", padding: "120px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>Class not found.</div></div>;

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <TeacherHeader user={user} />

      <div style={{ background: `linear-gradient(135deg, ${cls.color}18, ${cls.color}08)`, borderBottom: `1px solid ${cls.color}33` }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "28px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div style={{ width: "52px", height: "52px", borderRadius: "12px", background: cls.color + "22", border: `1px solid ${cls.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "24px" }}>{cls.icon}</div>
              <div>
                <h1 style={{ color: "#fff", margin: "0 0 4px", fontSize: "22px", fontWeight: 700 }}>{cls.name}</h1>
                <div style={{ color: "rgba(255,255,255,0.45)", fontSize: "12px", fontFamily: "monospace" }}>
                  {cls.teacher_name} · Code: <span style={{ color: cls.color }}>{cls.code}</span>
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <Btn onClick={() => setShowEdit(true)} outline>Edit</Btn>
              <Btn onClick={() => setShowDeleteConfirm(true)} danger outline>Delete Class</Btn>
            </div>
          </div>

          <div style={{ display: "flex", gap: "4px", marginTop: "24px", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} style={{ background: "transparent", border: "none", borderBottom: `2px solid ${activeTab === tab ? cls.color : "transparent"}`, color: activeTab === tab ? "#fff" : "rgba(255,255,255,0.4)", padding: "8px 18px 7px", fontSize: "13px", fontFamily: "monospace", fontWeight: activeTab === tab ? 700 : 400, cursor: "pointer", transition: "color 0.15s" }}
                onMouseEnter={e => { if (activeTab !== tab) e.currentTarget.style.color = "rgba(255,255,255,0.75)"; }}
                onMouseLeave={e => { if (activeTab !== tab) e.currentTarget.style.color = "rgba(255,255,255,0.4)"; }}
              >{tab}</button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "28px 24px" }}>
        {activeTab === "Stream"    && <StreamTab    cls={cls} token={token} onUpdate={setCls} />}
        {activeTab === "Classwork" && <ClassworkTab cls={cls} token={token} onUpdate={setCls} />}
        {activeTab === "People"    && <PeopleTab    cls={cls} token={token} onUpdate={setCls} />}
        {activeTab === "Lectures"  && <LecturesTab  cls={cls} token={token} />}
        {activeTab === "Quiz"      && <QuizTab      cls={cls} token={token} />}
      </div>

      {showEdit && (
        <EditClassModal cls={cls} token={token} onClose={() => setShowEdit(false)}
          onSaved={updated => setCls(prev => ({ ...prev, ...updated }))}
        />
      )}

      {showDeleteConfirm && (
        <Modal title={`Delete "${cls.name}"?`} onClose={() => setShowDeleteConfirm(false)}>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "13px", fontFamily: "monospace", lineHeight: 1.7, margin: "0 0 24px" }}>
            This will permanently delete the class, all assignments, lectures, announcements, and student enrollments. This cannot be undone.
          </p>
          <div style={{ display: "flex", gap: "10px" }}>
            <Btn onClick={() => setShowDeleteConfirm(false)} outline>Cancel</Btn>
            <Btn onClick={handleDeleteClass} danger disabled={deleting}>{deleting ? "Deleting..." : "Delete Forever"}</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}

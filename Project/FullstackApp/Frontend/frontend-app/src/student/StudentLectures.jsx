import { useState } from "react";
import { CLASSES, LECTURES } from "./mockData";

const FILE_ICONS = {
  pdf:  { icon: "PDF",  color: "#ef4444" },
  doc:  { icon: "DOC",  color: "#3b82f6" },
  docx: { icon: "DOC",  color: "#3b82f6" },
  zip:  { icon: "ZIP",  color: "#eab308" },
  png:  { icon: "IMG",  color: "#8b5cf6" },
  jpg:  { icon: "IMG",  color: "#8b5cf6" },
  py:   { icon: "PY",   color: "#10b981" },
  js:   { icon: "JS",   color: "#f97316" },
  txt:  { icon: "TXT",  color: "rgba(255,255,255,0.4)" },
};

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

function LectureCard({ lec, color }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      background: "#111111",
      border: `1px solid ${open ? color + "55" : "rgba(255,255,255,0.07)"}`,
      borderRadius: "10px", overflow: "hidden",
      transition: "border-color 0.15s ease",
    }}>
      {/* Row */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{ display: "flex", alignItems: "center", gap: "14px", padding: "16px 20px", cursor: "pointer" }}
      >
        <div style={{
          width: "38px", height: "38px", borderRadius: "8px", flexShrink: 0,
          background: color + "1a", border: `1px solid ${color}44`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "14px", color,
        }}>▶</div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: "#fff", fontSize: "14px", fontWeight: 600, fontFamily: "'Georgia', serif" }}>
            {lec.title}
          </div>
          <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", marginTop: "3px" }}>
            {lec.date} · {lec.duration}
            {lec.files.length > 0 && ` · ${lec.files.length} file${lec.files.length > 1 ? "s" : ""}`}
          </div>
        </div>

        <span style={{
          color: "rgba(255,255,255,0.25)", fontSize: "14px",
          transform: open ? "rotate(180deg)" : "rotate(0deg)",
          transition: "transform 0.2s ease", display: "inline-block", flexShrink: 0,
        }}>▾</span>
      </div>

      {/* Expanded */}
      {open && (
        <div style={{ padding: "0 20px 18px 72px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <p style={{
            color: "rgba(255,255,255,0.6)", fontSize: "13px",
            fontFamily: "'Georgia', serif", lineHeight: 1.7, margin: "14px 0 0",
          }}>
            {lec.description}
          </p>
          {lec.files.length > 0 && (
            <div style={{ marginTop: "14px" }}>
              <div style={{
                fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em",
                color: "rgba(255,255,255,0.25)", textTransform: "uppercase", marginBottom: "8px",
              }}>
                Attached Files
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {lec.files.map((f, i) => <FileChip key={i} name={f.name} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function StudentLectures() {
  const [activeClass, setActiveClass] = useState(CLASSES[0].id);

  const cls = CLASSES.find(c => c.id === activeClass);
  const lectures = LECTURES[activeClass] ?? [];

  return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "32px 24px" }}>

        {/* Page header */}
        <div style={{ marginBottom: "28px" }}>
          <h1 style={{ color: "#fff", fontWeight: 700, fontSize: "24px", margin: "0 0 6px 0" }}>Lectures</h1>
          <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>
            {lectures.length} lecture{lectures.length !== 1 ? "s" : ""} · {cls.teacher}
          </div>
        </div>

        {/* Class tabs */}
        <div style={{
          display: "flex", gap: "6px", flexWrap: "wrap",
          borderBottom: "1px solid rgba(255,255,255,0.07)",
          paddingBottom: "16px", marginBottom: "20px",
        }}>
          {CLASSES.map(c => (
            <button
              key={c.id}
              onClick={() => setActiveClass(c.id)}
              style={{
                display: "flex", alignItems: "center", gap: "7px",
                padding: "7px 14px",
                background: activeClass === c.id ? c.color + "18" : "transparent",
                border: `1px solid ${activeClass === c.id ? c.color + "66" : "rgba(255,255,255,0.1)"}`,
                color: activeClass === c.id ? c.color : "rgba(255,255,255,0.45)",
                fontSize: "12px", fontFamily: "monospace", fontWeight: activeClass === c.id ? 700 : 400,
                letterSpacing: "0.07em", cursor: "pointer", borderRadius: "6px",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={e => { if (activeClass !== c.id) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.25)"; e.currentTarget.style.color = "rgba(255,255,255,0.75)"; } }}
              onMouseLeave={e => { if (activeClass !== c.id) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "rgba(255,255,255,0.45)"; } }}
            >
              <span style={{ fontSize: "14px" }}>{c.icon}</span>
              {c.name}
              <span style={{
                fontSize: "10px", fontFamily: "monospace",
                color: activeClass === c.id ? c.color : "rgba(255,255,255,0.2)",
                background: activeClass === c.id ? c.color + "18" : "rgba(255,255,255,0.06)",
                padding: "1px 6px", borderRadius: "8px",
              }}>
                {(LECTURES[c.id] ?? []).length}
              </span>
            </button>
          ))}
        </div>

        {/* Lecture list */}
        {lectures.length === 0 ? (
          <div style={{
            background: "#111111", border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "10px", padding: "48px",
            textAlign: "center", color: "rgba(255,255,255,0.25)",
            fontSize: "13px", fontFamily: "monospace",
          }}>
            No lectures posted yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {lectures.map(lec => (
              <LectureCard key={lec.id} lec={lec} color={cls.color} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

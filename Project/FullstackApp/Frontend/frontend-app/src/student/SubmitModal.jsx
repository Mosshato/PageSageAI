import { useState, useRef } from "react";

const FILE_ICONS = {
  pdf:  { icon: "PDF", color: "#ef4444" },
  doc:  { icon: "DOC", color: "#3b82f6" },
  docx: { icon: "DOC", color: "#3b82f6" },
  zip:  { icon: "ZIP", color: "#eab308" },
  png:  { icon: "IMG", color: "#8b5cf6" },
  jpg:  { icon: "IMG", color: "#8b5cf6" },
  jpeg: { icon: "IMG", color: "#8b5cf6" },
  py:   { icon: "PY",  color: "#10b981" },
  js:   { icon: "JS",  color: "#f97316" },
  txt:  { icon: "TXT", color: "rgba(255,255,255,0.4)" },
};

function ext(name) { return name.split(".").pop().toLowerCase(); }

function fileStyle(name) {
  return FILE_ICONS[ext(name)] ?? { icon: ext(name).toUpperCase().slice(0, 3), color: "rgba(255,255,255,0.4)" };
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FileChip({ name, size, onRemove, accent }) {
  const [hovered, setHovered] = useState(false);
  const { icon, color } = fileStyle(name);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "flex", alignItems: "center", gap: "10px",
        background: "rgba(255,255,255,0.03)",
        border: `1px solid ${hovered ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.08)"}`,
        borderRadius: "6px", padding: "9px 12px",
        transition: "border-color 0.15s ease",
      }}
    >
      <div style={{
        width: "32px", height: "32px", borderRadius: "5px", flexShrink: 0,
        background: color + "22", border: `1px solid ${color}44`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "9px", fontWeight: 700, fontFamily: "monospace",
        color, letterSpacing: "0.05em",
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: "#fff", fontSize: "12px", fontFamily: "monospace",
          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
        }}>
          {name}
        </div>
        {size != null && (
          <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>
            {formatSize(size)}
          </div>
        )}
      </div>
      {onRemove && (
        <button
          onClick={onRemove}
          style={{
            background: "transparent", border: "none",
            color: "rgba(255,255,255,0.25)", cursor: "pointer",
            fontSize: "16px", lineHeight: 1, padding: "0 2px",
            transition: "color 0.15s ease", flexShrink: 0,
          }}
          onMouseEnter={e => { e.currentTarget.style.color = "#ef4444"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "rgba(255,255,255,0.25)"; }}
        >×</button>
      )}
    </div>
  );
}

export default function SubmitModal({ assignment, color, onClose, onSubmit }) {
  const [files, setFiles] = useState([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  function addFiles(newFiles) {
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      const toAdd = Array.from(newFiles).filter(f => !existing.has(f.name));
      return [...prev, ...toAdd];
    });
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  function handleSubmit() {
    onSubmit(files);
    onClose();
  }

  const teacherFiles = assignment.attachments ?? [];

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 300,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "#111111", border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: "12px", width: "100%", maxWidth: "500px",
          maxHeight: "90vh", overflowY: "auto",
          padding: "28px", display: "flex", flexDirection: "column", gap: "22px",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h3 style={{ color: "#fff", margin: "0 0 4px", fontSize: "17px", fontFamily: "'Georgia', serif", fontWeight: 700 }}>
              Submit Work
            </h3>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace" }}>
              {assignment.title} · {assignment.points} pts · Due {assignment.due}
            </div>
          </div>
          <span
            onClick={onClose}
            style={{ color: "rgba(255,255,255,0.35)", cursor: "pointer", fontSize: "22px", lineHeight: 1 }}
          >×</span>
        </div>

        {/* Teacher attachments */}
        {teacherFiles.length > 0 && (
          <div>
            <div style={{
              fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em",
              color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "8px",
            }}>
              Attached by Teacher
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {teacherFiles.map((f, i) => (
                f.url
                  ? <a key={i} href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><FileChip name={f.name} size={null} /></a>
                  : <FileChip key={i} name={f.name} size={null} />
              ))}
            </div>
          </div>
        )}

        {/* Divider */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }} />

        {/* Drop zone */}
        <div>
          <div style={{
            fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em",
            color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "8px",
          }}>
            Your Work
          </div>

          <div
            onClick={() => inputRef.current.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${dragging ? color : "rgba(255,255,255,0.12)"}`,
              borderRadius: "8px", padding: "28px 20px",
              textAlign: "center", cursor: "pointer",
              background: dragging ? color + "08" : "transparent",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={e => { if (!dragging) e.currentTarget.style.borderColor = "rgba(255,255,255,0.25)"; }}
            onMouseLeave={e => { if (!dragging) e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"; }}
          >
            <div style={{ fontSize: "24px", marginBottom: "8px", opacity: 0.5 }}>↑</div>
            <div style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px", fontFamily: "monospace" }}>
              Drop files here or <span style={{ color }}>browse</span>
            </div>
            <div style={{ color: "rgba(255,255,255,0.25)", fontSize: "10px", fontFamily: "monospace", marginTop: "4px" }}>
              Any file type accepted
            </div>
          </div>
          <input
            ref={inputRef}
            type="file"
            multiple
            style={{ display: "none" }}
            onChange={e => addFiles(e.target.files)}
          />
        </div>

        {/* Queued files */}
        {files.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {files.map((f, i) => (
              <FileChip
                key={i}
                name={f.name}
                size={f.size}
                onRemove={() => setFiles(prev => prev.filter((_, j) => j !== i))}
                accent={color}
              />
            ))}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={onClose}
            style={{
              flex: 1, padding: "11px",
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "rgba(255,255,255,0.5)", fontSize: "11px",
              fontFamily: "monospace", fontWeight: 700,
              letterSpacing: "0.12em", textTransform: "uppercase",
              cursor: "pointer", borderRadius: "4px",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)"; e.currentTarget.style.color = "#fff"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"; e.currentTarget.style.color = "rgba(255,255,255,0.5)"; }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={files.length === 0}
            style={{
              flex: 2, padding: "11px",
              background: files.length === 0 ? "rgba(255,255,255,0.06)" : color,
              color: files.length === 0 ? "rgba(255,255,255,0.25)" : "#000",
              border: "none", fontSize: "11px", fontWeight: 700,
              fontFamily: "monospace", letterSpacing: "0.12em",
              textTransform: "uppercase",
              cursor: files.length === 0 ? "not-allowed" : "pointer",
              borderRadius: "4px", transition: "opacity 0.15s ease",
            }}
            onMouseEnter={e => { if (files.length > 0) e.currentTarget.style.opacity = "0.85"; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
          >
            Submit {files.length > 0 ? `(${files.length} file${files.length > 1 ? "s" : ""})` : ""}
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];

function assignmentStatus(a) {
  if (a.my_submission?.grade != null) return "graded";
  if (a.my_submission) return "submitted";
  return "pending";
}

const STATUS_COLOR = { pending: "#f97316", submitted: "#3b82f6", graded: "#10b981" };

function buildDueMap(assignments) {
  const map = {};
  assignments.forEach(a => {
    if (!a.due_date) return;
    // due_date is "YYYY-MM-DD"
    const [y, m, d] = a.due_date.split("-").map(Number);
    const key = `${y}-${m - 1}-${d}`;  // month is 0-indexed like JS Date
    if (!map[key]) map[key] = [];
    map[key].push(a);
  });
  return map;
}

function DayPopover({ items, anchorRect, onClose }) {
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const style = {
    position: "fixed",
    zIndex: 300,
    left: Math.min(anchorRect.left, window.innerWidth - 280),
    top: anchorRect.bottom + 6,
    width: "264px",
    background: "#1a1a1a",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "10px",
    boxShadow: "0 16px 48px rgba(0,0,0,0.6)",
    overflow: "hidden",
  };
  if (anchorRect.bottom + 6 + 260 > window.innerHeight) {
    style.top = "auto";
    style.bottom = window.innerHeight - anchorRect.top + 6;
  }

  return (
    <div ref={ref} style={style}>
      <div style={{ padding: "12px 14px 8px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
        {items.length} Assignment{items.length > 1 ? "s" : ""}
      </div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {items.map((a, i) => {
          const st = assignmentStatus(a);
          const sc = STATUS_COLOR[st];
          return (
            <div
              key={a.id}
              onClick={() => { navigate(`/student/classes/${a.class_obj}`); onClose(); }}
              style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px 14px", cursor: "pointer", borderBottom: i < items.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none", transition: "background 0.12s ease" }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
            >
              <div style={{ width: "3px", height: "32px", borderRadius: "2px", background: a.class_color, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: "#fff", fontSize: "12px", fontWeight: 600, fontFamily: "'Georgia', serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{a.title}</div>
                <div style={{ color: a.class_color, fontSize: "10px", fontFamily: "monospace", marginTop: "2px" }}>{a.class_name}</div>
              </div>
              <span style={{ fontSize: "9px", fontFamily: "monospace", letterSpacing: "0.08em", color: sc, background: sc + "18", border: `1px solid ${sc}33`, padding: "2px 6px", borderRadius: "3px", flexShrink: 0 }}>
                {st}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CalendarCell({ day, items, isToday, inMonth }) {
  const [anchorRect, setAnchorRect] = useState(null);
  if (!day) return <div style={{ background: "transparent" }} />;

  const hasDue = items.length > 0;
  const MAX_DOTS = 3;
  const visibleItems = items.slice(0, MAX_DOTS);
  const overflow = items.length - MAX_DOTS;

  return (
    <>
      <div
        onClick={e => { if (hasDue) setAnchorRect(e.currentTarget.getBoundingClientRect()); }}
        style={{ borderRadius: "6px", background: isToday ? "#f97316" : "transparent", border: hasDue && !isToday ? "1px solid rgba(255,255,255,0.1)" : "1px solid transparent", cursor: hasDue ? "pointer" : "default", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "4px 2px", gap: "3px", minHeight: "44px", transition: "background 0.12s ease", opacity: inMonth ? 1 : 0.25 }}
        onMouseEnter={e => { if (hasDue && !isToday) e.currentTarget.style.background = "rgba(255,255,255,0.06)"; }}
        onMouseLeave={e => { if (!isToday) e.currentTarget.style.background = "transparent"; }}
      >
        <span style={{ fontSize: "12px", fontFamily: "monospace", color: isToday ? "#000" : inMonth ? "#fff" : "rgba(255,255,255,0.3)", fontWeight: isToday ? 700 : 400, lineHeight: 1 }}>
          {day}
        </span>
        {hasDue && (
          <div style={{ display: "flex", gap: "2px", alignItems: "center", flexWrap: "wrap", justifyContent: "center" }}>
            {visibleItems.map((a, i) => (
              <div key={i} style={{ width: "5px", height: "5px", borderRadius: "50%", background: isToday ? "#000" : a.class_color, flexShrink: 0 }} />
            ))}
            {overflow > 0 && (
              <span style={{ fontSize: "8px", fontFamily: "monospace", color: isToday ? "#000" : "rgba(255,255,255,0.5)", lineHeight: 1 }}>+{overflow}</span>
            )}
          </div>
        )}
      </div>
      {anchorRect && <DayPopover items={items} anchorRect={anchorRect} onClose={() => setAnchorRect(null)} />}
    </>
  );
}

export default function StudentCalendar() {
  const { token } = useAuth();
  const today = new Date();
  const [current, setCurrent] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);

  function fetchAssignments() {
    fetch(`${API}/assignments/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(setAssignments)
      .catch(() => setAssignments([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchAssignments();
    window.addEventListener("focus", fetchAssignments);
    return () => window.removeEventListener("focus", fetchAssignments);
  }, [token]);

  const dueMap = useMemo(() => buildDueMap(assignments.filter(a => !a.my_submission && a.status === "pending")), [assignments]);

  const year = current.getFullYear();
  const month = current.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevMonthDays = new Date(year, month, 0).getDate();

  const cells = [];
  for (let i = 0; i < firstDay; i++) {
    cells.push({ day: prevMonthDays - firstDay + 1 + i, inMonth: false, month: month - 1, year });
  }
  for (let i = 1; i <= daysInMonth; i++) {
    cells.push({ day: i, inMonth: true, month, year });
  }
  while (cells.length < 42) {
    cells.push({ day: cells.length - firstDay - daysInMonth + 1, inMonth: false, month: month + 1, year });
  }

  const monthPending = Object.entries(dueMap)
    .filter(([key]) => { const [y, m] = key.split("-").map(Number); return y === year && m === month; })
    .flatMap(([, items]) => items)
    .filter(a => assignmentStatus(a) === "pending").length;

  // Unique classes for legend
  const classLegend = useMemo(() => {
    const seen = new Set();
    return assignments.filter(a => {
      if (seen.has(a.class_obj)) return false;
      seen.add(a.class_obj);
      return true;
    }).map(a => ({ id: a.class_obj, name: a.class_name, color: a.class_color }));
  }, [assignments]);

  return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <div style={{ maxWidth: "900px", margin: "0 auto", padding: "32px 24px" }}>

        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "28px" }}>
          <div>
            <h1 style={{ color: "#fff", fontWeight: 700, fontSize: "24px", margin: "0 0 6px 0" }}>Calendar</h1>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>
              {loading ? "Loading..." : monthPending > 0 ? `${monthPending} pending assignment${monthPending > 1 ? "s" : ""} this month` : "No pending assignments this month"}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button onClick={() => setCurrent(new Date(year, month - 1, 1))} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer", padding: "6px 14px", fontFamily: "monospace", fontSize: "16px", borderRadius: "4px", transition: "all 0.15s ease" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)"; e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "rgba(255,255,255,0.5)"; }}
            >‹</button>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: "15px", fontFamily: "monospace", letterSpacing: "0.08em", minWidth: "160px", textAlign: "center" }}>
              {MONTHS[month]} {year}
            </div>
            <button onClick={() => setCurrent(new Date(year, month + 1, 1))} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer", padding: "6px 14px", fontFamily: "monospace", fontSize: "16px", borderRadius: "4px", transition: "all 0.15s ease" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)"; e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "rgba(255,255,255,0.5)"; }}
            >›</button>
          </div>
        </div>

        <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            {DAYS.map(d => (
              <div key={d} style={{ textAlign: "center", padding: "12px 0", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.12em", color: "rgba(255,255,255,0.25)", textTransform: "uppercase" }}>{d}</div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "1px", background: "rgba(255,255,255,0.04)", padding: "1px" }}>
            {cells.map((cell, i) => {
              const key = `${cell.year}-${cell.month}-${cell.day}`;
              const items = dueMap[key] ?? [];
              const isToday = cell.inMonth && cell.day === today.getDate() && month === today.getMonth() && year === today.getFullYear();
              return (
                <div key={i} style={{ background: "#111111", padding: "3px" }}>
                  <CalendarCell day={cell.day} items={items} isToday={isToday} inMonth={cell.inMonth} />
                </div>
              );
            })}
          </div>
        </div>

        {classLegend.length > 0 && (
          <div style={{ display: "flex", gap: "20px", marginTop: "16px", flexWrap: "wrap", justifyContent: "flex-end" }}>
            {classLegend.map(cls => (
              <div key={cls.id} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: cls.color }} />
                <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace" }}>{cls.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useRef, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { AssignmentsProvider } from "./AssignmentsContext";
import { useAuth } from "../context/AuthContext";

function AccountDropdown({ user, onClose, onLogout, onAccount }) {
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose();
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  const initials = `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();

  return (
    <div ref={ref} style={{
      position: "absolute", top: "calc(100% + 10px)", right: 0,
      background: "#161616", border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: "10px", width: "240px", zIndex: 300,
      boxShadow: "0 16px 40px rgba(0,0,0,0.6)",
      overflow: "hidden",
    }}>
      {/* Triangle pointer */}
      <div style={{
        position: "absolute", top: "-6px", right: "13px",
        width: "10px", height: "10px",
        background: "#161616", border: "1px solid rgba(255,255,255,0.1)",
        borderRight: "none", borderBottom: "none",
        transform: "rotate(45deg)",
      }} />

      {/* User info */}
      <div style={{ padding: "16px 18px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "38px", height: "38px", borderRadius: "50%", background: "linear-gradient(135deg, #f97316, #ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, color: "#000", fontFamily: "monospace", flexShrink: 0 }}>
            {initials}
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: "#fff", fontSize: "13px", fontWeight: 600, fontFamily: "'Georgia', serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user.firstName} {user.lastName}
            </div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontFamily: "monospace", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user.email}
            </div>
          </div>
        </div>
        <div style={{ marginTop: "10px" }}>
          <span style={{ background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.25)", color: "#f97316", padding: "2px 8px", borderRadius: "10px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase" }}>
            {user.role}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div style={{ padding: "8px" }}>
        <button
          onClick={onAccount}
          style={{ width: "100%", textAlign: "left", padding: "9px 12px", background: "transparent", border: "none", color: "rgba(255,255,255,0.6)", fontSize: "12px", fontFamily: "monospace", cursor: "pointer", borderRadius: "6px", display: "flex", alignItems: "center", gap: "10px", transition: "all 0.15s ease" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.color = "#fff"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.6)"; }}
        >
          <span style={{ opacity: 0.5 }}>◉</span> My Account
        </button>
        <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", margin: "6px 0" }} />
        <button
          onClick={onLogout}
          style={{ width: "100%", textAlign: "left", padding: "9px 12px", background: "transparent", border: "none", color: "rgba(239,68,68,0.7)", fontSize: "12px", fontFamily: "monospace", cursor: "pointer", borderRadius: "6px", display: "flex", alignItems: "center", gap: "10px", transition: "all 0.15s ease" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(239,68,68,0.08)"; e.currentTarget.style.color = "#ef4444"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(239,68,68,0.7)"; }}
        >
          <span style={{ opacity: 0.7 }}>→</span> Log out
        </button>
      </div>
    </div>
  );
}

function Header() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const navItems = [
    { label: "Home",        path: "/student" },
    { label: "Classes",     path: "/student/classes" },
    { label: "Assignments", path: "/student/assignments" },
    { label: "Calendar",    path: "/student/calendar" },
  ];

  const initials = user ? `${user.firstName[0]}${user.lastName[0]}`.toUpperCase() : "S";

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header style={{
      background: "#111111", borderBottom: "1px solid rgba(255,255,255,0.07)",
      padding: "0 24px", height: "60px", display: "flex", alignItems: "center",
      justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
        <div onClick={() => navigate("/student")} style={{ cursor: "pointer" }}>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>Page</span>
          <span style={{ color: "#f97316", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>Sage</span>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "18px", letterSpacing: "-1px", fontFamily: "'Georgia', serif" }}>AI</span>
        </div>
        <nav style={{ display: "flex", gap: "4px" }}>
          {navItems.map(({ label, path }) => {
            const active = pathname === path;
            return (
              <button key={label} onClick={() => navigate(path)} style={{
                background: active ? "rgba(249,115,22,0.1)" : "transparent",
                color: active ? "#f97316" : "rgba(255,255,255,0.45)",
                border: "none", padding: "6px 14px", fontSize: "13px",
                fontFamily: "monospace", cursor: "pointer", borderRadius: "4px", transition: "all 0.2s ease",
              }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.color = "#fff"; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.45)"; }}
              >{label}</button>
            );
          })}
        </nav>
      </div>

      {/* Avatar + dropdown */}
      <div style={{ position: "relative" }}>
        <div
          onClick={() => setDropdownOpen(o => !o)}
          style={{
            width: "32px", height: "32px", borderRadius: "50%",
            background: dropdownOpen ? "linear-gradient(135deg, #ea580c, #c2410c)" : "linear-gradient(135deg, #f97316, #ea580c)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "12px", fontWeight: 700, color: "#000", cursor: "pointer",
            fontFamily: "monospace", transition: "background 0.2s ease",
            outline: dropdownOpen ? "2px solid rgba(249,115,22,0.4)" : "none",
            outlineOffset: "2px",
          }}
        >
          {initials}
        </div>

        {dropdownOpen && user && (
          <AccountDropdown
            user={user}
            onClose={() => setDropdownOpen(false)}
            onLogout={handleLogout}
            onAccount={() => { navigate("/student/account"); setDropdownOpen(false); }}
          />
        )}
      </div>
    </header>
  );
}

export default function StudentLayout() {
  return (
    <AssignmentsProvider>
      <Header />
      <Outlet />
    </AssignmentsProvider>
  );
}

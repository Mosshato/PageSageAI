import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [role, setRole] = useState("student");
  const [focused, setFocused] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const inputStyle = (name) => ({
    width: "100%", padding: "14px 16px",
    background: focused === name ? "rgba(249,115,22,0.06)" : "rgba(255,255,255,0.03)",
    border: `1px solid ${focused === name ? "#f97316" : "rgba(255,255,255,0.1)"}`,
    color: "#ffffff", fontSize: "14px", fontFamily: "monospace", outline: "none",
    transition: "border 0.2s ease, background 0.2s ease",
    boxSizing: "border-box", letterSpacing: "0.05em",
  });

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.message || "Login failed");
        return;
      }
      login(data.token, data.refresh, data.user);
      navigate(data.user.role === "teacher" ? "/teacher" : "/student");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#0a0a0a", display: "flex",
      alignItems: "center", justifyContent: "center",
      fontFamily: "'Georgia', serif", position: "relative", overflow: "hidden",
    }}>
      <div style={{ position: "absolute", top: 0, right: 0, width: "400px", height: "400px", background: "radial-gradient(circle, rgba(249,115,22,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, width: "300px", height: "300px", background: "radial-gradient(circle, rgba(249,115,22,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ width: "100%", maxWidth: "420px", padding: "0 24px", zIndex: 1 }}>

        <div onClick={() => navigate("signup")} style={{ marginBottom: "48px", cursor: "pointer", display: "inline-block" }}>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>Page</span>
          <span style={{ color: "#f97316", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>Sage</span>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>AI</span>
        </div>

        <div style={{ marginBottom: "36px" }}>
          <h2 style={{ margin: "0 0 8px", color: "#ffffff", fontSize: "32px", fontWeight: 900, letterSpacing: "-1px" }}>Welcome back.</h2>
          <p style={{ margin: 0, color: "rgba(255,255,255,0.35)", fontSize: "13px", fontFamily: "monospace" }}>Sign in to continue your journey</p>
        </div>

        <div style={{ display: "flex", marginBottom: "28px", border: "1px solid rgba(255,255,255,0.1)", overflow: "hidden" }}>
          {["student", "teacher"].map(r => (
            <button key={r} onClick={() => setRole(r)} style={{
              flex: 1, padding: "10px",
              background: role === r ? "#f97316" : "transparent",
              color: role === r ? "#000" : "rgba(255,255,255,0.4)",
              border: "none", cursor: "pointer", fontSize: "11px", fontFamily: "monospace",
              fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase", transition: "all 0.2s ease",
            }}>
              {r}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <label style={{ display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Email</label>
            <input
              type="email"
              placeholder="you@school.edu"
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={inputStyle("email")}
              onFocus={() => setFocused("email")}
              onBlur={() => setFocused(null)}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={inputStyle("password")}
              onFocus={() => setFocused("password")}
              onBlur={() => setFocused(null)}
            />
          </div>
          <div style={{ textAlign: "right", marginTop: "-4px" }}>
            <span style={{ fontSize: "11px", color: "#f97316", fontFamily: "monospace", cursor: "pointer" }}>Forgot password?</span>
          </div>
          <button
            type="submit"
            disabled={submitting}
            style={{
              marginTop: "8px", padding: "15px", background: "#f97316", color: "#000",
              border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace",
              letterSpacing: "0.2em", textTransform: "uppercase", cursor: submitting ? "not-allowed" : "pointer",
              opacity: submitting ? 0.7 : 1,
            }}
            onMouseEnter={e => { if (!submitting) e.currentTarget.style.opacity = "0.85"; }}
            onMouseLeave={e => { if (!submitting) e.currentTarget.style.opacity = "1"; }}
          >
            {submitting ? "Signing in…" : `Sign In as ${role.charAt(0).toUpperCase() + role.slice(1)}`}
          </button>
          {error && (
            <p style={{ margin: 0, color: "#f87171", fontSize: "11px", fontFamily: "monospace" }}>{error}</p>
          )}
        </form>

        <div style={{ display: "flex", alignItems: "center", margin: "28px 0", gap: "12px" }}>
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.08)" }} />
          <span style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.2)", letterSpacing: "0.1em" }}>OR</span>
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.08)" }} />
        </div>

        <p style={{ textAlign: "center", margin: 0, fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>
          No account?{" "}
          <span onClick={() => navigate("/signup")} style={{ color: "#f97316", cursor: "pointer" }}>Sign up</span>
        </p>
      </div>
    </div>
  );
}

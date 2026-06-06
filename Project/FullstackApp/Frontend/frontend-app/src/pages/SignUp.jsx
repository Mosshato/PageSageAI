import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function SignUp() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [role, setRole] = useState("student");
  const [focused, setFocused] = useState(null);
  const [step, setStep] = useState(1);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const inputStyle = (name) => ({
    width: "100%", padding: "14px 16px",
    background: focused === name ? "rgba(249,115,22,0.06)" : "rgba(255,255,255,0.03)",
    border: `1px solid ${focused === name ? "#f97316" : "rgba(255,255,255,0.1)"}`,
    color: "#ffffff", fontSize: "14px", fontFamily: "monospace", outline: "none",
    transition: "border 0.2s ease, background 0.2s ease",
    boxSizing: "border-box", letterSpacing: "0.05em",
  });

  async function handleCreateAccount(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/signup/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firstName, lastName, email, password, role }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.message || "Sign up failed");
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
      <div style={{ position: "absolute", bottom: 0, right: 0, width: "500px", height: "500px", background: "radial-gradient(circle, rgba(249,115,22,0.07) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: "calc(50% - 260px)", top: 0, bottom: 0, width: "1px", background: "linear-gradient(180deg, transparent, rgba(249,115,22,0.1), transparent)", pointerEvents: "none" }} />

      <div style={{ width: "100%", maxWidth: "420px", padding: "0 24px", zIndex: 1 }}>

        <div onClick={() => navigate("welcome")} style={{ marginBottom: "48px", cursor: "pointer", display: "inline-block" }}>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>Page</span>
          <span style={{ color: "#f97316", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>Sage</span>
          <span style={{ color: "#ffffff", fontWeight: 900, fontSize: "22px", letterSpacing: "-1px" }}>AI</span>
        </div>

        <div style={{ display: "flex", gap: "6px", marginBottom: "32px" }}>
          {[1, 2].map(s => (
            <div key={s} style={{ height: "2px", flex: 1, background: s <= step ? "#f97316" : "rgba(255,255,255,0.1)", transition: "background 0.3s ease" }} />
          ))}
        </div>

        <div style={{ marginBottom: "32px" }}>
          <h2 style={{ margin: "0 0 8px", color: "#ffffff", fontSize: "32px", fontWeight: 900, letterSpacing: "-1px" }}>
            {step === 1 ? "Join PageSageAI." : "Almost there."}
          </h2>
          <p style={{ margin: 0, color: "rgba(255,255,255,0.35)", fontSize: "13px", fontFamily: "monospace" }}>
            {step === 1 ? "Step 1 — choose your role" : "Step 2 — your credentials"}
          </p>
        </div>

        {step === 1 && (
          <div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "32px" }}>
              {["student", "teacher"].map(r => (
                <div key={r} onClick={() => setRole(r)} style={{
                  padding: "20px 24px",
                  border: `1px solid ${role === r ? "#f97316" : "rgba(255,255,255,0.1)"}`,
                  background: role === r ? "rgba(249,115,22,0.06)" : "transparent",
                  cursor: "pointer", transition: "all 0.2s ease",
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                }}>
                  <div>
                    <div style={{ color: role === r ? "#f97316" : "#fff", fontWeight: 700, fontSize: "15px", marginBottom: "4px" }}>
                      {r.charAt(0).toUpperCase() + r.slice(1)}
                    </div>
                    <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "11px", fontFamily: "monospace" }}>
                      {r === "student" ? "Access classes, assignments & AI tools" : "Create classrooms & manage students"}
                    </div>
                  </div>
                  <div style={{
                    width: "18px", height: "18px", borderRadius: "50%", flexShrink: 0,
                    border: `2px solid ${role === r ? "#f97316" : "rgba(255,255,255,0.2)"}`,
                    background: role === r ? "#f97316" : "transparent", transition: "all 0.2s ease",
                  }} />
                </div>
              ))}
            </div>
            <button onClick={() => setStep(2)} style={{
              width: "100%", padding: "15px", background: "#f97316", color: "#000",
              border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace",
              letterSpacing: "0.2em", textTransform: "uppercase", cursor: "pointer",
            }}>
              Continue as {role.charAt(0).toUpperCase() + role.slice(1)} →
            </button>
          </div>
        )}

        {step === 2 && (
          <form onSubmit={handleCreateAccount} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", gap: "12px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>First Name</label>
                <input
                  placeholder="John"
                  value={firstName}
                  onChange={e => setFirstName(e.target.value)}
                  style={inputStyle("first")}
                  onFocus={() => setFocused("first")}
                  onBlur={() => setFocused(null)}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", marginBottom: "6px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.2em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Last Name</label>
                <input
                  placeholder="Doe"
                  value={lastName}
                  onChange={e => setLastName(e.target.value)}
                  style={inputStyle("last")}
                  onFocus={() => setFocused("last")}
                  onBlur={() => setFocused(null)}
                />
              </div>
            </div>
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
            <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
              <button type="button" onClick={() => setStep(1)} style={{
                padding: "15px 20px", background: "transparent", color: "rgba(255,255,255,0.35)",
                border: "1px solid rgba(255,255,255,0.1)", fontSize: "12px", fontFamily: "monospace",
                letterSpacing: "0.1em", cursor: "pointer",
              }}>← Back</button>
              <button
                type="submit"
                disabled={submitting}
                style={{
                  flex: 1, padding: "15px", background: "#f97316", color: "#000",
                  border: "none", fontSize: "12px", fontWeight: 700, fontFamily: "monospace",
                  letterSpacing: "0.2em", textTransform: "uppercase", cursor: submitting ? "not-allowed" : "pointer",
                  opacity: submitting ? 0.7 : 1,
                }}
              >
                {submitting ? "Creating…" : "Create Account"}
              </button>
            </div>
            {error && (
              <p style={{ margin: 0, color: "#f87171", fontSize: "11px", fontFamily: "monospace" }}>{error}</p>
            )}
          </form>
        )}

        <p style={{ textAlign: "center", marginTop: "28px", fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>
          Already have an account?{" "}
          <span onClick={() => navigate("/login")} style={{ color: "#f97316", cursor: "pointer" }}>Sign in</span>
        </p>
      </div>
    </div>
  );
}

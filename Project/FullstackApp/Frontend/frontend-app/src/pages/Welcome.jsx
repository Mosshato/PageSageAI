import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";     // ← add this import

export default function Welcome() {
  const navigate = useNavigate();  
  const [visible, setVisible] = useState(false);
  const [btnVisible, setBtnVisible] = useState(false);
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const p = Array.from({ length: 28 }, () => ({
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 20 + 15,
      opacity: Math.random() * 0.5 + 0.1,
    }));
    setParticles(p);
    setTimeout(() => setVisible(true), 100);
    setTimeout(() => setBtnVisible(true), 1200);
  }, []);

  const name = "PageSageAI";

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
      overflow: "hidden",
      fontFamily: "'Georgia', serif",
    }}>
      {particles.map((p, i) => (
        <div key={i} style={{
          position: "absolute",
          left: `${p.x}%`,
          top: `${p.y}%`,
          width: `${p.size}px`,
          height: `${p.size}px`,
          borderRadius: "50%",
          background: "#f97316",
          opacity: p.opacity,
          animation: `floatUp ${p.speed}s linear infinite`,
          animationDelay: `${-Math.random() * p.speed}s`,
        }} />
      ))}

      <div style={{
        position: "absolute", width: "700px", height: "700px", borderRadius: "50%",
        background: "radial-gradient(circle, rgba(249,115,22,0.12) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div style={{
        position: "absolute", top: "50%", left: "0", right: "0", height: "1px",
        background: "linear-gradient(90deg, transparent, rgba(249,115,22,0.15), transparent)",
        transform: "translateY(-80px)",
      }} />

      <div style={{
        textAlign: "center", zIndex: 1,
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(40px)",
        transition: "opacity 1s ease, transform 1s ease",
      }}>
        <div style={{ marginBottom: "8px", letterSpacing: "0.3em", fontSize: "11px", color: "#f97316", textTransform: "uppercase", fontFamily: "monospace" }}>
          AI-Powered Virtual Classroom
        </div>

        <h1 style={{ margin: 0, lineHeight: 1 }}>
          {name.split("").map((char, i) => (
            <span key={i} style={{
              display: "inline-block",
              fontSize: char === char.toUpperCase() && char !== char.toLowerCase() ? "clamp(64px, 12vw, 130px)" : "clamp(60px, 11vw, 120px)",
              fontWeight: 900,
              color: i < 4 ? "#ffffff" : i < 8 ? "#f97316" : "#ffffff",
              opacity: visible ? 1 : 0,
              transform: visible ? "translateY(0) rotateX(0deg)" : "translateY(60px) rotateX(40deg)",
              transition: `opacity 0.6s ease ${i * 0.07}s, transform 0.6s ease ${i * 0.07}s`,
              textShadow: i >= 4 && i < 8 ? "0 0 40px rgba(249,115,22,0.4)" : "none",
              letterSpacing: "-2px",
              fontFamily: "'Georgia', serif",
            }}>
              {char}
            </span>
          ))}
        </h1>

        <div style={{
          height: "2px",
          background: "linear-gradient(90deg, transparent, #f97316, transparent)",
          opacity: visible ? 1 : 0,
          transition: "opacity 1s ease 0.9s",
          width: "clamp(300px, 50vw, 600px)",
          margin: "16px auto 0",
        }} />

        <p style={{
          color: "rgba(255,255,255,0.35)", fontSize: "15px", marginTop: "20px",
          letterSpacing: "0.08em", fontFamily: "monospace",
          opacity: visible ? 1 : 0, transition: "opacity 1s ease 1s",
        }}>
          Learn. Teach. Evolve.
        </p>
      </div>

      <div style={{
        marginTop: "56px", zIndex: 1,
        opacity: btnVisible ? 1 : 0,
        transform: btnVisible ? "translateY(0)" : "translateY(20px)",
        transition: "opacity 0.7s ease, transform 0.7s ease",
      }}>
        <button
          onClick={() => navigate("login")}
          style={{
            padding: "16px 48px", fontSize: "13px", fontWeight: 600,
            letterSpacing: "0.2em", textTransform: "uppercase", fontFamily: "monospace",
            background: "transparent", color: "#f97316", border: "1px solid #f97316",
            cursor: "pointer", transition: "color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease",
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = "#000";
            e.currentTarget.style.background = "#f97316";
            e.currentTarget.style.boxShadow = "0 0 40px rgba(249,115,22,0.4)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = "#f97316";
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          Try PageSageAI
        </button>
      </div>

      <div style={{
        position: "absolute", bottom: "32px", display: "flex", gap: "24px",
        opacity: btnVisible ? 0.4 : 0, transition: "opacity 0.7s ease 0.3s",
        fontSize: "11px", letterSpacing: "0.2em", fontFamily: "monospace",
        color: "#ffffff", textTransform: "uppercase",
      }}>
        <span onClick={() => navigate("login")} style={{ cursor: "pointer" }}>Login</span>
        <span style={{ color: "#f97316" }}>·</span>
        <span onClick={() => navigate("signup")} style={{ cursor: "pointer" }}>Sign Up</span>
      </div>

      <style>{`
        @keyframes floatUp {
          0% { transform: translateY(100vh) scale(0); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 0.3; }
          100% { transform: translateY(-100px) scale(1); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: "#111111", border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: "10px", padding: "24px 28px",
    }}>
      <div style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase", marginBottom: "12px" }}>{label}</div>
      <div style={{ fontSize: "36px", fontWeight: 900, color: color || "#f97316", fontFamily: "monospace", letterSpacing: "-1px" }}>{value ?? "—"}</div>
      {sub && <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginTop: "6px" }}>{sub}</div>}
    </div>
  );
}

function GradeBar({ cls }) {
  const pct = cls.avg_grade ?? 0;
  return (
    <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "18px 22px", display: "flex", alignItems: "center", gap: "16px" }}>
      <span style={{ fontSize: "22px", flexShrink: 0 }}>{cls.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ color: "#fff", fontSize: "13px", fontWeight: 600, fontFamily: "'Georgia', serif" }}>{cls.class_name}</span>
          <span style={{ fontSize: "13px", fontWeight: 700, fontFamily: "monospace", color: cls.avg_grade != null ? cls.color : "rgba(255,255,255,0.2)" }}>
            {cls.avg_grade != null ? `${cls.avg_grade}%` : "No grades yet"}
          </span>
        </div>
        <div style={{ height: "4px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, background: cls.color, borderRadius: "2px", transition: "width 0.6s ease" }} />
        </div>
        <div style={{ marginTop: "5px", fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.25)" }}>
          {cls.graded_count} assignment{cls.graded_count !== 1 ? "s" : ""} graded
        </div>
      </div>
    </div>
  );
}

export default function StudentAccount() {
  const { user, token } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/account/stats/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, [token]);

  const initials = user ? `${user.firstName[0]}${user.lastName[0]}`.toUpperCase() : "?";
  const joinDate = new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const avgColor = stats?.avg_grade >= 90 ? "#10b981" : stats?.avg_grade >= 75 ? "#f97316" : stats?.avg_grade != null ? "#ef4444" : "rgba(255,255,255,0.3)";

  return (
    <div style={{ minHeight: "calc(100vh - 60px)", background: "#0a0a0a", fontFamily: "'Georgia', serif" }}>
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "40px 24px" }}>

        {/* Profile header */}
        <div style={{ display: "flex", alignItems: "center", gap: "24px", marginBottom: "40px", padding: "28px 32px", background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px" }}>
          <div style={{ width: "64px", height: "64px", borderRadius: "50%", background: "linear-gradient(135deg, #f97316, #ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "22px", fontWeight: 700, color: "#000", fontFamily: "monospace", flexShrink: 0 }}>
            {initials}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#fff", fontSize: "20px", fontWeight: 700, marginBottom: "4px" }}>
              {user?.firstName} {user?.lastName}
            </div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>{user?.email}</div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px" }}>
              <span style={{ background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.3)", color: "#f97316", padding: "2px 8px", borderRadius: "10px", fontSize: "10px", fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                {user?.role}
              </span>
              <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "11px", fontFamily: "monospace" }}>Member since {joinDate}</span>
            </div>
          </div>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "60px", color: "rgba(255,255,255,0.2)", fontFamily: "monospace", fontSize: "12px" }}>
            Loading stats...
          </div>
        )}

        {!loading && stats?.empty && (
          <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "60px", textAlign: "center" }}>
            <div style={{ fontSize: "32px", marginBottom: "16px" }}>📚</div>
            <div style={{ color: "#fff", fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>No classes yet</div>
            <div style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px", fontFamily: "monospace" }}>{stats.message}</div>
          </div>
        )}

        {!loading && stats && !stats.empty && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "28px" }}>
              <StatCard label="Classes Enrolled" value={stats.classes_count} sub="active this semester" color="#f97316" />
              <StatCard label="Assignments Done" value={`${stats.assignments_completed}/${stats.assignments_total}`} sub={`${stats.assignments_pending} still pending`} color="#10b981" />
              <StatCard label="Average Grade" value={stats.avg_grade != null ? `${stats.avg_grade}%` : "N/A"} sub={stats.avg_grade != null ? "across all graded work" : "no grades yet"} color={avgColor} />
            </div>

            {stats.assignments_total > 0 && (
              <div style={{ background: "#111111", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px 24px", marginBottom: "28px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Overall Progress</span>
                  <span style={{ fontSize: "12px", fontFamily: "monospace", color: "#f97316", fontWeight: 700 }}>
                    {Math.round((stats.assignments_completed / stats.assignments_total) * 100)}%
                  </span>
                </div>
                <div style={{ height: "6px", background: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${(stats.assignments_completed / stats.assignments_total) * 100}%`, background: "linear-gradient(90deg, #f97316, #ea580c)", borderRadius: "3px", transition: "width 0.8s ease" }} />
                </div>
              </div>
            )}

            <div>
              <div style={{ fontSize: "11px", fontFamily: "monospace", letterSpacing: "0.15em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase", marginBottom: "14px" }}>Grade per Class</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {stats.grades_per_class.map(cls => (
                  <GradeBar key={cls.class_id} cls={cls} />
                ))}
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  );
}

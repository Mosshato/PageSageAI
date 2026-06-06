import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ requiredRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh", background: "#0a0a0a",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <div style={{
          width: "32px", height: "32px", borderRadius: "50%",
          border: "2px solid rgba(249,115,22,0.2)",
          borderTopColor: "#f97316",
          animation: "spin 0.7s linear infinite",
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to={user.role === "teacher" ? "/teacher" : "/student"} replace />;
  }

  return <Outlet />;
}

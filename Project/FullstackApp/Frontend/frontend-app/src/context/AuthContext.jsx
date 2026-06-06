import { createContext, useContext, useState, useEffect, useRef } from "react";

const AuthContext = createContext(null);

const API = "http://localhost:8000/api";
// Cu cat timp inainte de expirarea access token-ului facem refresh (30 secunde)
const REFRESH_BEFORE_MS = 30_000;

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [token, setToken]     = useState(null);
  const [loading, setLoading] = useState(true);
  const refreshTimerRef       = useRef(null);

  // Decodifica payload-ul JWT fara verificare (nu avem secret-ul pe frontend)
  function decodePayload(tok) {
    return JSON.parse(atob(tok.split(".")[1]));
  }

  // Programeaza un refresh silentios cu 30s inainte de expirarea access token-ului
  function scheduleRefresh(accessToken) {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    try {
      const { exp } = decodePayload(accessToken);
      const msUntilRefresh = exp * 1000 - Date.now() - REFRESH_BEFORE_MS;

      if (msUntilRefresh <= 0) {
        // Token-ul e deja expirat sau aproape — incercam refresh imediat
        silentRefresh();
      } else {
        refreshTimerRef.current = setTimeout(silentRefresh, msUntilRefresh);
      }
    } catch {
      logout();
    }
  }

  // Face request catre /api/auth/token/refresh/ cu refresh token-ul din localStorage
  // Daca reuseste → salveaza noul access token si reprogrameaza refresh-ul
  // Daca esueaza (refresh token expirat) → logout
  async function silentRefresh() {
    const refreshToken = localStorage.getItem("pagesage_refresh");
    if (!refreshToken) { logout(); return; }

    try {
      const res = await fetch(`${API}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
      });
      if (!res.ok) throw new Error("Refresh failed");
      const data = await res.json();
      // Django simplejwt returneaza { access: "..." }
      localStorage.setItem("pagesage_token", data.access);
      setToken(data.access);
      scheduleRefresh(data.access);  // reprogrameaza pentru urmatorul ciclu
    } catch {
      logout();
    }
  }

  function login(accessToken, refreshToken, usr) {
    localStorage.setItem("pagesage_token", accessToken);
    localStorage.setItem("pagesage_refresh", refreshToken);
    localStorage.setItem("pagesage_user", JSON.stringify(usr));
    setToken(accessToken);
    setUser(usr);
    scheduleRefresh(accessToken);
  }

  function logout() {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    localStorage.removeItem("pagesage_token");
    localStorage.removeItem("pagesage_refresh");
    localStorage.removeItem("pagesage_user");
    setToken(null);
    setUser(null);
  }

  // La montarea componentei: verifica daca exista o sesiune salvata
  useEffect(() => {
    async function restore() {
      const savedToken   = localStorage.getItem("pagesage_token");
      const savedRefresh = localStorage.getItem("pagesage_refresh");
      if (!savedToken || !savedRefresh) { setLoading(false); return; }

      try {
        // Verificam daca access token-ul e inca valid
        const res = await fetch(`${API}/auth/me/`, {
          headers: { Authorization: `Bearer ${savedToken}` },
        });

        if (res.ok) {
          // Token valid — restauram sesiunea si programam refresh-ul
          const data = await res.json();
          setToken(savedToken);
          setUser(data.user);
          scheduleRefresh(savedToken);
        } else {
          // Access token expirat — incercam sa il reinnuim cu refresh token-ul
          const refRes = await fetch(`${API}/auth/token/refresh/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: savedRefresh }),
          });
          if (!refRes.ok) throw new Error("Refresh expired");
          const refData = await refRes.json();
          localStorage.setItem("pagesage_token", refData.access);

          const meRes = await fetch(`${API}/auth/me/`, {
            headers: { Authorization: `Bearer ${refData.access}` },
          });
          if (!meRes.ok) throw new Error("Me failed");
          const meData = await meRes.json();
          setToken(refData.access);
          setUser(meData.user);
          scheduleRefresh(refData.access);
        }
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    }
    restore();
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

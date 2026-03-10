import { createContext, useContext, useEffect, useState } from "react";
import { DecodedToken, UserRole } from "./auth.types";

interface AuthState {
  token: string | null;
  role: UserRole | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("access_token");
    if (stored) applyToken(stored);
  }, []);

  function applyToken(jwt: string) {
    const payload = JSON.parse(atob(jwt.split(".")[1])) as DecodedToken;
    setToken(jwt);
    setRole(payload.role);
    localStorage.setItem("access_token", jwt);
  }

  function login(jwt: string) {
    applyToken(jwt);
  }

  function logout() {
    setToken(null);
    setRole(null);
    localStorage.removeItem("access_token");
  }

  return (
    <AuthContext.Provider value={{ token, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

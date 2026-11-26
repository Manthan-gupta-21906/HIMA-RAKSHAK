import { createContext, useContext, useState, type ReactNode } from "react";
import type { AuthUser, LoginCredentials, UserRole } from "../types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const STORAGE_KEY = "hima_rakshak_auth_user";

const DEMO_USERS: Record<UserRole, Omit<AuthUser, "email">> = {
  operator: {
    id: "usr-ddma-01",
    name: "M. Gupta",
    initials: "MG",
    role: "operator",
    station: "DDMA Control Room",
    district: "Srinagar",
  },
  field_officer: {
    id: "usr-sdrf-04",
    name: "Sub-Inspector R. Ahmed",
    initials: "RA",
    role: "field_officer",
    station: "SDRF Ground Unit 04",
    district: "Poonch - Surankote",
  },
  viewer: {
    id: "usr-sdma-09",
    name: "Dr. S. Lone",
    initials: "SL",
    role: "viewer",
    station: "J&K SDMA Advisory Desk",
    district: "Jammu",
  },
};

const AuthContext = createContext<AuthContextValue | null>(null);

function loadStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

/** Provides mock authentication state persisted in localStorage until backend auth is wired. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(loadStoredUser);

  const login = async ({ email, role }: LoginCredentials): Promise<void> => {
    const profile = DEMO_USERS[role];
    const nextUser: AuthUser = { ...profile, email: email.trim().toLowerCase() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: user !== null, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook to access current authentication state and actions. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getMeApi, loginApi, logoutApi } from "../api/auth";
import { AUTH_EXPIRED_EVENT, ApiError, clearToken, getStoredToken } from "../api/client";
import type { AuthUser, LoginCredentials, UserRole } from "../types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const STORAGE_KEY = "hima_rakshak_auth_user";

const VALID_ROLES: ReadonlySet<UserRole> = new Set(["admin", "district_operator", "viewer"]);

const ROLE_PROFILES: Record<UserRole, Omit<AuthUser, "email">> = {
  admin: {
    id: "usr-admin-01",
    name: "System Administrator",
    initials: "AD",
    role: "admin",
    station: "SDMA Command Center",
    district: "Srinagar",
  },
  district_operator: {
    id: "usr-ddma-01",
    name: "M. Gupta",
    initials: "MG",
    role: "district_operator",
    station: "DDMA Control Room",
    district: "Srinagar",
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

function deriveInitials(name: string, fallback: string): string {
  const parts = name
    .trim()
    .split(/[\s._-]+/)
    .filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  if (parts.length === 1 && parts[0].length >= 2) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return fallback;
}

function loadStoredUser(): AuthUser | null {
  try {
    if (!getStoredToken()) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthUser;
    if (!parsed || !VALID_ROLES.has(parsed.role)) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function buildUserFromMe(username: string, role: UserRole, emailInput?: string): AuthUser {
  const profile = ROLE_PROFILES[role];
  const displayName = username.trim() || profile.name;
  return {
    ...profile,
    name: displayName,
    email: emailInput?.trim().toLowerCase() || username.trim().toLowerCase(),
    initials: deriveInitials(displayName, profile.initials),
    role,
  };
}

/** Provides authentication state backed by JWT tokens and server-verified roles. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(loadStoredUser);

  useEffect(() => {
    const handleAuthExpired = () => {
      localStorage.removeItem(STORAGE_KEY);
      setUser(null);
    };
    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, []);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) return;

    let active = true;
    getMeApi()
      .then((me) => {
        if (!active) return;
        const verified = buildUserFromMe(me.username, me.role, user?.email);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(verified));
        setUser(verified);
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          localStorage.removeItem(STORAGE_KEY);
          setUser(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = async ({ email, password }: LoginCredentials): Promise<void> => {
    const username = email.includes("@") ? email.split("@")[0].trim() : email.trim();

    await loginApi(username, password);
    try {
      const me = await getMeApi();
      const nextUser = buildUserFromMe(me.username, me.role, email);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
      setUser(nextUser);
    } catch (err) {
      clearToken();
      localStorage.removeItem(STORAGE_KEY);
      setUser(null);
      throw err;
    }
  };

  const logout = () => {
    logoutApi();
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  const isAuthenticated = user !== null && getStoredToken() !== null;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
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

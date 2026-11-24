import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Button } from "./components/ui/Button";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";

function ProtectedPlaceholder() {
  const { user, logout } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  return (
    <main className="min-h-screen bg-surface-canvas flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-surface-card border border-border-hairline rounded p-6 flex flex-col gap-4">
        <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
          Session Active • {user.role}
        </span>
        <h1 className="text-xl font-semibold text-text-primary">Welcome, {user.name}</h1>
        <p className="text-xs text-on-surface-variant">
          {user.station} ({user.district}) — {user.email}
        </p>
        <Button variant="secondary" onClick={logout}>
          Sign Out
        </Button>
      </div>
    </main>
  );
}

function PublicOnlyLogin() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />;
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicOnlyLogin />} />
          <Route path="/*" element={<ProtectedPlaceholder />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

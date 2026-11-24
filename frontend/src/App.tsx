import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { LocationDetailPage } from "./pages/LocationDetailPage";
import { FieldObservationPage } from "./pages/FieldObservationPage";
import { LoginPage } from "./pages/LoginPage";
import { MapPage } from "./pages/MapPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ReplayPage } from "./pages/ReplayPage";
import { SourcesPage } from "./pages/SourcesPage";
import { WarningsPage } from "./pages/WarningsPage";

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/locations/:id" element={<LocationDetailPage />} />
        <Route path="/field-log" element={<FieldObservationPage />} />
        <Route path="/warnings" element={<WarningsPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/replay" element={<ReplayPage />} />
        <Route
          path="/profile"
          element={
            <ComingSoonPage
              phase="Phase 9"
              title="Profile & Settings"
              description="Operator profile and control-room alert preferences."
            />
          }
        />
      </Route>
    </Routes>
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
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

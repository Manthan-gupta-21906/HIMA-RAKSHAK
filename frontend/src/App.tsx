import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { LocationDetailPage } from "./pages/LocationDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { MapPage } from "./pages/MapPage";
import { OverviewPage } from "./pages/OverviewPage";

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/locations/:id" element={<LocationDetailPage />} />
        <Route
          path="/field-log"
          element={
            <ComingSoonPage
              phase="Phase 5"
              title="Field Observation Form"
              description="FORM OPS-JK-449 field telemetry submission and validation."
            />
          }
        />
        <Route
          path="/warnings"
          element={
            <ComingSoonPage
              phase="Phase 6"
              title="Official Warnings"
              description="Authoritative IMD, CWC, and DGRE read-only bulletins."
            />
          }
        />
        <Route
          path="/sources"
          element={
            <ComingSoonPage
              phase="Phase 7"
              title="Data Source Status"
              description="Agency telemetry sync status, latency, and freshness monitoring."
            />
          }
        />
        <Route
          path="/replay"
          element={
            <ComingSoonPage
              phase="Phase 8"
              title="Historical Event Replay"
              description="Timeline playback and system loading/empty edge states."
            />
          }
        />
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

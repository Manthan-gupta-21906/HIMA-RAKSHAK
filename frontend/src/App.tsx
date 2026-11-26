import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";
import { FieldObservationPage } from "./pages/FieldObservationPage";
import { LocationDetailPage } from "./pages/LocationDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { MapPage } from "./pages/MapPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ReplayPage } from "./pages/ReplayPage";
import { SourcesPage } from "./pages/SourcesPage";
import { WarningsPage } from "./pages/WarningsPage";

function PublicOnlyLogin() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />;
}

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<PublicOnlyLogin />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<OverviewPage />} />
              <Route path="/map" element={<MapPage />} />
              <Route path="/locations/:id" element={<LocationDetailPage />} />
              <Route
                path="/field-log"
                element={
                  <ProtectedRoute allowedRoles={["admin", "district_operator"]}>
                    <FieldObservationPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/warnings" element={<WarningsPage />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="/replay" element={<ReplayPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

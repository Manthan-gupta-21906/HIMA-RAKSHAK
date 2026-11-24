/** Route guard that redirects unauthenticated users. */

import { type ReactNode } from "react";
import { getStoredToken } from "./authClient";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, fallback }: Props) {
  const token = getStoredToken();
  if (!token) {
    return <>{fallback ?? <p>Please log in to access this page.</p>}</>;
  }
  return <>{children}</>;
}

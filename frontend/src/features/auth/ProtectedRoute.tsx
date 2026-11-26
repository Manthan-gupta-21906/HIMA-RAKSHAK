/** Route guard that enforces authentication and optional role-based authorization. */

import { type ReactNode } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import type { UserRole } from "../../types/auth";

interface Props {
  children: ReactNode;
  allowedRoles?: UserRole[];
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, allowedRoles, fallback }: Props) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated || !user) {
    return <>{fallback ?? <Navigate to="/login" replace />}</>;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="max-w-lg mx-auto my-12 bg-surface-card border border-border-hairline rounded-xl p-6 text-center flex flex-col items-center gap-3 shadow-xs">
        <span className="material-symbols-outlined text-[36px] text-emergency-red">
          gpp_maybe
        </span>
        <h1 className="text-lg font-bold text-text-primary">Access Restricted</h1>
        <p className="text-xs sm:text-sm text-secondary">
          Your role (<span className="font-semibold">{user.role}</span>) does not have permission to
          access this page.
        </p>
        <Link
          to="/"
          className="mt-1 inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-xs font-semibold"
        >
          Return to Overview
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}

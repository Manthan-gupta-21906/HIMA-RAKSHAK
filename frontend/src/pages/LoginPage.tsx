import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types/auth";

interface FormErrors {
  email?: string;
  password?: string;
}

const ROLE_OPTIONS: { value: UserRole; label: string; hint: string }[] = [
  { value: "operator", label: "DDMA Operator", hint: "Full control-room triage & replay" },
  { value: "field_officer", label: "SDRF Field Officer", hint: "Field log & telemetry override" },
  { value: "viewer", label: "SDMA Viewer", hint: "Read-only advisory monitoring" },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateLogin(email: string, password: string): FormErrors {
  const errors: FormErrors = {};
  if (!email.trim()) {
    errors.email = "Official email address is required.";
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address (e.g. ops@jk-ddma.gov.in).";
  }
  if (!password) {
    errors.password = "Password is required.";
  } else if (password.length < 6) {
    errors.password = "Password must be at least 6 characters.";
  }
  return errors;
}

/** Operator authentication screen styled with Civil Defense Alpine Support tokens. */
export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("operator");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const nextErrors = validateLogin(email, password);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await login({ email, password, role });
      navigate("/", { replace: true });
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = () => {
    setEmail("ops.srinagar@jk-ddma.gov.in");
    setPassword("HimaRakshak#2026");
    setErrors({});
  };

  return (
    <div className="min-h-screen bg-surface-canvas flex flex-col justify-between px-4 py-8">
      <header className="max-w-md w-full mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary-container flex items-center justify-center text-on-primary shadow-sm">
            <span className="material-symbols-outlined text-[20px]">ac_unit</span>
          </div>
          <div>
            <p className="text-sm font-bold text-text-primary tracking-tight">HIMA-RAKSHAK</p>
            <p className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">
              Jammu &amp; Kashmir DDSS
            </p>
          </div>
        </div>
        <Badge tone="neutral">Prototype</Badge>
      </header>

      <main className="max-w-md w-full mx-auto my-8">
        <div className="bg-surface-card border border-border-hairline rounded p-6 sm:p-8 shadow-sm">
          <div className="mb-6 pb-4 border-b border-border-hairline">
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Authorized Control Access
            </span>
            <h1 className="text-2xl font-semibold text-text-primary tracking-tight mt-1">
              Sign in to Operations Console
            </h1>
            <p className="text-xs text-on-surface-variant mt-1">
              Access flood and avalanche risk intelligence for Jammu &amp; Kashmir sectors.
            </p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="login-email" className="text-xs font-semibold text-text-primary">
                Official Email
              </label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ops.srinagar@jk-ddma.gov.in"
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? "login-email-error" : undefined}
                className={`h-11 px-4 rounded-full bg-surface-container-lowest border text-sm text-text-primary focus:outline-none transition-all ${
                  errors.email
                    ? "border-error bg-error-container/30"
                    : "border-border-hairline focus:border-primary-container"
                }`}
              />
              {errors.email ? (
                <p id="login-email-error" role="alert" className="text-xs text-error font-medium px-2">
                  {errors.email}
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="login-password" className="text-xs font-semibold text-text-primary">
                Password
              </label>
              <div className="relative flex items-center">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (min 6 chars)"
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? "login-password-error" : undefined}
                  className={`w-full h-11 pl-4 pr-11 rounded-full bg-surface-container-lowest border text-sm text-text-primary focus:outline-none transition-all ${
                    errors.password
                      ? "border-error bg-error-container/30"
                      : "border-border-hairline focus:border-primary-container"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 p-1 text-text-muted hover:text-text-primary cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {showPassword ? "visibility_off" : "visibility"}
                  </span>
                </button>
              </div>
              {errors.password ? (
                <p id="login-password-error" role="alert" className="text-xs text-error font-medium px-2">
                  {errors.password}
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-text-primary">Operational Role</span>
              <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-surface-container-low border border-border-hairline">
                {ROLE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setRole(opt.value)}
                    title={opt.hint}
                    className={`py-2 px-2 rounded-lg text-[11px] font-semibold transition-all cursor-pointer ${
                      role === opt.value
                        ? "bg-primary-container text-on-primary shadow-xs"
                        : "text-on-surface-variant hover:text-text-primary"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2 pt-2">
              <Button type="submit" disabled={isSubmitting} className="w-full">
                <span className="material-symbols-outlined text-[16px]">login</span>
                <span>{isSubmitting ? "Signing in..." : "Sign In"}</span>
              </Button>
              <Button type="button" variant="secondary" onClick={fillDemoCredentials} className="w-full">
                Use Demo Credentials
              </Button>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-border-hairline flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px] text-text-muted">
              <span>Authoritative Feeds</span>
              <div className="flex items-center gap-1.5">
                <Badge tone="imd" showDot>IMD</Badge>
                <Badge tone="cwc" showDot>CWC</Badge>
                <Badge tone="dgre" showDot>DGRE</Badge>
              </div>
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Decision-support prototype only. Official agency bulletins remain authoritative.
            </p>
          </div>
        </div>
      </main>

      <footer className="max-w-md w-full mx-auto text-center text-[11px] text-text-muted">
        Civil Defense Alpine Support • Sector J&amp;K
      </footer>
    </div>
  );
}

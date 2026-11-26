import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "emergency" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-primary-container text-on-primary hover:bg-text-primary shadow-sm",
  secondary: "bg-secondary-container text-primary-container hover:bg-surface-container-high",
  emergency: "bg-emergency-red text-on-primary hover:opacity-90 font-semibold",
  ghost: "bg-transparent text-on-surface-variant hover:bg-surface-container",
};

/** Pill-shaped operational action button following Civil Defense Alpine Support tokens. */
export function Button({ variant = "primary", className = "", children, ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 h-10 px-6 rounded-full text-xs font-semibold tracking-wide transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

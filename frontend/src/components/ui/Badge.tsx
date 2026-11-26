import type { ReactNode } from "react";

export type BadgeTone = "imd" | "cwc" | "dgre" | "warning" | "emergency" | "clear" | "neutral";

const TONE_CLASSES: Record<BadgeTone, string> = {
  imd: "bg-[#d7e3ff] text-[#13295b]",
  cwc: "bg-[#cdf9f9] text-[#024444]",
  dgre: "bg-[#fdf1d6] text-[#8c380f]",
  warning: "bg-hazard-yellow text-primary-container",
  emergency: "bg-emergency-red text-on-primary",
  clear: "bg-alert-green text-[#054024]",
  neutral: "bg-surface-container text-on-surface-variant",
};

const DOT_CLASSES: Partial<Record<BadgeTone, string>> = {
  imd: "bg-agency-imd",
  cwc: "bg-agency-cwc",
  dgre: "bg-agency-dgre",
};

/** Pill badge for official agency attribution and hazard status indicators. */
export function Badge({
  tone = "neutral",
  showDot = false,
  children,
}: {
  tone?: BadgeTone;
  showDot?: boolean;
  children: ReactNode;
}) {
  const dotClass = DOT_CLASSES[tone];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-[0.08em] ${TONE_CLASSES[tone]}`}
    >
      {showDot && dotClass ? <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} /> : null}
      {children}
    </span>
  );
}

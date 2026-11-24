import { Link } from "react-router-dom";

interface ComingSoonPageProps {
  title: string;
  phase: string;
  description: string;
}

/** Temporary route view for screens scheduled in subsequent implementation phases. */
export function ComingSoonPage({ title, phase, description }: ComingSoonPageProps) {
  return (
    <div className="bg-surface-card border border-border-hairline rounded-xl p-6 sm:p-8 flex flex-col gap-3 max-w-2xl">
      <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
        {phase}
      </span>
      <h1 className="text-xl font-bold text-text-primary">{title}</h1>
      <p className="text-sm text-secondary">{description}</p>
      <div className="pt-2">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary text-xs font-semibold"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          <span>Back to Overview</span>
        </Link>
      </div>
    </div>
  );
}

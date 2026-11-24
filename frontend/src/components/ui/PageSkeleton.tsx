/** Reusable skeleton loading screen matching Civil Defense Alpine Support card layout. */
export function PageSkeleton() {
  return (
    <div
      role="status"
      aria-label="Loading screen"
      className="flex flex-col gap-6 animate-pulse"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div className="flex flex-col gap-2">
          <div className="h-3 w-36 rounded bg-surface-container-high" />
          <div className="h-7 w-64 rounded bg-surface-container-high" />
          <div className="h-3.5 w-80 max-w-full rounded bg-surface-container" />
        </div>
        <div className="h-9 w-44 rounded-full bg-surface-container" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((slot) => (
          <div
            key={slot}
            className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-2.5"
          >
            <div className="h-3 w-20 rounded bg-surface-container-high" />
            <div className="h-6 w-24 rounded bg-surface-container-high" />
            <div className="h-3 w-28 rounded bg-surface-container" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((slot) => (
          <div
            key={slot}
            className="p-5 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-3"
          >
            <div className="flex items-center justify-between">
              <div className="h-4 w-32 rounded bg-surface-container-high" />
              <div className="h-5 w-16 rounded-full bg-surface-container" />
            </div>
            <div className="h-5 w-28 rounded-full bg-surface-container" />
            <div className="h-3 w-full rounded bg-surface-container" />
            <div className="pt-3 border-t border-border-hairline flex items-center justify-between">
              <div className="h-3 w-24 rounded bg-surface-container" />
              <div className="h-8 w-24 rounded-md bg-surface-container-high" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

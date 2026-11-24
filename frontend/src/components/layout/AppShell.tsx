import { useState } from "react";
import { Outlet } from "react-router-dom";
import { SidebarDock } from "./SidebarDock";
import { TopHeader } from "./TopHeader";

/** Main authenticated application shell with fixed header, left sidebar, and content outlet. */
export function AppShell() {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-canvas text-text-primary">
      <TopHeader
        isMobileNavOpen={isMobileNavOpen}
        onToggleMobileNav={() => setIsMobileNavOpen((prev) => !prev)}
      />
      <SidebarDock
        isMobileOpen={isMobileNavOpen}
        onCloseMobile={() => setIsMobileNavOpen(false)}
      />
      <div className="md:pl-20 pt-16 min-h-screen">
        <main className="w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-10 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

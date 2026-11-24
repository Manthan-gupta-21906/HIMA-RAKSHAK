import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { OverviewPage } from "../../../pages/OverviewPage";
import { loadStoredPreferences, PREFS_STORAGE_KEY } from "../../../utils/preferences";
import { PageSkeleton } from "../PageSkeleton";

describe("PageSkeleton & Preferences", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders accessible PageSkeleton with animate-pulse", () => {
    render(<PageSkeleton />);
    const skeleton = screen.getByRole("status", { name: "Loading screen" });
    expect(skeleton).toBeInTheDocument();
    expect(skeleton.className).toContain("animate-pulse");
  });

  it("shows PageSkeleton when clicking Refresh on OverviewPage", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    expect(screen.getByRole("status", { name: "Loading screen" })).toBeInTheDocument();
  });

  it("reads saved defaultMapLayer preference from localStorage", () => {
    localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify({ defaultMapLayer: "terrain" }));
    expect(loadStoredPreferences().defaultMapLayer).toBe("terrain");
  });
});

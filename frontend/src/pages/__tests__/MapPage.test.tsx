import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";

vi.mock("../../components/map/HazardMap", () => ({
  HazardMap: ({
    sectors,
    selectedSectorId,
    onSelectSector,
  }: {
    sectors: { id: string; name: string }[];
    selectedSectorId: string | null;
    onSelectSector: (s: { id: string; name: string }) => void;
  }) => (
    <div data-testid="mock-leaflet-map" data-selected={selectedSectorId}>
      {sectors.map((s) => (
        <button key={s.id} type="button" onClick={() => onSelectSector(s)}>
          Pin {s.name}
        </button>
      ))}
    </div>
  ),
}));

const SEEDED_USER = {
  id: "usr-ddma-01",
  name: "M. Gupta",
  email: "ops.srinagar@jk-ddma.gov.in",
  initials: "MG",
  role: "operator",
  station: "DDMA Control Room",
  district: "Srinagar",
};

describe("MapPage", () => {
  beforeEach(() => {
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/map");
  });

  it("renders all 5 sectors and filters by flood/avalanche/stale", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByText("Multi-Hazard Risk Map")).toBeInTheDocument();
    expect(screen.getByText("Showing 4 of 4 sectors")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^flood pathway$/i }));
    expect(screen.getByText("Showing 2 of 4 sectors")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^avalanche pathway$/i }));
    expect(screen.getByText("Showing 2 of 4 sectors")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /stale only/i }));
    expect(screen.getByText("Showing 1 of 4 sectors")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drass — Zojila High Pass" })).toBeInTheDocument();
  });

  it("updates inspector panel when selecting a sector pin", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Pin Gulmarg — Affarwat Ridge" }));
    expect(screen.getByRole("heading", { name: "Gulmarg — Affarwat Ridge" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /inspect sector/i })).toHaveAttribute(
      "href",
      "/locations/JK-GUL-01"
    );
  });
});

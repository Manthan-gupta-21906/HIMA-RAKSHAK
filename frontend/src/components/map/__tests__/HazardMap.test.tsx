import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { HazardMap } from "../HazardMap";
import { MOCK_SECTORS, type MonitoringSector } from "../../../data/mockSectors";

const TEST_SECTORS = MOCK_SECTORS.slice(0, 2);

function MapHarness({ onSelectSector }: { onSelectSector?: (sector: MonitoringSector) => void }) {
  const [selectedSectorId, setSelectedSectorId] = useState<string | null>(null);

  return (
    <MemoryRouter>
      <HazardMap
        sectors={TEST_SECTORS}
        selectedSectorId={selectedSectorId}
        onSelectSector={(sector) => {
          setSelectedSectorId(sector.id);
          onSelectSector?.(sector);
        }}
      />
    </MemoryRouter>
  );
}

describe("HazardMap", () => {
  it("toggles between standard and terrain base layers", async () => {
    const user = userEvent.setup();
    render(<MapHarness />);

    const terrain = screen.getByRole("button", { name: /terrain/i });
    const standard = screen.getByRole("button", { name: /standard/i });

    expect(standard).toHaveAttribute("aria-pressed", "true");
    await user.click(terrain);
    expect(terrain).toHaveAttribute("aria-pressed", "true");
    expect(standard).toHaveAttribute("aria-pressed", "false");
  });

  it("keeps the marker popup open after selection and exposes a details link", () => {
    const { container } = render(<MapHarness />);
    const pins = container.querySelectorAll(".hima-sector-pin");
    expect(pins).toHaveLength(2);

    fireEvent.click(pins[1]);

    expect(screen.getByText("Gulmarg - Affarwat")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view details/i })).toHaveAttribute(
      "href",
      "/locations/JK-BM-12"
    );
  });
});

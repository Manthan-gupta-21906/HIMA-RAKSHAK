import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WarningPanel } from "../WarningPanel";
import type { OfficialWarning } from "../../../types/warning";

const mockActiveWarning: OfficialWarning = {
  id: "WARN-TEST-01",
  bulletinCode: "CWC-TEST-01",
  agency: "CWC",
  agencyFullName: "Central Water Commission",
  title: "Flash Flood Warning — Sangam Gauge",
  hazard: "flood",
  severity: "Red",
  affectedSectors: ["JK-SGR-01", "Sangam"],
  district: "Anantnag",
  issuedAt: "2026-11-26 10:00 IST",
  validUntil: "2099-12-31 23:59 IST",
  summary: "Water level rising rapidly past danger mark.",
  advisoryNotes: "Evacuate low-lying riverbank areas immediately.",
  sourceReference: "CWC Official Northern Rivers Bulletin #104",
  isReadOnly: true,
};

const mockExpiredWarning: OfficialWarning = {
  id: "WARN-EXPIRED-01",
  bulletinCode: "DGRE-TEST-EXPIRED",
  agency: "DGRE",
  agencyFullName: "Defence Geoinformatics Research Establishment",
  title: "Expired Avalanche Advisory",
  hazard: "avalanche",
  severity: "Orange",
  affectedSectors: ["JK-KLU-02"],
  district: "Kullu",
  issuedAt: "2020-01-01 10:00 IST",
  validUntil: "2020-01-02 10:00 IST",
  summary: "Historical avalanche warning that has concluded.",
  advisoryNotes: "No further action needed.",
  sourceReference: "DGRE Historical Bulletin (Sample Cached Record)",
  isReadOnly: true,
};

describe("WarningPanel component", () => {
  it("renders active warning with authority, severity, and source reference", () => {
    render(<WarningPanel warning={mockActiveWarning} />);

    expect(screen.getByText("Flash Flood Warning — Sangam Gauge")).toBeInTheDocument();
    expect(screen.getByText("Central Water Commission • CWC-TEST-01")).toBeInTheDocument();
    expect(screen.getByText("CWC")).toBeInTheDocument();
    expect(screen.getByText("Red Alert")).toBeInTheDocument();
    expect(screen.getByTestId("warning-active-tag")).toHaveTextContent("Active");
    expect(screen.getByTestId("warning-source-ref")).toHaveTextContent("CWC Official Northern Rivers Bulletin #104");
  });

  it("identifies expired warnings clearly", () => {
    render(<WarningPanel warning={mockExpiredWarning} />);

    expect(screen.getByText("Expired Avalanche Advisory")).toBeInTheDocument();
    expect(screen.getByTestId("warning-expired-tag")).toHaveTextContent("Expired");
    expect(screen.getByText(/\* Sample warning fixture/i)).toBeInTheDocument();
  });

  it("displays isolation disclaimer confirming warning is not merged into model score", () => {
    render(<WarningPanel warning={mockActiveWarning} />);

    expect(screen.getByText(/not blended into automated scores/i)).toBeInTheDocument();
    expect(screen.getByText(/Read-Only Record/i)).toBeInTheDocument();
  });

  it("renders empty placeholder when warning is null", () => {
    render(<WarningPanel warning={null} />);

    expect(screen.getByTestId("warning-panel-empty")).toBeInTheDocument();
    expect(screen.getByText(/Select an official warning bulletin/i)).toBeInTheDocument();
  });
});

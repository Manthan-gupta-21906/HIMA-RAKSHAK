export type WarningAgency = "IMD" | "CWC" | "DGRE";
export type WarningSeverity = "Red" | "Orange" | "Yellow";
export type WarningHazard = "flood" | "avalanche" | "weather";

export interface OfficialWarning {
  id: string;
  bulletinCode: string;
  agency: WarningAgency;
  agencyFullName: string;
  title: string;
  hazard: WarningHazard;
  severity: WarningSeverity;
  affectedSectors: string[];
  district: string;
  issuedAt: string;
  validUntil: string;
  summary: string;
  advisoryNotes: string;
  sourceReference: string;
  isReadOnly: true;
}

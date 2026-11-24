export type SourceStatus = "online" | "delayed" | "offline";
export type SourceAgency = "IMD" | "CWC" | "DGRE" | "SDRF";

export interface DataSourceRecord {
  id: string;
  name: string;
  agency: SourceAgency;
  category: string;
  coverage: string;
  status: SourceStatus;
  latencyLabel: string;
  lastUpdated: string;
  cadence: string;
  provenanceNote: string;
  knownLimitation?: string;
}

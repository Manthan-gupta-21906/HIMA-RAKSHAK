import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../ui/Button";
import { getSectorById, SECTOR_OPTIONS } from "../../data/observationDefaults";
import { HAZARD_CONFIG, type HazardKind, VALIDATION_ERROR_CODES } from "../../types/observation";

const DEFAULT_SECTOR_ID = "JK-PN-04";
const DEFAULT_HAZARD_KIND: HazardKind = "avalanche";

type FormMode = "editing" | "submitting" | "success";

interface ObservationFormProps {
  initialSectorId?: string;
  initialHazardKind?: HazardKind;
  onSubmit?: (result: {
    sectorId: string;
    sectorName: string;
    hazardKind: HazardKind;
    value: number;
    unit: string;
    notes: string;
  }) => void;
}

/** FORM OPS-JK-449 field observation submission with dynamic metric validation. */
export function ObservationForm({
  initialSectorId,
  initialHazardKind,
  onSubmit,
}: ObservationFormProps) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [mode, setMode] = useState<FormMode>("editing");
  const [sectorId, setSectorId] = useState(
    initialSectorId ?? searchParams.get("sector") ?? DEFAULT_SECTOR_ID
  );
  const [hazardKind, setHazardKind] = useState<HazardKind>(
    (searchParams.get("hazard") as HazardKind) ?? initialHazardKind ?? DEFAULT_HAZARD_KIND
  );
  const [observationValue, setObservationValue] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<{ code: string; message: string; detail?: string } | null>(
    null
  );

  const sector = useMemo(() => getSectorById(sectorId), [sectorId]);
  const config = HAZARD_CONFIG[hazardKind];
  const inputRef = useRef<HTMLInputElement>(null);

  const clearError = useCallback(() => setError(null), []);

  const handleSectorChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSectorId(event.target.value);
    clearError();
  };

  const handleHazardChange = (next: HazardKind) => {
    setHazardKind(next);
    setObservationValue("");
    clearError();
  };

  const handleValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const next = event.target.value;
    setObservationValue(next);

    const trimmed = next.trim();
    if (!trimmed) {
      setError(null);
      return;
    }

    const num = Number(trimmed);
    if (!Number.isFinite(num) || num < config.min || num > config.max) {
      setError({
        code: Number.isFinite(num) ? VALIDATION_ERROR_CODES.OUT_OF_RANGE : VALIDATION_ERROR_CODES.NON_NUMERIC,
        message:
          Number.isFinite(num)
            ? "Enter a valid positive measurement"
            : "Enter a numeric value",
        detail:
          Number.isFinite(num)
            ? `Physical ${config.label.toLowerCase()} cannot be negative (${num} ${config.unit} recorded). Input positive numeric value in ${config.unit}.`
            : `Input must be a valid number in ${config.unit}.`,
      });
      return;
    }

    if (error) {
      setError(null);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = observationValue.trim();
    if (!trimmed) {
      setError({
        code: VALIDATION_ERROR_CODES.REQUIRED,
        message: "Enter a valid positive measurement",
        detail: `Physical ${config.label.toLowerCase()} cannot be empty. Input a positive numeric value in ${config.unit}.`,
      });
      inputRef.current?.focus();
      return;
    }

    const num = Number(trimmed);
    if (!Number.isFinite(num)) {
      setError({
        code: VALIDATION_ERROR_CODES.NON_NUMERIC,
        message: "Enter a numeric value",
        detail: `Input must be a valid number in ${config.unit}.`,
      });
      inputRef.current?.focus();
      return;
    }

    if (num < config.min || num > config.max) {
      setError({
        code: VALIDATION_ERROR_CODES.OUT_OF_RANGE,
        message: "Value outside valid range",
        detail: `Value ${num} ${config.unit} is outside the standard baseline range of ${config.min} – ${config.max} ${config.unit}.`,
      });
      inputRef.current?.focus();
      return;
    }

    setMode("submitting");
    const result = {
      sectorId: sector?.id ?? sectorId,
      sectorName: sector?.name ?? "Unknown Sector",
      hazardKind,
      value: num,
      unit: config.unit,
      notes,
    };

    if (onSubmit) {
      onSubmit(result);
    }

    // Simulate backend persistence delay for the demo.
    setTimeout(() => {
      setMode("success");
    }, 200);
  };

  const handleCancel = () => {
    navigate(-1);
  };

  const handleReset = () => {
    setObservationValue("");
    setNotes("");
    setError(null);
    setMode("editing");
    inputRef.current?.focus();
  };

  const isDisabled = mode !== "editing";
  const showError = !!error && mode === "editing";

  if (mode === "success") {
    return (
      <div className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-6 sm:p-10 text-center max-w-md mx-auto">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-alert-green/10 text-alert-green mb-4 mx-auto">
          <span className="material-symbols-outlined text-[44px]">check_circle</span>
        </div>
        <h2 className="text-xl font-bold text-text-primary mb-1">Observation Recorded</h2>
        <p className="text-sm text-text-muted mb-6">
          Field observation for <span className="font-semibold text-text-primary">{sector?.name}</span>
          has been validated and the hazard model recalculated.
        </p>

        <div className="bg-surface-container-low rounded-lg p-4 text-left mb-6">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Sector
            </span>
            <span className="text-base font-semibold text-text-primary">
              {sector?.name} ({sector?.id})
            </span>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Hazard
            </span>
            <span className="text-base font-semibold text-text-primary">{hazardKind}</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Measurement
            </span>
            <span className="text-base font-semibold text-text-primary">
              {observationValue} {config.unit}
            </span>
          </div>
        </div>

        <div className="w-full p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-900 dark:text-amber-200 text-left mb-2">
          <span className="font-semibold">Backend Notice:</span> The backend currently lacks <code className="font-mono text-[10px] px-1 py-0.5 rounded bg-amber-500/20">POST /observations</code>. This observation has been captured locally and not persisted to remote database.
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" onClick={handleReset} className="flex-1 sm:w-auto">
            Log Another Observation
          </Button>
          <Button variant="ghost" onClick={handleCancel} className="flex-1 sm:w-auto">
            Return to Map
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
      {/* Backend Integration Notice */}
      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-900 dark:text-amber-200">
        <span className="material-symbols-outlined text-[18px] text-amber-600 dark:text-amber-400 shrink-0 mt-0.5">
          info
        </span>
        <div className="flex flex-col gap-0.5">
          <span className="font-bold">Missing Backend Endpoint: POST /observations</span>
          <p className="text-[11px] leading-relaxed text-amber-800 dark:text-amber-300">
            The backend API currently implements only <code className="font-mono text-[10px] px-1 py-0.5 rounded bg-amber-500/20">GET /observations</code> (read-only). A dedicated <code className="font-mono text-[10px] px-1 py-0.5 rounded bg-amber-500/20">POST /observations</code> submission route is not yet available on the server. Observations submitted here are captured in local session memory.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="sector-location"
            className="text-xs font-semibold text-text-primary flex items-center gap-1"
          >
            Target Sector &amp; Station Coordinates <span className="text-emergency-red">*</span>
          </label>
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
            Critical Geo-Code
          </span>
        </div>
        <div className="relative">
          <select
            id="sector-location"
            value={sectorId}
            onChange={handleSectorChange}
            disabled={isDisabled}
            className="w-full h-10 px-3.5 pr-10 rounded-lg bg-surface-container-low border border-border-hairline text-text-primary text-xs sm:text-sm focus:border-primary focus:outline-none focus:ring-1 focus-ring focus:ring-primary/20 cursor-pointer appearance-none transition-all"
          >
            {SECTOR_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-text-muted">
            <span className="material-symbols-outlined text-[18px]">expand_more</span>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-0.5 px-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-agency-dgre" />
          <span className="text-[11px] text-text-muted">
            Current DGRE Threat Advisory in Sector:{" "}
            <span className="font-semibold text-text-primary uppercase tracking-tight">
              {sector?.threatLabel}
            </span>
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
          Observed Hazard Dynamic <span className="text-emergency-red">*</span>
        </label>
        <div className="grid grid-cols-2 gap-2 p-1 rounded-lg border border-border-hairline bg-surface-container-low">
          <label
            className={`relative flex items-center justify-center gap-2 py-2 px-3 rounded-md cursor-pointer transition-all ${
              hazardKind === "avalanche"
                ? "bg-primary-container text-on-primary shadow-sm"
                : "text-on-surface-variant hover:bg-surface-container hover:text-text-primary"
            }`}
          >
            <input
              className="sr-only"
              name="hazard_type"
              onChange={() => handleHazardChange("avalanche")}
              type="radio"
              value="avalanche"
              checked={hazardKind === "avalanche"}
            />
            <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
              ac_unit
            </span>
            <span className="text-xs font-semibold tracking-wide">Snowpack &amp; Avalanche</span>
          </label>
          <label
            className={`relative flex items-center justify-center gap-2 py-2 px-3 rounded-md cursor-pointer transition-all ${
              hazardKind === "flood"
                ? "bg-primary-container text-on-primary shadow-sm"
                : "text-on-surface-variant hover:bg-surface-container hover:text-text-primary"
            }`}
          >
            <input
              className="sr-only"
              name="hazard_type"
              onChange={() => handleHazardChange("flood")}
              type="radio"
              value="flood"
              checked={hazardKind === "flood"}
            />
            <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
              waves
            </span>
            <span className="text-xs font-semibold tracking-wide">Riverine Basin / Flood</span>
          </label>
        </div>
      </div>

      <div className="flex flex-col gap-1.5" id="field-observation-wrapper">
        <div className="flex items-center justify-between">
          <label
            htmlFor="observation-value"
            className={`text-xs font-semibold flex items-center gap-1.5 ${
              showError ? "text-emergency-red" : "text-text-primary"
            }`}
          >
            <span className={`material-symbols-outlined text-[16px] ${
              showError ? "text-emergency-red" : "text-text-muted"
            }`}>warning</span>
            {config.label}
            <span className="text-emergency-red font-bold">*</span>
          </label>
          {showError && (
            <span className={`text-[10px] font-bold text-emergency-red uppercase tracking-wider`}>
              Validation Error ({error.code})
            </span>
          )}
        </div>
        <div className="relative flex items-center">
          <input
            ref={inputRef}
            id="observation-value"
            aria-describedby={showError ? "observation-error observation-hint" : "observation-hint"}
            aria-invalid={showError}
            value={observationValue}
            onChange={handleValueChange}
            disabled={isDisabled}
            className={`w-full h-10 pl-3.5 pr-24 rounded-lg bg-surface-container-lowest border text-base font-semibold focus:outline-none focus:ring-1 transition-all ${
              showError
                ? "border-emergency-red bg-[#fff5f5] text-[#991b1b] focus:ring-emergency-red shadow-sm"
                : "border-border-hairline text-text-primary focus:border-primary focus:ring-primary/20"
            }`}
            placeholder={config.placeholder}
            type="text"
          />
          <div className="absolute right-9 flex items-center pr-1 text-text-muted">
            <span className="text-[11px] uppercase font-bold tracking-wider">{config.unit}</span>
          </div>
          {showError && (
            <div className="absolute right-3 flex items-center pointer-events-none text-emergency-red">
              <span className="material-symbols-outlined text-[18px]">error</span>
            </div>
          )}
        </div>

        {showError && (
          <div className="flex items-start gap-2.5 p-3 rounded-lg bg-[#fff5f5] border border-[#fee2e2] text-[#991b1b] mt-0.5" id="observation-error" role="alert">
            <span className="material-symbols-outlined text-[18px] text-emergency-red shrink-0 mt-0.5">
              info
            </span>
            <div className="flex flex-col text-xs">
              <span className="font-bold text-emergency-red">{error.message}</span>
              <span className="text-[#7f1d1d] mt-0.5 leading-relaxed">
                {error.detail ?? `Input positive numeric value in ${config.unit}.`}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between px-0.5">
          <span className="text-[11px] text-text-muted" id="observation-hint">
            Standard baseline range:{" "}
            <span className="font-medium text-text-primary">
              {config.min}.0 {config.unit} – {config.max}.0 {config.unit}
            </span>
            . Use calibrated stake measurement.
          </span>
          <span className="text-[10px] text-agency-dgre font-bold uppercase tracking-wider">
            DGRE Methodology
          </span>
        </div>
      </div>

      <div className="p-3.5 rounded-lg bg-surface-container-low border border-border-hairline flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center text-text-primary font-bold text-[11px]">
            S04
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-text-primary">
              Observer: SDRF Ground Unit 04 (Sub-Inspector R. Ahmed)
            </span>
            <span className="text-[11px] text-text-muted">
              Station Device: Ruggedized Field Terminal #JKS-094
            </span>
          </div>
        </div>
        <div className="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto">
          <span className="px-2 py-0.5 rounded bg-surface-card border border-border-hairline text-[11px] font-semibold text-text-primary">
            {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} IST • Today
          </span>
          <span className="text-[9px] text-alert-green font-bold uppercase tracking-wider mt-0.5 sm:mt-0">
            GPS Lock: Verified
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="verification-notes"
            className="text-xs font-semibold text-text-primary"
          >
            Field Observations &amp; Ground Context
          </label>
          <span className="text-[11px] text-text-muted">Optional detailed log</span>
        </div>
        <textarea
          id="verification-notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          disabled={isDisabled}
          className="w-full p-3 rounded-lg bg-surface-container-low border border-border-hairline text-text-primary text-xs sm:text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 placeholder:text-text-muted transition-all resize-none leading-relaxed"
          placeholder="Detail drift characteristics, weak layer shears, soundings, visibility conditions, or river crest visual markers..."
          rows={3}
        />
      </div>

      <div className="flex items-start gap-3 p-3.5 rounded-lg bg-surface-container-low border border-border-hairline">
        <span className="material-symbols-outlined text-[18px] text-critical-blue shrink-0 mt-0.5">
          verified_user
        </span>
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-text-primary">
            Immediate Hazard Recalculation Notice
          </span>
          <p className="text-[11px] text-text-muted mt-0.5 leading-relaxed">
            Validated field observations immediately supersede asynchronous DGRE/IMD automated radar
            telemetry. Emergency evacuation thresholds will be recalculated dynamically.
          </p>
        </div>
      </div>

      <div className="flex flex-col-reverse sm:flex-row items-center justify-between gap-3 pt-2">
        <button
          type="button"
          onClick={handleCancel}
          disabled={isDisabled}
          className={`w-full sm:w-auto px-5 h-9 rounded-lg text-xs font-semibold text-text-muted bg-surface-container-low border border-border-hairline hover:bg-surface-container transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          Cancel &amp; Discard Entry
        </button>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            type="submit"
            variant="primary"
            className="w-full sm:w-auto px-6 h-9"
          >
            <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
              publish
            </span>
            {mode === "submitting" ? "Saving..." : "Save &amp; Update Risk State"}
          </Button>
        </div>
      </div>
    </form>
  );
}

import { useState, type FormEvent, type ReactNode } from "react";
import {
  createLocation,
  updateLocationCoverage,
  type LocationCreatePayload,
} from "../api/locations";
import {
  refreshSource,
  registerSource,
  type SourceCreatePayload,
} from "../api/sources";
import { Badge } from "../components/ui/Badge";

type Feedback = { tone: "success" | "error"; message: string } | null;

const INPUT_CLASS =
  "h-9 w-full rounded-lg bg-surface-container-lowest border border-border-hairline px-3 text-xs text-text-primary focus:outline-none focus:border-primary-container";
const LABEL_CLASS =
  "text-[10px] font-bold uppercase tracking-wider text-text-muted";
const CARD_CLASS =
  "bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5 flex flex-col gap-3";

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

function FeedbackNote({ feedback }: { feedback: Feedback }) {
  if (!feedback) return null;
  return (
    <p
      role={feedback.tone === "error" ? "alert" : "status"}
      className={`text-[11px] font-medium ${
        feedback.tone === "error" ? "text-emergency-red" : "text-alert-green"
      }`}
    >
      {feedback.message}
    </p>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className={LABEL_CLASS}>
        {label}
      </label>
      {children}
    </div>
  );
}

/** Admin-only catalogue and source registry management. */
export function AdminPage() {
  const [locationFeedback, setLocationFeedback] = useState<Feedback>(null);
  const [isCreatingLocation, setIsCreatingLocation] = useState(false);
  const [locationId, setLocationId] = useState("");
  const [name, setName] = useState("");
  const [adminUnit, setAdminUnit] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [hazards, setHazards] = useState<string[]>(["flood"]);
  const [coverageStatus, setCoverageStatus] = useState<
    "supported" | "partial" | "unsupported"
  >("partial");
  const [coverageNote, setCoverageNote] = useState("");

  const [coverageFeedback, setCoverageFeedback] = useState<Feedback>(null);
  const [isUpdatingCoverage, setIsUpdatingCoverage] = useState(false);
  const [coverageLocationId, setCoverageLocationId] = useState("");
  const [newCoverageStatus, setNewCoverageStatus] = useState<
    "supported" | "partial" | "unsupported"
  >("supported");
  const [newCoverageNote, setNewCoverageNote] = useState("");

  const [sourceFeedback, setSourceFeedback] = useState<Feedback>(null);
  const [isRegisteringSource, setIsRegisteringSource] = useState(false);
  const [sourceId, setSourceId] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [provider, setProvider] = useState("");
  const [dataset, setDataset] = useState("");
  const [sourceType, setSourceType] = useState("weather");
  const [accessMode, setAccessMode] = useState("sample");
  const [licence, setLicence] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [updateFrequency, setUpdateFrequency] = useState("60");
  const [trustClassification, setTrustClassification] = useState("demo");
  const [isAuthoritative, setIsAuthoritative] = useState(false);
  const [isDemoFixture, setIsDemoFixture] = useState(true);

  const [fetchFeedback, setFetchFeedback] = useState<Feedback>(null);
  const [isFetchingSource, setIsFetchingSource] = useState(false);
  const [fetchSourceId, setFetchSourceId] = useState("");

  const toggleHazard = (hazard: string) => {
    setHazards((prev) =>
      prev.includes(hazard)
        ? prev.filter((item) => item !== hazard)
        : [...prev, hazard]
    );
  };

  const handleCreateLocation = async (event: FormEvent) => {
    event.preventDefault();
    setIsCreatingLocation(true);
    setLocationFeedback(null);
    const payload: LocationCreatePayload = {
      location_id: locationId.trim(),
      name: name.trim(),
      admin_unit: adminUnit.trim(),
      latitude: Number(latitude),
      longitude: Number(longitude),
      supported_hazards: hazards,
      coverage_status: coverageStatus,
      coverage_note: coverageNote.trim(),
    };
    try {
      const created = await createLocation(payload);
      setLocationFeedback({
        tone: "success",
        message: `Registered ${created.location_id} — ${created.name}.`,
      });
      setLocationId("");
      setName("");
      setAdminUnit("");
      setLatitude("");
      setLongitude("");
      setCoverageNote("");
    } catch (err) {
      setLocationFeedback({
        tone: "error",
        message: errorMessage(err, "Could not register the location."),
      });
    } finally {
      setIsCreatingLocation(false);
    }
  };

  const handleUpdateCoverage = async (event: FormEvent) => {
    event.preventDefault();
    setIsUpdatingCoverage(true);
    setCoverageFeedback(null);
    try {
      const updated = await updateLocationCoverage(coverageLocationId.trim(), {
        coverage_status: newCoverageStatus,
        coverage_note: newCoverageNote.trim(),
      });
      setCoverageFeedback({
        tone: "success",
        message: `Coverage updated for ${updated.location_id}: ${updated.coverage_status}.`,
      });
      setCoverageLocationId("");
      setNewCoverageNote("");
    } catch (err) {
      setCoverageFeedback({
        tone: "error",
        message: errorMessage(err, "Could not update coverage."),
      });
    } finally {
      setIsUpdatingCoverage(false);
    }
  };

  const handleRegisterSource = async (event: FormEvent) => {
    event.preventDefault();
    setIsRegisteringSource(true);
    setSourceFeedback(null);
    const payload: SourceCreatePayload = {
      source_id: sourceId.trim(),
      source_name: sourceName.trim() || undefined,
      provider: provider.trim() || undefined,
      dataset: dataset.trim() || undefined,
      source_type: sourceType,
      access_mode: accessMode,
      licence: licence.trim(),
      reference_url: referenceUrl.trim() || undefined,
      update_frequency_minutes: Number(updateFrequency),
      trust_classification: trustClassification,
      is_authoritative: isAuthoritative,
      is_demo_fixture: isDemoFixture,
    };
    try {
      const created = await registerSource(payload);
      setSourceFeedback({
        tone: "success",
        message: `Registered ${created.source_id} — ${created.source_name}.`,
      });
      setSourceId("");
      setSourceName("");
      setProvider("");
      setDataset("");
      setLicence("");
      setReferenceUrl("");
    } catch (err) {
      setSourceFeedback({
        tone: "error",
        message: errorMessage(err, "Could not register the data source."),
      });
    } finally {
      setIsRegisteringSource(false);
    }
  };

  const handleFetchSource = async (event: FormEvent) => {
    event.preventDefault();
    setIsFetchingSource(true);
    setFetchFeedback(null);
    try {
      const source = await refreshSource(fetchSourceId.trim());
      setFetchFeedback({
        tone: "success",
        message: `Fetch recorded for ${source.source_id}. Freshness: ${source.freshness}.`,
      });
      setFetchSourceId("");
    } catch (err) {
      setFetchFeedback({
        tone: "error",
        message: errorMessage(err, "Could not record a fetch for this source."),
      });
    } finally {
      setIsFetchingSource(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Catalogue &amp; Registry Administration
            </span>
            <Badge tone="warning">Admin Only</Badge>
          </div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Administration
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Register pilot locations, update coverage, and manage the telemetry source
            registry. These writes are enforced as admin-only by the backend.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
        <section aria-labelledby="admin-location-title" className={CARD_CLASS}>
          <h2 id="admin-location-title" className="text-base font-bold text-text-primary">
            Register Pilot Location
          </h2>
          <form className="flex flex-col gap-3" onSubmit={(event) => void handleCreateLocation(event)}>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Location ID" htmlFor="admin-location-id">
                <input
                  id="admin-location-id"
                  value={locationId}
                  onChange={(event) => setLocationId(event.target.value)}
                  required
                  minLength={3}
                  maxLength={32}
                  placeholder="JK-PAH-01"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Name" htmlFor="admin-location-name">
                <input
                  id="admin-location-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                  placeholder="Pahalgam — Lidder Valley"
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <Field label="Admin Unit" htmlFor="admin-location-unit">
              <input
                id="admin-location-unit"
                value={adminUnit}
                onChange={(event) => setAdminUnit(event.target.value)}
                required
                placeholder="Anantnag District, J&K"
                className={INPUT_CLASS}
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Latitude" htmlFor="admin-location-lat">
                <input
                  id="admin-location-lat"
                  type="number"
                  step="0.0001"
                  value={latitude}
                  onChange={(event) => setLatitude(event.target.value)}
                  required
                  placeholder="34.0161"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Longitude" htmlFor="admin-location-lng">
                <input
                  id="admin-location-lng"
                  type="number"
                  step="0.0001"
                  value={longitude}
                  onChange={(event) => setLongitude(event.target.value)}
                  required
                  placeholder="75.3150"
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <fieldset className="flex flex-col gap-1">
              <legend className={LABEL_CLASS}>Supported Hazards</legend>
              <div className="flex flex-wrap gap-3 pt-1 text-xs text-on-surface-variant">
                {["flood", "avalanche"].map((hazard) => (
                  <label key={hazard} className="inline-flex items-center gap-1.5 capitalize">
                    <input
                      type="checkbox"
                      checked={hazards.includes(hazard)}
                      onChange={() => toggleHazard(hazard)}
                    />
                    {hazard}
                  </label>
                ))}
              </div>
            </fieldset>

            <Field label="Coverage Status" htmlFor="admin-location-coverage">
              <select
                id="admin-location-coverage"
                value={coverageStatus}
                onChange={(event) =>
                  setCoverageStatus(
                    event.target.value as "supported" | "partial" | "unsupported"
                  )
                }
                className={INPUT_CLASS}
              >
                <option value="supported">Supported</option>
                <option value="partial">Partial</option>
                <option value="unsupported">Unsupported</option>
              </select>
            </Field>

            <Field label="Coverage Note" htmlFor="admin-location-note">
              <textarea
                id="admin-location-note"
                value={coverageNote}
                onChange={(event) => setCoverageNote(event.target.value)}
                required
                minLength={3}
                maxLength={300}
                rows={2}
                placeholder="Indicative pilot entry pending local validation."
                className="w-full rounded-lg bg-surface-container-lowest border border-border-hairline p-2.5 text-xs text-text-primary focus:outline-none focus:border-primary-container"
              />
            </Field>

            <FeedbackNote feedback={locationFeedback} />
            <button
              type="submit"
              disabled={isCreatingLocation}
              className="self-start inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-xs font-semibold disabled:opacity-60 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">add_location_alt</span>
              {isCreatingLocation ? "Registering…" : "Register Location"}
            </button>
          </form>
        </section>

        <section aria-labelledby="admin-coverage-title" className={CARD_CLASS}>
          <h2 id="admin-coverage-title" className="text-base font-bold text-text-primary">
            Update Location Coverage
          </h2>
          <form className="flex flex-col gap-3" onSubmit={(event) => void handleUpdateCoverage(event)}>
            <Field label="Location ID" htmlFor="admin-coverage-id">
              <input
                id="admin-coverage-id"
                value={coverageLocationId}
                onChange={(event) => setCoverageLocationId(event.target.value)}
                required
                placeholder="JK-PAH-01"
                className={INPUT_CLASS}
              />
            </Field>

            <Field label="New Coverage Status" htmlFor="admin-coverage-status">
              <select
                id="admin-coverage-status"
                value={newCoverageStatus}
                onChange={(event) =>
                  setNewCoverageStatus(
                    event.target.value as "supported" | "partial" | "unsupported"
                  )
                }
                className={INPUT_CLASS}
              >
                <option value="supported">Supported</option>
                <option value="partial">Partial</option>
                <option value="unsupported">Unsupported</option>
              </select>
            </Field>

            <Field label="Coverage Note" htmlFor="admin-coverage-note">
              <textarea
                id="admin-coverage-note"
                value={newCoverageNote}
                onChange={(event) => setNewCoverageNote(event.target.value)}
                required
                minLength={3}
                maxLength={300}
                rows={3}
                placeholder="Upgraded with field telemetry station."
                className="w-full rounded-lg bg-surface-container-lowest border border-border-hairline p-2.5 text-xs text-text-primary focus:outline-none focus:border-primary-container"
              />
            </Field>

            <FeedbackNote feedback={coverageFeedback} />
            <button
              type="submit"
              disabled={isUpdatingCoverage}
              className="self-start inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold disabled:opacity-60 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">verified</span>
              {isUpdatingCoverage ? "Updating…" : "Update Coverage"}
            </button>
          </form>
        </section>

        <section aria-labelledby="admin-source-title" className={CARD_CLASS}>
          <h2 id="admin-source-title" className="text-base font-bold text-text-primary">
            Register Data Source
          </h2>
          <form className="flex flex-col gap-3" onSubmit={(event) => void handleRegisterSource(event)}>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Source ID" htmlFor="admin-source-id">
                <input
                  id="admin-source-id"
                  value={sourceId}
                  onChange={(event) => setSourceId(event.target.value)}
                  required
                  minLength={2}
                  maxLength={64}
                  placeholder="src-imd-aws"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Provider" htmlFor="admin-source-provider">
                <input
                  id="admin-source-provider"
                  value={provider}
                  onChange={(event) => setProvider(event.target.value)}
                  required
                  placeholder="IMD"
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Source Name (optional)" htmlFor="admin-source-name">
                <input
                  id="admin-source-name"
                  value={sourceName}
                  onChange={(event) => setSourceName(event.target.value)}
                  placeholder="IMD AWS Network"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Dataset (optional)" htmlFor="admin-source-dataset">
                <input
                  id="admin-source-dataset"
                  value={dataset}
                  onChange={(event) => setDataset(event.target.value)}
                  placeholder="hourly rainfall"
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Source Type" htmlFor="admin-source-type">
                <select
                  id="admin-source-type"
                  value={sourceType}
                  onChange={(event) => setSourceType(event.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="weather">Weather</option>
                  <option value="hydrology">Hydrology</option>
                  <option value="snow">Snow</option>
                  <option value="terrain">Terrain</option>
                  <option value="official_warning">Official Warning</option>
                  <option value="field_observation">Field Observation</option>
                </select>
              </Field>
              <Field label="Access Mode" htmlFor="admin-source-access">
                <select
                  id="admin-source-access"
                  value={accessMode}
                  onChange={(event) => setAccessMode(event.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="live">Live</option>
                  <option value="cached">Cached</option>
                  <option value="sample">Sample</option>
                </select>
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Licence" htmlFor="admin-source-licence">
                <input
                  id="admin-source-licence"
                  value={licence}
                  onChange={(event) => setLicence(event.target.value)}
                  required
                  minLength={2}
                  maxLength={200}
                  placeholder="GODL"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Update Cadence (minutes)" htmlFor="admin-source-cadence">
                <input
                  id="admin-source-cadence"
                  type="number"
                  min={1}
                  max={10080}
                  value={updateFrequency}
                  onChange={(event) => setUpdateFrequency(event.target.value)}
                  required
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <Field label="Reference URL (optional)" htmlFor="admin-source-url">
              <input
                id="admin-source-url"
                value={referenceUrl}
                onChange={(event) => setReferenceUrl(event.target.value)}
                maxLength={500}
                placeholder="https://mausam.imd.gov.in"
                className={INPUT_CLASS}
              />
            </Field>

            <Field label="Trust Classification" htmlFor="admin-source-trust">
              <select
                id="admin-source-trust"
                value={trustClassification}
                onChange={(event) => setTrustClassification(event.target.value)}
                className={INPUT_CLASS}
              >
                <option value="authoritative">Authoritative</option>
                <option value="institutional">Institutional</option>
                <option value="community">Community</option>
                <option value="demo">Demo</option>
              </select>
            </Field>

            <div className="flex flex-wrap gap-4 text-xs text-on-surface-variant">
              <label className="inline-flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={isAuthoritative}
                  onChange={(event) => setIsAuthoritative(event.target.checked)}
                />
                Authoritative source
              </label>
              <label className="inline-flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={isDemoFixture}
                  onChange={(event) => setIsDemoFixture(event.target.checked)}
                />
                Demo fixture
              </label>
            </div>

            <FeedbackNote feedback={sourceFeedback} />
            <button
              type="submit"
              disabled={isRegisteringSource}
              className="self-start inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-xs font-semibold disabled:opacity-60 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">sensors</span>
              {isRegisteringSource ? "Registering…" : "Register Source"}
            </button>
          </form>
        </section>

        <section aria-labelledby="admin-fetch-title" className={CARD_CLASS}>
          <h2 id="admin-fetch-title" className="text-base font-bold text-text-primary">
            Record Source Fetch
          </h2>
          <p className="text-[11px] text-text-muted">
            Records that data was fetched from a registered source. This updates the
            source freshness timestamp used across the registry.
          </p>
          <form className="flex flex-col gap-3" onSubmit={(event) => void handleFetchSource(event)}>
            <Field label="Source ID" htmlFor="admin-fetch-id">
              <input
                id="admin-fetch-id"
                value={fetchSourceId}
                onChange={(event) => setFetchSourceId(event.target.value)}
                required
                placeholder="src-imd-aws"
                className={INPUT_CLASS}
              />
            </Field>

            <FeedbackNote feedback={fetchFeedback} />
            <button
              type="submit"
              disabled={isFetchingSource}
              className="self-start inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold disabled:opacity-60 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">cloud_sync</span>
              {isFetchingSource ? "Recording…" : "Record Fetch"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

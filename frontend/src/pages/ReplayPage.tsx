import { useCallback, useEffect, useState } from "react";
import { fetchReplayEvents, type BackendHistoricalReplayEvent } from "../api/risk";
import { Badge } from "../components/ui/Badge";
import { MOCK_REPLAY_EVENTS } from "../data/mockReplayEvents";
import type { HistoricalEvent, PlaybackSpeed, ReplayViewMode } from "../types/replay";

function mapBackendReplayEvent(evt: BackendHistoricalReplayEvent): HistoricalEvent {
  return {
    id: evt.id,
    locationId: evt.location_id,
    title: evt.title,
    sector: evt.sector,
    hazard: evt.hazard,
    dateRange: evt.date_range,
    provenance: evt.provenance,
    isPersisted: true,
    isDemoFixture: evt.is_demo_fixture,
    frames: evt.frames.map((f) => ({
      id: f.id,
      timestamp: new Date(f.timestamp).toLocaleString("en-IN", {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
      phaseLabel: f.phase_label,
      primaryMetricLabel: f.primary_metric_label,
      primaryMetricValue: f.primary_metric_value,
      secondaryMetricLabel: f.secondary_metric_label,
      secondaryMetricValue: f.secondary_metric_value,
      alertTier: f.alert_tier,
      summary: f.summary,
    })),
  };
}

/** Historical Event Replay and system loading/empty edge states matching Stitch system_states_loading_empty_event_replay. */
export function ReplayPage() {
  const [viewMode, setViewMode] = useState<ReplayViewMode>("replay");
  const [events, setEvents] = useState<HistoricalEvent[]>(MOCK_REPLAY_EVENTS);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historySourceNote, setHistorySourceNote] = useState<string>("Archival Sample");
  const [selectedEventId, setSelectedEventId] = useState(MOCK_REPLAY_EVENTS[0].id);
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<PlaybackSpeed>(1);

  const loadPersistedReplay = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetchReplayEvents({ limit: 50 });
      const persisted = response.items
        .filter((item) => item.frames.length > 0)
        .map(mapBackendReplayEvent);
      if (persisted.length > 0) {
        const combined = [...persisted, ...MOCK_REPLAY_EVENTS];
        setEvents(combined);
        setSelectedEventId((prev) =>
          combined.some((e) => e.id === prev) ? prev : persisted[0].id
        );
        setHistorySourceNote(`Persisted History (${persisted.length} sequences)`);
      } else {
        setEvents(MOCK_REPLAY_EVENTS);
        setHistorySourceNote("Archival Sample (no persisted assessments yet)");
      }
    } catch {
      setEvents(MOCK_REPLAY_EVENTS);
      setHistorySourceNote("Archival Sample (offline fallback)");
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    void loadPersistedReplay();
  }, [loadPersistedReplay]);

  const activeEvent = events.find((e) => e.id === selectedEventId) ?? events[0];
  const frames = activeEvent.frames;
  const safeIndex = Math.min(frameIndex, Math.max(0, frames.length - 1));
  const activeFrame = frames[safeIndex];

  useEffect(() => {
    if (!isPlaying || viewMode !== "replay") return;
    const intervalMs = Math.round(1800 / speed);
    const timer = window.setInterval(() => {
      setFrameIndex((prev) => {
        if (prev >= frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [isPlaying, speed, frames.length, viewMode]);

  const handleEventChange = (nextId: string) => {
    setSelectedEventId(nextId);
    setFrameIndex(0);
    setIsPlaying(false);
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            Incident Reconstruction &amp; Edge States
          </span>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Historical Event Replay
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Time-sequenced historical reconstruction alongside predictable loading and zero-threat states.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              { value: "replay", label: "Event Replay" },
              { value: "loading", label: "Loading State" },
              { value: "empty", label: "Empty / Zero-Threat" },
            ] as const
          ).map((mode) => (
            <button
              key={mode.value}
              type="button"
              onClick={() => {
                setViewMode(mode.value);
                setIsPlaying(false);
              }}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                viewMode === mode.value
                  ? "bg-primary-container text-on-primary"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {viewMode === "loading" ? (
        <section aria-label="Telemetry loading state" className="flex flex-col gap-4">
          <div className="bg-surface-container-low border border-border-hairline rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[22px] text-agency-imd animate-spin">
                sync
              </span>
              <div>
                <p className="text-xs font-semibold text-text-primary">
                  Fetching live weather and river telemetry from CWC &amp; IMD radar (3/4 stations synced)...
                </p>
                <p className="text-[11px] text-text-muted">
                  Station 4: Sonamarg High-Ridge link renegotiating packet sequence.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:w-44">
              <div className="w-full h-2 rounded-full bg-surface-variant overflow-hidden">
                <div className="h-full bg-agency-imd rounded-full" style={{ width: "75%" }} />
              </div>
              <span className="text-xs font-bold text-agency-imd">75%</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse">
            {[1, 2, 3].map((slot) => (
              <div
                key={slot}
                className="bg-surface-card border border-border-hairline rounded-xl p-5 flex flex-col gap-3"
              >
                <div className="h-4 w-28 bg-surface-variant rounded" />
                <div className="h-7 w-20 bg-surface-variant rounded" />
                <div className="h-3 w-3/4 bg-surface-variant rounded" />
                <div className="h-16 w-full bg-surface-container rounded-lg" />
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {viewMode === "empty" ? (
        <section
          aria-label="Zero threat empty state"
          className="bg-surface-card border border-border-hairline rounded-xl p-8 text-center flex flex-col items-center gap-3 max-w-xl mx-auto"
        >
          <span className="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-alert-green flex items-center justify-center">
            <span className="material-symbols-outlined text-[26px]">verified</span>
          </span>
          <h2 className="text-lg font-bold text-text-primary">
            No Active Threat Thresholds Exceeded
          </h2>
          <p className="text-xs sm:text-sm text-secondary">
            Zero sectors match high-severity flood or avalanche triggers for the selected evaluation window.
          </p>
          <button
            type="button"
            onClick={() => setViewMode("replay")}
            className="mt-1 px-5 py-2 rounded-full bg-primary-container text-on-primary text-xs font-semibold cursor-pointer"
          >
            Return to Event Replay
          </button>
        </section>
      ) : null}

      {viewMode === "replay" ? (
        <div className="flex flex-col gap-5">
          <section className="bg-surface-card border border-border-hairline rounded-xl p-5 flex flex-col gap-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex flex-col gap-1 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <label htmlFor="replay-event-select" className="text-xs font-semibold text-text-primary">
                    Select Historical Event
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-text-muted">
                      {isLoadingHistory ? "Syncing persisted history..." : historySourceNote}
                    </span>
                    <button
                      type="button"
                      onClick={() => void loadPersistedReplay()}
                      disabled={isLoadingHistory}
                      className="text-[11px] font-semibold text-primary hover:underline disabled:opacity-50 cursor-pointer"
                    >
                      Refresh
                    </button>
                  </div>
                </div>
                <select
                  id="replay-event-select"
                  value={activeEvent.id}
                  onChange={(e) => handleEventChange(e.target.value)}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs sm:text-sm font-medium text-text-primary"
                >
                  {events.map((evt) => (
                    <option key={evt.id} value={evt.id}>
                      {evt.isPersisted ? "[DB] " : "[Sample] "}
                      {evt.title} ({evt.dateRange})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1 md:w-64">
                <label htmlFor="replay-frame-select" className="text-xs font-semibold text-text-primary">
                  Jump to Timestamp
                </label>
                <select
                  id="replay-frame-select"
                  value={safeIndex}
                  onChange={(e) => {
                    setIsPlaying(false);
                    setFrameIndex(Number(e.target.value));
                  }}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs font-medium text-text-primary"
                >
                  {frames.map((frame, idx) => (
                    <option key={frame.id} value={idx}>
                      {frame.timestamp}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-2 pt-2 border-t border-border-hairline">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-text-primary">{activeFrame.phaseLabel}</span>
                <span className="text-text-muted">
                  Frame {safeIndex + 1} of {frames.length}
                </span>
              </div>

              <input
                type="range"
                aria-label="Timeline scrubber"
                min={0}
                max={frames.length - 1}
                value={safeIndex}
                onChange={(e) => {
                  setIsPlaying(false);
                  setFrameIndex(Number(e.target.value));
                }}
                className="w-full accent-[#1d1b16] cursor-pointer"
              />

              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    aria-label="Step back"
                    disabled={safeIndex === 0}
                    onClick={() => {
                      setIsPlaying(false);
                      setFrameIndex((prev) => Math.max(0, prev - 1));
                    }}
                    className="h-9 px-3 rounded-full border border-border-hairline bg-surface-container-low hover:bg-surface-container text-xs font-semibold disabled:opacity-40 cursor-pointer"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (safeIndex >= frames.length - 1) setFrameIndex(0);
                      setIsPlaying((prev) => !prev);
                    }}
                    className="inline-flex items-center gap-1.5 h-9 px-5 rounded-full bg-primary-container text-on-primary text-xs font-semibold cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {isPlaying ? "pause" : "play_arrow"}
                    </span>
                    <span>{isPlaying ? "Pause" : "Play"}</span>
                  </button>
                  <button
                    type="button"
                    aria-label="Step forward"
                    disabled={safeIndex >= frames.length - 1}
                    onClick={() => {
                      setIsPlaying(false);
                      setFrameIndex((prev) => Math.min(frames.length - 1, prev + 1));
                    }}
                    className="h-9 px-3 rounded-full border border-border-hairline bg-surface-container-low hover:bg-surface-container text-xs font-semibold disabled:opacity-40 cursor-pointer"
                  >
                    Next
                  </button>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-semibold text-text-muted mr-1">Speed:</span>
                  {([1, 2, 4] as const).map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      onClick={() => setSpeed(spd)}
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold cursor-pointer ${
                        speed === spd
                          ? "bg-primary-container text-on-primary"
                          : "bg-surface-container text-on-surface-variant"
                      }`}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section
            aria-label="Replay frame snapshot"
            className="bg-surface-card border border-border-hairline rounded-xl p-5 flex flex-col gap-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border-hairline">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  {activeEvent.sector} • {activeFrame.timestamp}
                </span>
                <h2 className="text-base font-bold text-text-primary mt-0.5">{activeEvent.title}</h2>
              </div>
              <Badge
                tone={
                  activeFrame.alertTier === "Emergency" || activeFrame.alertTier === "High Risk"
                    ? "emergency"
                    : "warning"
                }
              >
                {activeFrame.alertTier}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-surface-container-low border border-border-hairline">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  {activeFrame.primaryMetricLabel}
                </span>
                <p className="text-xl font-bold text-text-primary mt-1">
                  {activeFrame.primaryMetricValue}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-surface-container-low border border-border-hairline">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  {activeFrame.secondaryMetricLabel}
                </span>
                <p className="text-xl font-bold text-text-primary mt-1">
                  {activeFrame.secondaryMetricValue}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-surface-container-low border border-border-hairline">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  Provenance
                </span>
                <p className="text-xs font-medium text-on-surface-variant mt-1">
                  {activeEvent.provenance}
                </p>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-secondary">{activeFrame.summary}</p>
          </section>
        </div>
      ) : null}
    </div>
  );
}

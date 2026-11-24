import { useEffect, useState } from "react";

interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<HealthResponse>;
      })
      .then(setHealth)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Backend unreachable");
      });
  }, []);

  return (
    <main style={{ fontFamily: "Inter, system-ui, sans-serif", maxWidth: 720, margin: "3rem auto", padding: "0 1rem" }}>
      <h1>HIMA-RAKSHAK</h1>
      <p>Multi-hazard flood and avalanche decision-support prototype for Jammu &amp; Kashmir.</p>
      <p style={{ fontSize: "0.9rem", color: "#4a463f" }}>
        Decision-support only: complements—and does not replace—official warnings or expert judgement.
      </p>
      <section style={{ padding: "1rem", border: "1px solid #d9d3c9", borderRadius: 6, background: "#faf9f8" }}>
        <strong>Backend Status:</strong>{" "}
        {health ? `${health.status.toUpperCase()} (${health.environment})` : error ? `Unavailable (${error})` : "Checking..."}
      </section>
    </main>
  );
}

import HelloClient from "./HelloClient";

// Read API_URL at request time (not build time) so the backend URL can change
// without rebuilding the image — it's a runtime env var on Cloud Run.
export const dynamic = "force-dynamic";

export default function Page() {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", padding: "0 1.5rem" }}>
      <h1>Pipeline</h1>
      <p style={{ color: "#555" }}>Frontend ↔ backend connectivity check</p>
      <HelloClient apiUrl={apiUrl} />
    </main>
  );
}

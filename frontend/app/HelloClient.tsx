"use client";

import { useEffect, useState } from "react";

export default function HelloClient({ apiUrl }: { apiUrl: string }) {
  const [message, setMessage] = useState("Loading…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Called directly from the browser → backend (relies on backend CORS).
    fetch(`${apiUrl}/api/hello`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setMessage(data.message))
      .catch((err) => setError(err.message));
  }, [apiUrl]);

  return (
    <div>
      {error ? (
        <p style={{ color: "crimson" }}>Backend error: {error}</p>
      ) : (
        <p style={{ fontSize: "1.5rem" }}>{message}</p>
      )}
      <small style={{ color: "#999" }}>API: {apiUrl}</small>
    </div>
  );
}

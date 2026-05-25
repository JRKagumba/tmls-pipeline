"use client";

import { useState } from "react";

type Usage = {
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
};

type ChatResponse = {
  reply: string;
  model: string;
  usage: Usage;
  latency_ms: number;
  stored_path: string | null;
};

export default function ChatBox({ apiUrl }: { apiUrl: string }) {
  const [message, setMessage] = useState("");
  const [data, setData] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const text = message.trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `HTTP ${res.status}`);
      }
      setData((await res.json()) as ChatResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter inserts a newline.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <section style={{ marginTop: "2.5rem", borderTop: "1px solid #eee", paddingTop: "1.5rem" }}>
      <h2 style={{ marginBottom: "0.25rem" }}>Ask the model</h2>
      <p style={{ color: "#777", marginTop: 0, fontSize: "0.9rem" }}>
        Sent to OpenAI via the backend; each exchange is logged to GCS.
      </p>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={onKeyDown}
        rows={3}
        placeholder="Type a message and press Enter…"
        style={{
          width: "100%",
          padding: "0.6rem",
          fontSize: "1rem",
          fontFamily: "inherit",
          boxSizing: "border-box",
          borderRadius: 6,
          border: "1px solid #ccc",
        }}
      />
      <button
        onClick={send}
        disabled={loading || message.trim().length === 0}
        style={{
          marginTop: "0.5rem",
          padding: "0.5rem 1.2rem",
          fontSize: "1rem",
          borderRadius: 6,
          border: "none",
          background: loading ? "#999" : "#2563eb",
          color: "white",
          cursor: loading ? "default" : "pointer",
        }}
      >
        {loading ? "Sending…" : "Send"}
      </button>

      {error && <p style={{ color: "crimson", marginTop: "1rem" }}>Error: {error}</p>}

      {data && (
        <div style={{ marginTop: "1.25rem" }}>
          <div
            style={{
              whiteSpace: "pre-wrap",
              background: "#f6f8fa",
              borderRadius: 6,
              padding: "0.9rem",
            }}
          >
            {data.reply}
          </div>
          <small style={{ color: "#999", display: "block", marginTop: "0.5rem" }}>
            {data.model} · {data.usage.total_tokens ?? "?"} tokens
            {data.usage.input_tokens != null &&
              ` (in ${data.usage.input_tokens} / out ${data.usage.output_tokens})`}{" "}
            · {data.latency_ms} ms ·{" "}
            {data.stored_path ? `saved ${data.stored_path}` : "not stored"}
          </small>
        </div>
      )}
    </section>
  );
}

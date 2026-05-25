import type { ReactNode } from "react";

export const metadata = {
  title: "Pipeline",
  description: "Hello world frontend ↔ backend connectivity check",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily:
            "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
          margin: 0,
        }}
      >
        {children}
      </body>
    </html>
  );
}

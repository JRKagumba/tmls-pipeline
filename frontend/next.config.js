/** @type {import('next').NextConfig} */
const nextConfig = {
  // Produces a minimal self-contained server (.next/standalone/server.js)
  // for a small Docker image on Cloud Run.
  output: "standalone",
};

module.exports = nextConfig;

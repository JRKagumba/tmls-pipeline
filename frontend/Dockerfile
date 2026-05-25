# syntax=docker/dockerfile:1

# ---- build stage ----
FROM node:20-slim AS builder
WORKDIR /app

# Install deps from the lockfile (npm ci requires package-lock.json).
COPY package.json package-lock.json ./
RUN npm ci

# Build the standalone Next.js output.
COPY . .
RUN npm run build

# ---- runtime stage ----
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
# Cloud Run injects PORT (8080); default it for local `docker run`.
ENV PORT=8080
# Next's standalone server must bind all interfaces for Cloud Run.
ENV HOSTNAME=0.0.0.0

# Copy the self-contained server and its assets.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 8080
CMD ["node", "server.js"]

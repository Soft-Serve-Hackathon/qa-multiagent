# Dockerfile for Frontend (Next.js 14)
# Build: docker build -t qa-multiagent-frontend:latest ./frontend
# Run: docker run -p 3000:3000 qa-multiagent-frontend:latest

# ── Stage 1: deps ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --prefer-offline

# ── Stage 2: builder ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Internal Docker URL so Next.js rewrites proxy to the backend container
ARG NEXT_PUBLIC_API_URL=http://backend:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

RUN npm run build

# ── Stage 3: runner ────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:3000 || exit 1

CMD ["node", "server.js"]

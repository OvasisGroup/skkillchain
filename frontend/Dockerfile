# syntax=docker/dockerfile:1

# pnpm@11.12.0 (pinned below, matching package.json) requires Node >=22.13 —
# confirmed by actually building this image; node:20 fails at `pnpm install`
# with ERR_UNKNOWN_BUILTIN_MODULE before it even gets to dependency errors.
FROM node:22-alpine AS base

# Matches package.json's pinned "packageManager" field exactly, rather than
# whatever corepack's own default resolves to — a mismatched pnpm version
# can produce a lockfile that fails --frozen-lockfile's integrity check.
RUN corepack enable && corepack prepare pnpm@11.12.0 --activate


FROM base AS deps

WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# Registry fetches from inside a container's build network are more prone to
# transient stalls than a host-network install — raised retries/timeout cost
# nothing on a healthy connection and turn a flaky single-package fetch into
# a retry instead of a failed build.
# Cache mount for pnpm's content-addressable store — a retried/resumed
# build (this stage re-running because a later stage changed) reuses
# already-downloaded packages instead of re-fetching everything, on top of
# BuildKit's normal layer cache.
RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store \
    pnpm config set fetch-retries 5 \
    && pnpm config set fetch-retry-mintimeout 20000 \
    && pnpm config set fetch-timeout 120000 \
    && pnpm install --frozen-lockfile


FROM base AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* vars are inlined into the client bundle at build time, not
# read at container start — every one of them has to be a build arg here,
# not a runtime ENV on the final image (which would have no effect on
# already-built output). Grep the codebase for `process.env.NEXT_PUBLIC_`
# before adding a new one — this list is not automatically kept in sync.
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
RUN pnpm build


FROM base AS runtime

RUN apk add --no-cache curl \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app

WORKDIR /app
# output: "standalone" (next.config.ts) traces the minimal server + pruned
# node_modules needed at runtime — copying just this, instead of the full
# node_modules from the build stage, is most of why this image is small.
COPY --from=builder --chown=app:app /app/public ./public
COPY --from=builder --chown=app:app /app/.next/standalone ./
COPY --from=builder --chown=app:app /app/.next/static ./.next/static

USER app
ENV NODE_ENV=production \
    HOSTNAME="0.0.0.0" \
    PORT=3000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

CMD ["node", "server.js"]

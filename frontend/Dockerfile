FROM node:22-alpine AS base

WORKDIR /app

RUN apk add --no-cache libc6-compat
RUN corepack enable

FROM base AS builder

COPY frontend/package.json ./package.json
COPY frontend/pnpm-lock.yaml ./pnpm-lock.yaml

RUN pnpm install --frozen-lockfile

COPY frontend/ ./

ARG NEXT_PUBLIC_API_BASE_URL
ARG API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV API_BASE_URL=$API_BASE_URL

RUN pnpm build

FROM base AS runner

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ARG API_BASE_URL
ENV API_BASE_URL=$API_BASE_URL

WORKDIR /app

COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

CMD ["node", "server.js"]

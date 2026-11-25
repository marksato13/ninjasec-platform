FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL=http://backend:8024/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
# Sin esto `next start` no encuentra la configuracion y usa los valores por defecto en
# las opciones de ejecucion: volvia a enviar `X-Powered-By: Next.js` aunque el build
# dijera `poweredByHeader: false`. Las cabeceras y los rewrites si van en el build.
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/node_modules ./node_modules

USER node

EXPOSE 3018

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3018"]

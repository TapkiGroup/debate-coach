FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    else npm i; fi

COPY . .
ARG NEXT_PUBLIC_BACKEND_URL=/api
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
RUN npm run build

FROM node:20-alpine AS run
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app/package.json /app/package.json

RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm i --omit=dev; fi

COPY --from=build /app/.next /app/.next
COPY --from=build /app/public /app/public

EXPOSE 3000
CMD npx next start -p ${PORT:-3000} -H 0.0.0.0

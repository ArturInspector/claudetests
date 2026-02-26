FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Reinstall deps at startup so volume-mounted node_modules stays in sync with package.json
CMD ["sh", "-c", "npm ci && npm run dev -- --hostname 0.0.0.0 --port 3000"]

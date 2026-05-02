# [SPEC-B-001] Frontend image (Vite dev server on :3000).
# Build context is the repo root so we can copy src/frontend/ into /app.

FROM node:20-alpine

WORKDIR /app

# Install deps first for layer caching.
COPY src/frontend/package.json src/frontend/package-lock.json* ./
RUN npm install

COPY src/frontend/ ./

EXPOSE 3000

CMD ["npm", "run", "dev"]

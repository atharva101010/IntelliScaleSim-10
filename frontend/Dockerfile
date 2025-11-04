# Frontend Dockerfile (dev-oriented)
FROM node:20-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json* .npmrc* ./
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]

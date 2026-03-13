# Node.js 22 LTS
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev

FROM node:22-alpine
WORKDIR /app
ENV NODE_OPTIONS="--max-old-space-size=384"
COPY --from=deps /app/node_modules ./node_modules
COPY src ./src
COPY package.json .
EXPOSE 8081
CMD ["node", "src/server.js"]

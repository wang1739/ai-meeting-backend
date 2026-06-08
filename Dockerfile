FROM node:20-alpine
RUN apk add --no-cache openssl
WORKDIR /app
COPY package*.json prisma.config.ts ./
RUN npm ci
COPY prisma/ ./prisma/
COPY dist/ ./dist/
RUN chmod +x node_modules/.bin/*
EXPOSE 3000
CMD npx prisma db push && npx prisma generate && node dist/src/main.js

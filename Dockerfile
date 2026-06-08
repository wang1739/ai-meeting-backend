# ---- Build Stage ----
FROM node:20-alpine AS builder

WORKDIR /app

# 安装 Prisma 依赖（openssl for prisma generate）
RUN apk add --no-cache openssl

COPY package*.json prisma.config.ts ./
COPY prisma/ ./prisma/

RUN npm ci

RUN chmod +x node_modules/.bin/*

COPY . .

# 构建 NestJS 应用
RUN npm run build

# ---- Production Stage ----
FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache openssl

# 复制 node_modules（含 Prisma Client）
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/prisma.config.ts ./

EXPOSE 3000

# 启动时先同步数据库 schema，再启动应用
CMD ["sh", "-c", "npx prisma db push --accept-data-loss && node dist/main"]

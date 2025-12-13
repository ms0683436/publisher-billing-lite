FROM node:20-alpine

WORKDIR /app

# Enable pnpm via Corepack
RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

# Copy dependency files first (for build cache)
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

EXPOSE 5173

# Default dev command
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

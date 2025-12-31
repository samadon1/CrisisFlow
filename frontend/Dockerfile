# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev)
RUN npm ci || npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies (express is listed there)
RUN npm ci --only=production || npm install --only=production

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Copy server file
COPY server.js ./

# Use PORT from Cloud Run environment
EXPOSE 8080

# Start the server
CMD ["node", "server.js"]
# Dockerfile for MergeMind UI service
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY ui/web/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY ui/web/ .

# Set build-time environment variable for API URL
ARG VITE_API_BASE_URL=https://mergemind-api-812918665937.us-central1.run.app/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Start the application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]

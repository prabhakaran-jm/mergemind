# Dockerfile for MergeMind UI service
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY ui/web/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY ui/web/ .

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# Start the application
CMD ["npm", "run", "preview"]

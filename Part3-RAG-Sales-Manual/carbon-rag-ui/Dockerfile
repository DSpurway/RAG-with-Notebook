# RHEL-based Dockerfile for Carbon RAG UI
# Based on successful RHEL deployment script approach

FROM registry.access.redhat.com/ubi9/ubi:latest

# Install Node.js 18 and build dependencies
RUN dnf install -y nodejs npm git gcc gcc-c++ make python3 && \
    dnf clean all

# Create non-root user
RUN useradd -m -u 1001 nextjs

WORKDIR /app

# Set npm cache directory to writable location
ENV npm_config_cache=/tmp/.npm

# Copy package files
COPY --chown=nextjs:nextjs package.json ./

# Install dependencies as nextjs user
USER nextjs
RUN npm install

# Copy application files
COPY --chown=nextjs:nextjs . .

# Runtime environment variable for backend URL (used by API routes, not client)
# Uses internal OpenShift service name - no FQDN needed!
ENV RAG_BACKEND_URL=http://rag-backend:8080

# Build the application (eslintrc.json already exists in repo)
RUN npm run build

# Clean npm cache after build to avoid permission issues
RUN rm -rf /tmp/.npm

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV npm_config_cache=/tmp/.npm
ENV HOME=/tmp

# Start the application
CMD ["npm", "start"]
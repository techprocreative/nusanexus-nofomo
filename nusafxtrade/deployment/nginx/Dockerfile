# NusaNexus NoFOMO - Nginx Production Dockerfile
# Multi-stage build for optimal reverse proxy

# Build stage
FROM nginx:alpine as builder

# Copy custom configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Production stage
FROM nginx:alpine as production

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directory for SSL certificates
RUN mkdir -p /etc/ssl/certs /etc/ssl/private && \
    chown -R nginx:nginx /etc/ssl

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
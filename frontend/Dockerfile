# Dockerfile for Frontend (Vanilla HTML/CSS/JS)
# Build: docker build -t qa-multiagent-frontend:latest ./frontend
# Run: docker run -p 3000:3000 qa-multiagent-frontend:latest

FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy static files to nginx
COPY src/static/ ./
COPY src/js/ ./js/

# Copy nginx configuration
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

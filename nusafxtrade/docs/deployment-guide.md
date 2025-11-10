# NusaNexus NoFOMO - Production Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Render Deployment](#render-deployment)
5. [Database Setup](#database-setup)
6. [SSL Configuration](#ssl-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Configuration](#security-configuration)
9. [Testing Deployment](#testing-deployment)
10. [Troubleshooting](#troubleshooting)

## Overview

NusaNexus NoFOMO is a comprehensive AI-powered trading platform that can be deployed to production on Render and other cloud platforms. This guide provides step-by-step instructions for deploying the platform to production.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Nginx Proxy   │────│   Frontend      │
│   (SSL Term)    │    │   (Security)    │    │   (Next.js)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌─────────────┐    ┌─────────────┐
            │  Backend    │    │   AI Engine │
            │  (FastAPI)  │    │  (Python)   │
            └─────────────┘    └─────────────┘
                    │                   │
            ┌─────────────┐    ┌─────────────┐
            │  Database   │    │   Redis     │
            │ (Supabase)  │    │ (Caching)   │
            └─────────────┘    └─────────────┘
```

## Prerequisites

### Required Services
- **Render Account** (for hosting)
- **Supabase Account** (for database and auth)
- **GitHub Account** (for CI/CD)
- **Domain Name** (optional, for custom domain)
- **SSL Certificate** (Let's Encrypt or custom)

### Required APIs
- **OpenRouter API** (for AI features)
- **Binance API** (for trading)
- **Bybit API** (for trading)
- **Tripay API** (for payments)

### Local Development
- **Docker** and **Docker Compose**
- **Python 3.11+**
- **Node.js 18+**
- **Git**

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-username/nusafxtrade.git
cd nusafxtrade
```

### 2. Environment Variables

Create environment files for each environment:

#### Development (`.env.development`)
```bash
cp .env.development .env.development.local
# Edit with your local development values
```

#### Staging (`.env.staging`)
```bash
cp .env.staging .env.staging.production
# Edit with your staging values
```

#### Production (`.env.production`)
```bash
cp .env.production .env.production.production
# Edit with your production values
```

## Render Deployment

### 1. Prepare for Render

1. **Connect GitHub Repository**
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

2. **Configure Secrets**
   In Render dashboard, add the following secrets:
   ```bash
   POSTGRES_PASSWORD=your-secure-postgres-password
   SECRET_KEY=your-secure-secret-key-32-chars-min
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   OPENROUTER_API_KEY=your-openrouter-api-key
   SENTRY_DSN=your-sentry-dsn
   BACKEND_URL=https://nusafx-backend.onrender.com
   ```

### 2. Deploy Services

Render will automatically deploy the following services:

1. **Database** (`nusafx-database`)
   - PostgreSQL instance
   - Automatically configured with your secrets

2. **Redis** (`nusafx-redis`)
   - Redis instance for caching and queues

3. **Backend** (`nusafx-backend`)
   - FastAPI application
   - Health checks configured
   - Auto-scaling enabled

4. **Frontend** (`nusafx-frontend`)
   - Next.js application
   - Static asset optimization
   - CDN enabled

5. **AI Engine** (`nusafx-ai-engine`)
   - Python AI processing
   - Background worker

6. **Bot Runner** (`nusafx-bot-runner`)
   - Trading bot execution
   - Background worker

### 3. Custom Domain (Optional)

1. **Add Custom Domain**
   ```bash
   # In Render dashboard
   - Go to your frontend service
   - Settings → Domains
   - Add your custom domain
   ```

2. **SSL Certificate**
   ```bash
   # Render automatically provisions Let's Encrypt certificates
   # No additional configuration needed
   ```

## Database Setup

### 1. Supabase Configuration

1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com
   # Create new project
   # Note the URL and keys
   ```

2. **Run Database Migration**
   ```sql
   -- Execute the migration script
   \i deployment/database/supabase-config.sql
   ```

3. **Configure Row Level Security**
   ```sql
   -- Already included in the migration script
   -- RLS policies are automatically applied
   ```

### 2. Connection Pooling

Configure connection pooling in your backend:

```python
# In backend/app/core/database.py
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}
```

## SSL Configuration

### 1. Automatic SSL (Render)
Render automatically provides SSL certificates. No additional configuration needed.

### 2. Custom Domain SSL
If using a custom domain with your own certificate:

```nginx
# deployment/nginx/nginx.conf
ssl_certificate /etc/ssl/certs/nusafxtrade.crt;
ssl_certificate_key /etc/ssl/private/nusafxtrade.key;
```

### 3. Security Headers
Security headers are automatically configured in the Nginx configuration.

## Monitoring Setup

### 1. Application Monitoring

1. **Prometheus Metrics**
   ```bash
   # Enable metrics in your services
   # Access at: https://your-service.onrender.com/metrics
   ```

2. **Grafana Dashboards**
   ```bash
   # Access Grafana at: http://localhost:3001 (local) or your monitoring URL
   # Login: admin / admin123 (change in production)
   ```

### 2. Log Aggregation

1. **Loki Configuration**
   ```bash
   # Logs are automatically collected
   # View in Grafana → Explore → Loki
   ```

2. **AlertManager**
   ```bash
   # Configure alerts in alertmanager.yml
   # Access at: http://localhost:9093
   ```

### 3. Error Tracking

1. **Sentry Integration**
   ```bash
   # Errors are automatically sent to Sentry
   # Configure SENTRY_DSN in environment
   ```

## Security Configuration

### 1. Network Security

1. **Firewall Rules**
   ```bash
   # Only allow necessary ports
   - 80/443 (HTTP/HTTPS)
   - SSH (22) for management
   ```

2. **Rate Limiting**
   ```bash
   # Configured in nginx rate-limiting.conf
   # Prevents DDoS and abuse
   ```

### 2. Application Security

1. **CORS Configuration**
   ```bash
   # Configured in production environment
   # Only allows specific origins
   ```

2. **Authentication**
   ```bash
   # Supabase Auth with JWT tokens
   # Session timeout configured
   ```

### 3. Data Security

1. **Encryption**
   ```bash
   # Database encryption at rest
   # TLS encryption in transit
   # Sensitive data encrypted in application
   ```

2. **Backup Strategy**
   ```bash
   # Daily automated backups
   # 30-day retention
   # Point-in-time recovery
   ```

## Testing Deployment

### 1. Health Checks

1. **Backend Health**
   ```bash
   curl https://nusafx-backend.onrender.com/health
   # Expected: {"status": "healthy"}
   ```

2. **Frontend Health**
   ```bash
   curl https://nusafxtrade.com/health
   # Expected: 200 OK with frontend loading
   ```

3. **Database Health**
   ```bash
   # Check via backend API
   curl https://nusafx-backend.onrender.com/api/v1/health/database
   ```

### 2. Functional Testing

1. **User Registration**
   ```bash
   # Test user registration flow
   # Verify email confirmation
   ```

2. **Trading Bot Creation**
   ```bash
   # Test bot creation and configuration
   # Verify API connectivity
   ```

3. **AI Strategy Generation**
   ```bash
   # Test AI strategy generation
   # Verify OpenRouter API integration
   ```

### 3. Performance Testing

1. **Load Testing**
   ```bash
   # Use tools like k6 or Artillery
   # Test under expected load
   ```

2. **Database Performance**
   ```bash
   # Monitor query performance
   # Check connection pool usage
   ```

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   ```bash
   # Check logs in Render dashboard
   # Verify environment variables
   # Ensure all secrets are set
   ```

2. **Database Connection Issues**
   ```bash
   # Verify Supabase credentials
   # Check network connectivity
   # Review connection pool settings
   ```

3. **SSL Certificate Issues**
   ```bash
   # Wait for certificate provisioning
   # Check domain configuration
   # Verify DNS settings
   ```

4. **High Memory Usage**
   ```bash
   # Check for memory leaks
   # Optimize database queries
   # Review caching strategy
   ```

### Monitoring Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f service-name

# Monitor resource usage
docker stats

# Database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

### Emergency Procedures

1. **Rollback Deployment**
   ```bash
   # Use GitHub Actions rollback workflow
   # Or manual deployment of previous version
   ```

2. **Database Recovery**
   ```bash
   # Restore from backup
   # Point-in-time recovery if needed
   ```

3. **Service Isolation**
   ```bash
   # Disable problematic service in render.yaml
   # Maintain partial functionality
   ```

## Post-Deployment Checklist

- [ ] All services deployed successfully
- [ ] Health checks passing
- [ ] SSL certificates configured
- [ ] Database migrations applied
- [ ] Monitoring dashboards accessible
- [ ] Error tracking configured
- [ ] Backup systems operational
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated

## Support

For deployment support:
- Check the troubleshooting section
- Review application logs
- Monitor error tracking in Sentry
- Contact development team

For production issues:
- Check the status page
- Review incident reports
- Execute rollback procedures if needed
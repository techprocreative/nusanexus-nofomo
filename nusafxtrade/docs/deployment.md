# Deployment Guide - NusaNexus NoFOMO

This guide covers deploying NusaNexus NoFOMO to production environments, including Render, Docker, and cloud platforms.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   Bot Runner    │
│   (Next.js)     │◄──►│    (FastAPI)     │◄──►│   (Freqtrade)   │
│   Port: 3000    │    │    Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Supabase   │  │   Redis      │  │   Tripay     │  │ Exchange │ │
│  │   Database   │  │   Queue      │  │   Payment    │  │   APIs   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## 1. Render Deployment (Recommended)

Render provides a simple, cost-effective way to deploy the entire stack.

### Frontend Deployment

1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Connect your GitHub/GitLab repository
   - Select the `nusafxtrade` folder

2. **Create Frontend Service**
   ```yaml
   # Frontend Service Configuration
   Name: nusanexus-frontend
   Region: Singapore (Southeast Asia)
   Branch: main
   Root Directory: nusafxtrade/frontend
   Build Command: npm install && npm run build
   Start Command: npm start
   ```

3. **Environment Variables**
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_APP_ENV=production
   NEXT_PUBLIC_APP_NAME=NusaNexus NoFOMO
   ```

### Backend API Deployment

1. **Create Backend Service**
   ```yaml
   # Backend Service Configuration
   Name: nusanexus-api
   Region: Singapore (Southeast Asia)
   Branch: main
   Root Directory: nusafxtrade/backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. **Environment Variables**
   ```env
   # Core Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   
   # Security
   ENCRYPTION_KEY=your-32-character-encryption-key
   JWT_SECRET=your-jwt-secret-key
   
   # External APIs
   BINANCE_API_KEY=your-binance-api-key
   BINANCE_API_SECRET=your-binance-api-secret
   BYBIT_API_KEY=your-bybit-api-key
   BYBIT_API_SECRET=your-bybit-api-secret
   OPENROUTER_API_KEY=your-openrouter-api-key
   
   # Payment
   TRIPAY_MERCHANT_CODE=your-merchant-code
   TRIPAY_API_KEY=your-tripay-api-key
   TRIPAY_SANDBOX=false
   
   # Application
   APP_ENV=production
   APP_DEBUG=false
   LOG_LEVEL=INFO
   ```

### Bot Runner Deployment

1. **Create Bot Runner Service**
   ```yaml
   # Bot Runner Service Configuration
   Name: nusanexus-bot-runner
   Region: Singapore (Southeast Asia)
   Branch: main
   Root Directory: nusafxtrade/bot-runner
   Build Command: pip install -r requirements.txt && pip install freqtrade[talib]
   Start Command: python bot_runner.py
   ```

2. **Environment Variables**
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   REDIS_URL=redis://redis:6379/0
   BINANCE_API_KEY=your-binance-api-key
   BINANCE_API_SECRET=your-binance-api-secret
   APP_ENV=production
   ```

### Redis Deployment

1. **Create Redis Service**
   - Use Render's managed Redis
   - Select appropriate memory size (1GB minimum)
   - Configure environment variables for bot runner

### AI Engine Deployment

1. **Create AI Engine Service**
   ```yaml
   # AI Engine Service Configuration
   Name: nusanexus-ai
   Region: Singapore (Southeast Asia)
   Branch: main
   Root Directory: nusafxtrade/ai_engine
   Build Command: pip install -r requirements.txt
   Start Command: python strategy_generator.py
   ```

2. **Environment Variables**
   ```env
   OPENROUTER_API_KEY=your-openrouter-api-key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   AI_MODEL=anthropic/claude-3-sonnet
   APP_ENV=production
   ```

## 2. Docker Deployment

### Multi-Container Setup

1. **Docker Compose Configuration**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   
   services:
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
         - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
         - NEXT_PUBLIC_APP_ENV=production
       depends_on:
         - backend
   
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - SUPABASE_URL=${SUPABASE_URL}
         - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
         - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
         - DATABASE_URL=${DATABASE_URL}
         - REDIS_URL=redis://redis:6379/0
         - ENCRYPTION_KEY=${ENCRYPTION_KEY}
         - JWT_SECRET=${JWT_SECRET}
         - BINANCE_API_KEY=${BINANCE_API_KEY}
         - BINANCE_API_SECRET=${BINANCE_API_SECRET}
         - BYBIT_API_KEY=${BYBIT_API_KEY}
         - BYBIT_API_SECRET=${BYBIT_API_SECRET}
         - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
         - TRIPAY_MERCHANT_CODE=${TRIPAY_MERCHANT_CODE}
         - TRIPAY_API_KEY=${TRIPAY_API_KEY}
         - TRIPAY_SANDBOX=false
         - APP_ENV=production
       depends_on:
         - redis
   
     bot-runner:
       build: ./bot-runner
       environment:
         - SUPABASE_URL=${SUPABASE_URL}
         - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
         - REDIS_URL=redis://redis:6379/0
         - BINANCE_API_KEY=${BINANCE_API_KEY}
         - BINANCE_API_SECRET=${BINANCE_API_SECRET}
         - APP_ENV=production
       depends_on:
         - redis
   
    ai-engine:
      build: ./ai_engine
       environment:
         - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
         - SUPABASE_URL=${SUPABASE_URL}
         - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
         - AI_MODEL=anthropic/claude-3-sonnet
         - APP_ENV=production
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
   
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
       depends_on:
         - frontend
         - backend
   ```

2. **Environment File**
   ```bash
   # .env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   ENCRYPTION_KEY=your-32-character-encryption-key
   JWT_SECRET=your-jwt-secret-key
   BINANCE_API_KEY=your-binance-api-key
   BINANCE_API_SECRET=your-binance-api-secret
   BYBIT_API_KEY=your-bybit-api-key
   BYBIT_API_SECRET=your-bybit-api-secret
   OPENROUTER_API_KEY=your-openrouter-api-key
   TRIPAY_MERCHANT_CODE=your-merchant-code
   TRIPAY_API_KEY=your-tripay-api-key
   ```

3. **Deploy with Docker**
   ```bash
   # Build and start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   ```

## 3. Cloud Platform Deployment

### AWS Deployment

1. **EC2 Setup**
   ```bash
   # Launch EC2 instance (t3.medium or larger)
   # Install Docker and Docker Compose
   sudo yum update -y
   sudo yum install docker -y
   sudo systemctl start docker
   sudo usermod -a -G docker ec2-user
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd nusanexus/nusafxtrade
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your values
   
   # Deploy
   docker-compose up -d
   ```

### Google Cloud Platform

1. **Cloud Run Deployment**
   ```yaml
   # Cloud Run service configuration
   apiVersion: serving.knative.dev/v1
   kind: Service
   metadata:
     name: nusanexus-backend
     annotations:
       run.googleapis.com/ingress: all
   spec:
     template:
       metadata:
         annotations:
           run.googleapis.com/cpu-throttling: "false"
           run.googleapis.com/memory: "1Gi"
       spec:
         containerConcurrency: 80
         containers:
         - image: gcr.io/PROJECT-ID/nusanexus-backend
           ports:
           - name: http1
             containerPort: 8000
           env:
           - name: SUPABASE_URL
             value: "https://your-project.supabase.co"
           # Add other environment variables
   ```

2. **Deploy Commands**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/PROJECT-ID/nusanexus-backend
   gcloud builds submit --tag gcr.io/PROJECT-ID/nusanexus-frontend
   gcloud builds submit --tag gcr.io/PROJECT-ID/nusanexus-ai
   
   # Deploy to Cloud Run
   gcloud run deploy nusanexus-backend --image gcr.io/PROJECT-ID/nusanexus-backend --platform managed
   gcloud run deploy nusanexus-frontend --image gcr.io/PROJECT-ID/nusanexus-frontend --platform managed
   gcloud run deploy nusanexus-ai --image gcr.io/PROJECT-ID/nusanexus-ai --platform managed
   ```

## 4. Database Migration in Production

### Supabase Migration
```bash
# Using Supabase CLI
supabase db push

# Or using the setup script
python backend/scripts/setup_database.py --skip-verification
```

### Manual Migration
```sql
-- Apply migrations in order
-- 1. Execute 001_initial_schema.sql
-- 2. Execute 002_indexes_and_triggers.sql
-- 3. Skip 003_sample_data.sql for production
```

## 5. SSL/TLS Configuration

### Nginx SSL Setup
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Let's Encrypt SSL
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 6. Monitoring and Logging

### Health Checks
```python
# backend/app/core/health.py
from fastapi import FastAPI
from supabase import create_client

app = FastAPI()

@app.get("/health")
async def health_check():
    try:
        # Database check
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        result = supabase.table("users").select("id").limit(1).execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500
```

### Log Aggregation
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
```

## 7. Backup Strategy

### Database Backup
```bash
# Supabase automatic backups are included
# For additional backup, use pg_dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### File System Backup
```bash
# Backup uploaded files and logs
tar -czf backup_files_$(date +%Y%m%d).tar.gz /var/log/nusanexus/ uploads/
```

## 8. Performance Optimization

### CDN Configuration
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['your-supabase-project.supabase.co'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://your-backend.render.com/api/:path*'
      }
    ]
  }
}
```

### Caching Strategy
```python
# backend/app/core/cache.py
import redis
import json

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

def cache_strategy_result(strategy_id: str, result: dict, ttl: int = 3600):
    key = f"strategy:{strategy_id}:result"
    redis_client.setex(key, ttl, json.dumps(result))

def get_cached_strategy_result(strategy_id: str):
    key = f"strategy:{strategy_id}:result"
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None
```

## 9. Security Hardening

### Environment Security
```bash
# Generate secure keys
openssl rand -hex 32  # For ENCRYPTION_KEY
openssl rand -base64 32  # For JWT_SECRET

# File permissions
chmod 600 .env
chmod 700 scripts/
```

### Network Security
```yaml
# docker-compose.secure.yml
services:
  backend:
    networks:
      - backend_network
    security_opt:
      - no-new-privileges:true
    
networks:
  backend_network:
    driver: bridge
    internal: true
```

## 10. Scaling Considerations

### Horizontal Scaling
- Use load balancers for multiple backend instances
- Distribute bot runners across multiple servers
- Implement queue-based bot execution

### Database Scaling
- Use Supabase read replicas for read-heavy workloads
- Implement connection pooling
- Consider database sharding for large datasets

## 11. Rollback Strategy

### Application Rollback
```bash
# Docker rollback
docker-compose down
git checkout <previous-commit>
docker-compose up -d

# Render rollback
# Use the dashboard to rollback to previous deployment
```

### Database Rollback
```bash
# Create backup before migration
pg_dump $DATABASE_URL > backup_before_migration.sql

# If needed, restore backup
psql $DATABASE_URL < backup_before_migration.sql
```

## 12. Disaster Recovery

### Recovery Plan
1. **Database Recovery**: Use Supabase automatic backups
2. **Application Recovery**: Redeploy from Git repository
3. **Configuration Recovery**: Store environment variables securely
4. **DNS Recovery**: Update DNS to point to backup infrastructure

### Testing Recovery
```bash
# Regular disaster recovery tests
./scripts/test-disaster-recovery.sh
```

## 13. Cost Optimization

### Resource Allocation
- Use appropriate instance sizes
- Implement auto-scaling
- Monitor resource usage
- Optimize database queries

### Cost Monitoring
```bash
# Set up cost alerts
# Render: Configure billing alerts
# AWS: Set up CloudWatch billing alarms
# GCP: Configure billing budgets
```

## Support and Maintenance

### Regular Tasks
- [ ] Monitor application health
- [ ] Review error logs
- [ ] Update dependencies
- [ ] Security patches
- [ ] Performance monitoring
- [ ] Backup verification

### Emergency Contacts
- Technical Support: support@nusanexus.com
- System Administrator: admin@nusanexus.com
- Emergency Hotline: +62-xxx-xxx-xxxx

For additional deployment assistance, refer to the [Environment Setup Guide](environment-setup.md) or contact the development team.

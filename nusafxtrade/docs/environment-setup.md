# Environment Setup Guide - NusaNexus NoFOMO

This guide will walk you through setting up the complete development and production environment for NusaNexus NoFOMO.

## Prerequisites

### System Requirements
- **Node.js**: v18+ (for frontend)
- **Python**: 3.11+ (for backend and AI engine)
- **Docker**: 20.10+ (for containerized deployment)
- **Git**: Latest version

### External Services
- **Supabase Account**: Database, Auth, and Realtime
- **Tripay Account**: Payment processing (Indonesia)
- **OpenRouter Account**: AI/LLM access
- **Exchange APIs**: Binance and/or Bybit for trading

## 1. Supabase Setup

### Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project
3. Note down your project URL and anon key

### Configure Database

#### Option A: Using the Setup Script (Recommended)
```bash
cd nusafxtrade/backend
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"

# Run the setup script
python scripts/setup_database.py
```

#### Option B: Manual SQL Execution
1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Execute the migration files in order:
   - `001_initial_schema.sql`
   - `002_indexes_and_triggers.sql`
   - `003_sample_data.sql` (for development only)

### Enable Authentication
1. Go to Authentication > Settings
2. Enable email authentication
3. Configure your site URL for OAuth redirects

### Setup Row Level Security
The migration files will automatically enable RLS on all user tables.

## 2. Environment Variables

### Backend Configuration
Create `nusafxtrade/backend/.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database Configuration
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Exchange API Keys
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-api-secret
BYBIT_API_KEY=your-bybit-api-key
BYBIT_API_SECRET=your-bybit-api-secret

# AI Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
AI_MODEL=anthropic/claude-3-sonnet

# Tripay Configuration
TRIPAY_MERCHANT_CODE=your-merchant-code
TRIPAY_API_KEY=your-tripay-api-key
TRIPAY_SANDBOX=true

# Security
ENCRYPTION_KEY=your-32-character-encryption-key
JWT_SECRET=your-jwt-secret-key

# Application
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO
```

### Frontend Configuration
Create `nusafxtrade/frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_APP_NAME=NusaNexus NoFOMO
```

### AI Engine Configuration
Create `nusafxtrade/ai_engine/.env`:

```env
OPENROUTER_API_KEY=your-openrouter-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 3. Installation

### Clone Repository
```bash
git clone <repository-url>
cd nusafxtrade
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### AI Engine Setup
```bash
cd ai_engine
pip install -r requirements.txt
```

### Bot Runner Setup
```bash
cd bot-runner
pip install -r requirements.txt
```

## 4. Development Services

### Start Redis (for job queue)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

### Install Freqtrade (for bot runner)
```bash
# For bot runner
pip install freqtrade[talib]
```

## 5. Database Initialization

### With Sample Data (Development)
```bash
cd backend
python scripts/setup_database.py
```

### Production Setup
```bash
cd backend
# Only run the first two migrations (no sample data)
# Execute 001_initial_schema.sql and 002_indexes_and_triggers.sql manually
```

## 6. Testing the Setup

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### API Health Check
```bash
curl http://localhost:8000/health
```

## 7. Docker Development

### Using Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services
```bash
# Backend API
cd backend
docker build -t nusanexus-api .
docker run -p 8000:8000 --env-file .env nusanexus-api

# Frontend
cd frontend
docker build -t nusanexus-frontend .
docker run -p 3000:3000 --env-file .env.local nusanexus-frontend

# AI Engine
cd ai_engine
docker build -t nusanexus-ai .
docker run -p 8001:8000 --env-file .env nusanexus-ai
```

## 8. Production Deployment

### Environment Preparation
```bash
# Set production environment
export APP_ENV=production
export APP_DEBUG=false
```

### Build Frontend
```bash
cd frontend
npm run build
npm start
```

### Deploy Backend
```bash
cd backend
# Deploy to your preferred platform (Render, Heroku, etc.)
# Ensure all environment variables are set
```

### Database Migration
```bash
# Apply migrations in production
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_indexes_and_triggers.sql
```

## 9. Security Checklist

### Development
- [ ] All API keys are stored in environment variables
- [ ] RLS policies are enabled on all user tables
- [ ] Database access is restricted to application users
- [ ] Exchange API keys are encrypted in database

### Production
- [ ] Strong encryption keys are generated
- [ ] HTTPS is enforced on all endpoints
- [ ] Database backups are automated
- [ ] Log monitoring is implemented
- [ ] Rate limiting is configured

## 10. Monitoring and Maintenance

### Health Checks
- [ ] Database connectivity
- [ ] Redis connection
- [ ] Exchange API status
- [ ] AI service availability

### Logging
- [ ] Application logs are centralized
- [ ] Error monitoring is configured
- [ ] Performance metrics are tracked

### Backup Strategy
- [ ] Database backups are automated
- [ ] Backup restoration is tested
- [ ] Offsite backup storage is configured

## 11. Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping
```

#### Supabase Auth Issues
```bash
# Verify Supabase configuration
curl -H "apikey: $SUPABASE_ANON_KEY" \
     -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/"
```

#### Exchange API Issues
```bash
# Test Binance connection
curl "https://api.binance.com/api/v3/ping" \
     -H "X-MBX-APIKEY: $BINANCE_API_KEY"
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export APP_DEBUG=true
```

## 12. Performance Optimization

### Database
- Monitor slow queries in Supabase dashboard
- Add indexes for frequently accessed data
- Use connection pooling for high traffic

### Caching
- Implement Redis caching for frequently accessed data
- Use Supabase realtime for live updates
- Cache strategy results for 24 hours

### Monitoring
- Set up uptime monitoring
- Configure performance alerts
- Monitor API rate limits

## 13. Scaling Considerations

### Database
- Use read replicas for read-heavy workloads
- Implement connection pooling
- Consider database partitioning for large datasets

### Application
- Use horizontal scaling with load balancers
- Implement caching strategies
- Use CDN for static assets

### Bot Runner
- Distribute bot execution across multiple instances
- Use queue systems for job distribution
- Monitor resource usage and scale accordingly

## Support

For additional help:
1. Check the [Troubleshooting Guide](docs/troubleshooting.md)
2. Review the [API Documentation](docs/api.md)
3. Contact support at support@nusanexus.com

## Next Steps

After setting up the environment:
1. [Database Schema Overview](database.md)
2. [API Documentation](api.md)
3. [Deployment Guide](deployment.md)
4. [Development Guide](development.md)

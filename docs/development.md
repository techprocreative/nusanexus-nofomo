# Development Guide - NusaNexus NoFOMO

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ and Python 3.9+
- Supabase account
- Redis Cloud account
- OpenRouter API account for AI features

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd nusafxtrade

# Copy environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Configure your environment variables
# Add your API keys and credentials
```

### 2. Development with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Development without Docker

#### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

#### Bot Runner
```bash
cd bot-runner
pip install -r requirements.txt
python bot_runner.py
```

## Project Structure

```
nusafxtrade/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   └── core/           # Core configuration
│   ├── main.py             # Application entry point
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # Next.js application
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile          # Frontend container
├── bot-runner/             # Freqtrade bot runner
│   ├── bot_runner.py       # Bot runner implementation
│   ├── requirements.txt    # Bot runner dependencies
│   └── Dockerfile          # Bot runner container
├── ai_engine/              # AI strategy generator
│   ├── strategy_generator.py # AI strategy generation
│   ├── requirements.txt    # AI engine dependencies
│   └── Dockerfile          # AI engine container
├── shared/                 # Shared utilities and types
│   └── types.py            # TypeScript/Python types
├── docs/                   # Documentation
│   ├── database.md         # Database schema
│   └── development.md      # This file
├── scripts/                # Deployment scripts
│   └── deploy.sh           # Production deployment
├── docker-compose.yml      # Multi-service orchestration
├── .env.example            # Environment template
└── README.md               # Project overview
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

### Bot Management
- `GET /api/v1/bots` - Get all bots
- `POST /api/v1/bots` - Create new bot
- `GET /api/v1/bots/{id}` - Get bot details
- `PUT /api/v1/bots/{id}` - Update bot
- `DELETE /api/v1/bots/{id}` - Delete bot
- `POST /api/v1/bots/{id}/start` - Start bot
- `POST /api/v1/bots/{id}/stop` - Stop bot
- `GET /api/v1/bots/{id}/status` - Get bot status

### Strategy Management
- `GET /api/v1/strategies` - Get all strategies
- `POST /api/v1/strategies` - Create new strategy
- `GET /api/v1/strategies/{id}` - Get strategy details
- `PUT /api/v1/strategies/{id}` - Update strategy
- `DELETE /api/v1/strategies/{id}` - Delete strategy
- `POST /api/v1/strategies/upload` - Upload strategy file

### Trade Management
- `GET /api/v1/trades` - Get trades
- `GET /api/v1/trades/stats` - Get trade statistics
- `GET /api/v1/trades/{id}` - Get trade details
- `GET /api/v1/trades/performance/daily` - Daily performance
- `GET /api/v1/trades/performance/monthly` - Monthly performance

### AI Features
- `POST /api/v1/ai/generate-strategy` - Generate strategy with AI
- `POST /api/v1/ai/optimize-strategy` - Optimize strategy parameters
- `GET /api/v1/ai/supervisor/{bot_id}` - Get AI analysis
- `POST /api/v1/ai/supervisor/analyze` - Run AI analysis
- `GET /api/v1/ai/market-analysis` - Get market analysis
- `POST /api/v1/ai/signal-analysis` - Analyze trading signal

## Database Schema

See [database.md](database.md) for complete database schema documentation.

## Testing

### Backend Testing
```bash
cd backend
pytest
```

### Frontend Testing
```bash
cd frontend
npm test
```

## Deployment

### Development Deployment
```bash
./scripts/deploy.sh
```

### Production Deployment
1. Set up Supabase production database
2. Configure environment variables
3. Set up Redis Cloud
4. Deploy to Render or similar platform
5. Configure domain and SSL

## Key Features

### 1. Multi-Tenant Architecture
- Row Level Security (RLS) in Supabase
- User data isolation
- Multi-tenant billing

### 2. AI-Powered Strategy Generation
- LLM integration with OpenRouter
- Freqtrade strategy templates
- Parameter optimization
- Market analysis

### 3. Bot Runner
- Isolated bot execution
- Redis queue management
- Real-time status monitoring
- Error handling and recovery

### 4. Real-time Features
- WebSocket connections
- Live trade updates
- Bot status monitoring
- Performance dashboards

### 5. Security
- Encrypted API key storage
- JWT authentication
- Input validation
- Rate limiting

## Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Submit pull request

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check Supabase credentials
   - Verify RLS policies
   - Test connection

2. **Bot won't start**
   - Check exchange credentials
   - Verify strategy code
   - Check Redis queue

3. **AI generation failed**
   - Verify OpenRouter API key
   - Check model availability
   - Review prompt format

### Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f bot-runner
```

## Support

- Documentation: [docs/](../docs/)
- API Reference: http://localhost:8000/api/docs
- GitHub Issues: [repository-url]/issues

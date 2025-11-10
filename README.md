# 🚀 NusaNexus NoFOMO — AI-Powered Crypto Trading Bot SaaS

**Platform Trading Bot AI berbasis Freqtrade**  
**Exchange Support:** Binance, Bybit  
**Database:** Supabase  
**Deployment:** Render  
**Billing:** Tripay (Hybrid SaaS)  
**AI Layer:** LLM-based (OpenRouter / Together AI)

## 🏗️ Architecture Overview

```mermaid
graph TD
  U[User Dashboard (Next.js)] -->|Auth| A[Supabase Auth]
  U -->|API Calls| B[FastAPI Backend]
  B -->|Read/Write| C[Supabase DB]
  B -->|Queue Job| D[Redis Queue]
  D -->|Exec Task| E[Bot Runner (Freqtrade Engine)]
  E -->|Fetch Data| F[Exchange (Binance/Bybit)]
  E -->|Log Trades| C
  B -->|Invoke| G[AI Engine (LLM)]
  G -->|Generate| H[Strategy Templates]
```

## 🧱 Components

### Frontend (Next.js + Tailwind + Shadcn UI)
- User dashboard, bot control panel, live trade feed (Supabase Realtime)

### Backend (FastAPI)
- REST & WebSocket API
- Worker scheduler dan orchestrator bot

### Bot Runner (Freqtrade Engine)
- Custom wrapper script untuk menjalankan strategy file per user

### Database (Supabase PostgreSQL)
- Multi-tenant schema + RLS untuk isolasi data user

### Queue System (Redis)
- Menjalankan bot task async dan backtest job

### AI Engine
- Model LLM (Sonnet / GPT / Claude / Llama via OpenRouter)
- Digunakan untuk strategi, optimasi, dan signal reasoning

### Billing (Tripay)
- Untuk tier SaaS: free / pro / enterprise

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ and Python 3.9+
- Supabase account
- Redis Cloud account

### Environment Setup
1. Copy environment templates:
   ```bash
   cp .env.example .env.local
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. Configure your environment variables in the `.env` files

### Development

```bash
# Start all services with Docker
docker-compose up -d

# Or start services individually
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

## 📁 Project Structure

```
nusafxtrade/
├── backend/                 # FastAPI application
├── frontend/               # Next.js application  
├── bot-runner/             # Freqtrade bot runner
├── ai_engine/              # AI strategy generator
├── shared/                 # Shared utilities and types
├── docs/                   # Documentation
├── docker/                 # Docker configurations
├── scripts/                # Deployment and setup scripts
└── README.md
```

## 🛠️ Development Roadmap

| Phase | Feature | Status |
|-------|----------|--------|
| 1 | Auth + Dashboard | 🟢 |
| 2 | Connect Exchange + Bot Config | 🟢 |
| 3 | AI Strategy Generator | 🟡 |
| 4 | Bot Runner (Freqtrade) | 🟡 |
| 5 | Monitoring Dashboard | 🟢 |
| 6 | Tripay Billing | 🔜 |
| 7 | AI Supervisor | 🔜 |
| 8 | White-label option | 🔜 |

## 📚 Documentation

See the `docs/` directory for detailed documentation:
- [API Documentation](docs/api.md)
- [Database Schema](docs/database.md)
- [Deployment Guide](docs/deployment.md)
- [Development Guide](docs/development.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, email support@NusaNexus.com or join our Discord community.

---

**Built with ❤️ using FastAPI, Next.js, Freqtrade, and Supabase**

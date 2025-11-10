# Environment Variables Reference

Complete guide for all environment variables used in NusaNexus NoFOMO platform.

---

## 🔧 Backend Environment Variables

### Core Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | "NusaNexus NoFOMO API" | Application name for logging |
| `APP_VERSION` | No | "0.1.0" | API version |
| `DEBUG` | No | `false` | Enable debug mode (NEVER true in production) |
| `SECRET_KEY` | **YES** | - | JWT signing key (min 32 chars, use: `openssl rand -base64 32`) |
| `API_V1_STR` | No | "/api/v1" | API version prefix |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 30 | JWT token expiration time |

### CORS & Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALLOWED_ORIGINS` | **YES** | "http://localhost:3000" | Comma-separated list of allowed CORS origins |
| `ALLOWED_HOSTS` | **YES** | "localhost,*.onrender.com" | Comma-separated list of trusted hosts |

**Example:**
```bash
ALLOWED_ORIGINS="https://nusafx-frontend.onrender.com,https://yourdomain.com"
ALLOWED_HOSTS="*.onrender.com,*.yourdomain.com,localhost"
```

### Database (Supabase)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | **YES** | - | Supabase project URL from dashboard |
| `SUPABASE_KEY` | **YES** | - | Supabase anon/public key (safe to expose) |
| `SUPABASE_SERVICE_ROLE_KEY` | **YES** | - | Service role key (KEEP SECURE - backend only) |

**Where to find:**
- Supabase Dashboard → Settings → API
- URL: `https://xxxxx.supabase.co`
- Keys are in the "Project API keys" section

### Redis (Job Queue)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | **YES** | "redis://localhost:6379" | Redis connection string |
| `REDIS_HOST` | No | "localhost" | Redis host (alternative to URL) |
| `REDIS_PORT` | No | "6379" | Redis port |
| `REDIS_PASSWORD` | No | - | Redis password if auth enabled |

**Render Auto-configured:**
When using Render Redis service, the `REDIS_URL` is automatically set via service linking.

### AI & OpenRouter

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | **YES** | - | OpenRouter API key for AI features |
| `OPENROUTER_BASE_URL` | No | "https://openrouter.ai/api/v1" | OpenRouter API base URL |
| `OPENROUTER_MODEL` | No | "anthropic/claude-3-sonnet" | Default AI model to use |

**Get API key:**
- Sign up at https://openrouter.ai
- Dashboard → Keys → Create new key
- Add credits to account

### Exchange APIs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BINANCE_API_URL` | No | "https://api.binance.com" | Binance API endpoint |
| `BYBIT_API_URL` | No | "https://api.bybit.com" | Bybit API endpoint |

**Note:** User exchange API keys are encrypted and stored in database, NOT in env vars.

### Billing (Tripay)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRIPAY_API_KEY` | No | - | Tripay API key for payment processing |
| `TRIPAY_MERCHANT_CODE` | No | - | Tripay merchant code |
| `TRIPAY_PRIVATE_KEY` | No | - | Tripay private key for webhooks |

**Optional for MVP** - Can be configured later when enabling billing.

### Monitoring & Logging

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | No | - | Sentry DSN for error tracking |
| `LOG_LEVEL` | No | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## 🎨 Frontend Environment Variables

### Supabase Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | **YES** | - | Supabase project URL (same as backend) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **YES** | - | Supabase anon key (safe for frontend) |

**Note:** Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

### API Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | **YES** | - | Backend API base URL |
| `NEXT_PUBLIC_WS_URL` | No | - | WebSocket URL for real-time features |

**Examples:**
```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Production
NEXT_PUBLIC_API_URL=https://nusafx-backend.onrender.com/api/v1
```

### Next.js Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | "development" | Node environment (production/development) |
| `NEXTAUTH_URL` | No | - | NextAuth base URL (if using NextAuth) |
| `NEXTAUTH_SECRET` | No | - | NextAuth secret key (if using NextAuth) |

---

## 👷 Worker Services Environment Variables

### AI Engine Worker

```bash
# Required
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-sonnet
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
REDIS_URL=redis://...

# Optional
LOG_LEVEL=INFO
```

### Bot Runner Worker

```bash
# Required
REDIS_URL=redis://...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Exchange URLs (can use defaults)
BINANCE_API_URL=https://api.binance.com
BYBIT_API_URL=https://api.bybit.com

# Optional
LOG_LEVEL=INFO
```

---

## 🔐 Security Best Practices

### ✅ DO:

1. **Use strong SECRET_KEY** - Generate with `openssl rand -base64 32`
2. **Keep service role keys secure** - Never expose in frontend
3. **Use .gitignore** - Never commit `.env` files
4. **Restrict CORS origins** - Only allow your domains
5. **Use environment-specific values** - Different keys for dev/prod
6. **Rotate secrets regularly** - Change keys periodically

### ❌ DON'T:

1. **Don't hardcode secrets** - Always use environment variables
2. **Don't expose service role keys** - Backend only
3. **Don't use DEBUG=true** - Never in production
4. **Don't commit .env files** - Already in .gitignore
5. **Don't use weak passwords** - Minimum 32 characters for SECRET_KEY
6. **Don't allow all origins** - Restrict CORS properly

---

## 📋 Environment Setup Checklist

### Local Development

- [ ] Copy `.env.example` to `.env` in backend folder
- [ ] Copy `.env.example` to `.env.local` in frontend folder
- [ ] Fill in Supabase credentials
- [ ] Fill in OpenRouter API key (if testing AI features)
- [ ] Set backend URL to `http://localhost:8000/api/v1`
- [ ] Start backend: `cd backend && uvicorn main:app --reload`
- [ ] Start frontend: `cd frontend && npm run dev`

### Render Production

- [ ] Setup Supabase project and apply schema
- [ ] Get OpenRouter API key and add credits
- [ ] Generate SECRET_KEY with OpenSSL
- [ ] Configure backend service environment variables
- [ ] Configure frontend service environment variables
- [ ] Update CORS origins with deployed frontend URL
- [ ] Test deployment and verify all features work

---

## 🔍 Troubleshooting

### "Missing environment variable" Error

**Solution:** Check if all required variables are set in Render dashboard or local `.env` file.

### CORS Error in Browser

**Solution:** 
1. Check `ALLOWED_ORIGINS` includes your frontend URL
2. Make sure it's comma-separated with NO spaces
3. Redeploy backend after changing

### "Invalid JWT" or Auth Errors

**Solution:**
1. Verify `SUPABASE_URL` and keys are correct
2. Check `SECRET_KEY` is same across all backend instances
3. Ensure database RLS policies are enabled

### API Connection Failed

**Solution:**
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check backend service is running
3. Test API endpoint directly: `curl https://backend.onrender.com/health`

---

## 📝 Quick Reference

### Generate SECRET_KEY
```bash
openssl rand -base64 32
```

### Format ALLOWED_ORIGINS
```bash
# Single origin
ALLOWED_ORIGINS="https://app.example.com"

# Multiple origins (comma-separated, NO spaces)
ALLOWED_ORIGINS="https://app.example.com,https://www.example.com,http://localhost:3000"
```

### Test Backend Health
```bash
curl https://your-backend.onrender.com/health
```

### Test API Endpoint
```bash
curl -X GET https://your-backend.onrender.com/api/v1/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

**Last Updated:** 2025-01-10  
**Version:** 1.0.0 (MVP)

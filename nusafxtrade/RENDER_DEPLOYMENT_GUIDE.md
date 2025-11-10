# NusaNexus NoFOMO - Render Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites

1. **Supabase Account** (FREE)
   - Sign up at https://supabase.com
   - Create a new project
   - Note down your project URL and keys

2. **OpenRouter Account** (API Credits)
   - Sign up at https://openrouter.ai
   - Add credits to your account
   - Generate API key

3. **Render Account** (FREE tier available)
   - Sign up at https://render.com
   - Connect your GitHub account

4. **GitHub Repository**
   - Push this code to a GitHub repository
   - Make sure `.env` files are NOT committed (already in `.gitignore`)

---

## 📋 Step-by-Step Deployment

### Step 1: Setup Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run the database schema:
   - Copy contents from `deployment/database/schema.sql`
   - Execute the SQL script
   - Verify tables are created in **Table Editor**

4. Get your credentials from **Settings > API**:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon/Public Key: `eyJhbGc...` (safe to expose)
   - Service Role Key: `eyJhbGc...` (keep secure!)

### Step 2: Get OpenRouter API Key

1. Go to https://openrouter.ai/keys
2. Create a new API key
3. Add credits to your account (minimum $5 recommended)
4. Copy the API key (starts with `sk-or-...`)

### Step 3: Generate Secret Key

Run this command in your terminal:

```bash
openssl rand -base64 32
```

Copy the output - this will be your `SECRET_KEY`.

### Step 4: Deploy to Render

#### Option A: Blueprint Deployment (Recommended)

1. Go to https://render.com/dashboard
2. Click **New** → **Blueprint**
3. Connect your GitHub repository
4. Select the repository with this code
5. Render will detect `render.yaml` automatically
6. Click **Apply**

#### Option B: Manual Service Creation

**Backend Service:**
1. New → Web Service
2. Connect repository
3. Name: `nusafx-backend`
4. Runtime: Python 3
5. Build Command: `cd backend && pip install -r requirements.txt`
6. Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

**Frontend Service:**
1. New → Web Service
2. Connect repository
3. Name: `nusafx-frontend`
4. Runtime: Node
5. Build Command: `cd frontend && npm ci && npm run build`
6. Start Command: `cd frontend && npm start`

**Redis Service:**
1. New → Redis
2. Name: `nusafx-redis`
3. Plan: Free (Starter)

**Workers (Optional for MVP):**
- Can be added later for bot execution and AI features

### Step 5: Configure Environment Variables

For **Backend Service** (nusafx-backend), add these environment variables:

```bash
# Required
SECRET_KEY=<your-generated-secret-key>
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>
OPENROUTER_API_KEY=<your-openrouter-api-key>

# CORS Configuration (Update after frontend deployed)
ALLOWED_ORIGINS=https://nusafx-frontend.onrender.com,http://localhost:3000
ALLOWED_HOSTS=*.onrender.com,localhost

# Optional
DEBUG=false
LOG_LEVEL=INFO
SENTRY_DSN=<optional-sentry-dsn>
```

For **Frontend Service** (nusafx-frontend), add these:

```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
NEXT_PUBLIC_API_URL=https://nusafx-backend.onrender.com/api/v1

# Production
NODE_ENV=production
```

For **Worker Services** (if deployed), add these:

```bash
# AI Engine Worker
OPENROUTER_API_KEY=<your-openrouter-api-key>
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>

# Bot Runner Worker
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>
```

### Step 6: Update CORS After Deployment

1. After both services are deployed, note the URLs:
   - Backend: `https://nusafx-backend.onrender.com`
   - Frontend: `https://nusafx-frontend.onrender.com`

2. Update backend environment variable:
   ```bash
   ALLOWED_ORIGINS=https://nusafx-frontend.onrender.com
   ```

3. Redeploy backend service

### Step 7: Test Deployment

1. Visit your frontend URL: `https://nusafx-frontend.onrender.com`
2. Try to register a new account
3. Check if login works
4. Verify dashboard loads
5. Test creating a bot (may not execute without workers)

---

## 🔧 Troubleshooting

### Backend Service Won't Start

**Check logs for:**
- Missing environment variables → Add all required vars
- Database connection error → Verify Supabase credentials
- Port binding error → Render handles this automatically

### Frontend Shows "API Error"

**Solutions:**
1. Check `NEXT_PUBLIC_API_URL` is correct
2. Verify backend service is running
3. Check CORS settings in backend
4. Look at browser console for specific error

### Authentication Not Working

**Check:**
1. Supabase URL and keys are correct
2. Database schema is applied
3. Users table has RLS policies enabled
4. JWT secret is configured in Supabase

### Build Failures

**Frontend:**
- Clear cache: Settings → Clear build cache
- Check Node version (use 18.x)
- Verify all dependencies install correctly

**Backend:**
- Check Python version (3.11)
- Verify requirements.txt has no conflicts
- Check for missing system dependencies

---

## 💰 Cost Estimate (Monthly)

### Render (Free Tier)
- 1x Web Service (Backend): **FREE** (750hrs/month)
- 1x Web Service (Frontend): **FREE** (750hrs/month)
- 1x Redis: **FREE** (25MB)
- **Total: $0/month** (with limitations)

### Render (Paid - Recommended for Production)
- 2x Starter Web Services: **$14/month** ($7 each)
- 1x Redis Starter: **$10/month**
- **Total: ~$24/month**

### Other Services
- Supabase: **FREE** (up to 500MB database, 2GB bandwidth)
- OpenRouter: **Pay-as-you-go** (~$0.01-0.10 per request)

**MVP Total: $0-24/month** (excluding AI API costs)

---

## 🔒 Security Checklist

- [ ] All `.env` files are in `.gitignore`
- [ ] No secrets committed to GitHub
- [ ] `SECRET_KEY` is random and secure (32+ chars)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is kept secure (backend only)
- [ ] CORS origins are restricted to your domains
- [ ] DEBUG mode is `false` in production
- [ ] Database RLS policies are enabled
- [ ] Supabase service role key is NOT exposed to frontend

---

## 🎯 Post-Deployment Tasks

1. **Setup Custom Domain** (Optional)
   - Add custom domain in Render dashboard
   - Update DNS records
   - Update CORS and ALLOWED_ORIGINS

2. **Enable Monitoring** (Optional)
   - Add Sentry DSN for error tracking
   - Setup uptime monitoring
   - Configure log aggregation

3. **Deploy Workers** (When Ready)
   - Deploy AI Engine worker for strategy generation
   - Deploy Bot Runner worker for trade execution
   - Configure job queues with Redis

4. **Test Billing Integration**
   - Setup Tripay credentials
   - Test payment flow
   - Configure subscription plans

5. **Load Testing**
   - Test with multiple users
   - Monitor resource usage
   - Optimize as needed

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## 🆘 Support

If you encounter issues:

1. Check Render service logs (Dashboard → Service → Logs)
2. Check Supabase logs (Dashboard → Logs)
3. Review browser console errors
4. Verify all environment variables are set
5. Check this guide for common issues

---

**Last Updated:** 2025-01-10
**Version:** 1.0.0 (MVP)

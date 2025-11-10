# Pre-Deployment Checklist

Use this checklist to ensure your NusaNexus NoFOMO application is ready for production deployment.

---

## ✅ Code Quality & Configuration

### Configuration Files
- [x] `next.config.js` has `output: 'standalone'` for Docker deployment
- [x] `.gitignore` files created (root, backend, frontend)
- [x] `.env.example` files updated with all variables
- [x] `render.yaml` configured with proper services
- [x] CORS origins configurable via environment variables
- [x] Trusted hosts configurable via environment variables

### Security
- [ ] No `.env` files committed to git
- [ ] No hardcoded secrets in code
- [ ] `DEBUG=false` in production environment variables
- [ ] Strong `SECRET_KEY` generated (32+ characters)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` kept secure (backend only)
- [ ] CORS origins restricted to your domains only

### Code Review
- [ ] No `console.log` statements with sensitive data
- [ ] No commented-out code blocks
- [ ] All TODO comments addressed or documented
- [ ] No mock data in production code paths
- [ ] Error handling implemented for all API calls

---

## 🗄️ Database Setup

### Supabase Configuration
- [ ] Supabase project created
- [ ] Database schema applied (`deployment/database/schema.sql`)
- [ ] Tables verified in Supabase Table Editor
- [ ] Row Level Security (RLS) policies enabled
- [ ] Seed data for plans inserted
- [ ] Project URL and keys copied

### Database Verification
- [ ] Users table exists with RLS
- [ ] Bots table exists with RLS
- [ ] Trades table exists with RLS
- [ ] Strategies table exists with RLS
- [ ] Plans table has seed data
- [ ] Indexes created for performance
- [ ] Audit log table configured

---

## 🔑 API Keys & Secrets

### Required Keys
- [ ] OpenRouter API key obtained
- [ ] OpenRouter account has credits ($5+ recommended)
- [ ] Supabase anon key copied
- [ ] Supabase service role key copied (keep secure!)
- [ ] `SECRET_KEY` generated with `openssl rand -base64 32`

### Optional Keys (Can add later)
- [ ] Sentry DSN for error monitoring
- [ ] Tripay API credentials for billing
- [ ] Custom domain SSL certificates

---

## 🚀 Render Setup

### Account & Repository
- [ ] Render account created
- [ ] GitHub account connected to Render
- [ ] Code pushed to GitHub repository
- [ ] `.env` files NOT in repository (check `.gitignore`)

### Services Configuration
- [ ] Backend service plan selected (Free or Starter)
- [ ] Frontend service plan selected (Free or Starter)
- [ ] Redis service created (Free tier available)
- [ ] Service names decided (e.g., nusafx-backend, nusafx-frontend)

### Environment Variables Prepared
- [ ] Backend env vars documented and ready
- [ ] Frontend env vars documented and ready
- [ ] Worker env vars documented (if deploying workers)
- [ ] All placeholder values replaced with real credentials

---

## 📝 Documentation

### Guides Created
- [x] Render deployment guide (`RENDER_DEPLOYMENT_GUIDE.md`)
- [x] Environment variables reference (`ENV_VARIABLES_REFERENCE.md`)
- [x] Pre-deployment checklist (this file)
- [ ] User documentation (can add post-deployment)
- [ ] API documentation (can add post-deployment)

### Team Communication
- [ ] Deployment plan shared with team
- [ ] Credentials securely shared (use password manager)
- [ ] Rollback plan documented
- [ ] Monitoring strategy defined

---

## 🧪 Testing

### Local Testing
- [ ] Backend runs locally without errors
- [ ] Frontend runs locally without errors
- [ ] Database connection works
- [ ] Authentication flow works
- [ ] API endpoints respond correctly
- [ ] No console errors in browser

### Pre-Deploy Testing
- [ ] Build commands work: `cd backend && pip install -r requirements.txt`
- [ ] Build commands work: `cd frontend && npm ci && npm run build`
- [ ] Start commands work locally
- [ ] Environment variables load correctly
- [ ] Docker containers build (if using)

---

## 📊 Monitoring & Observability

### Setup (Optional but Recommended)
- [ ] Sentry account created for error tracking
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
- [ ] Log aggregation planned
- [ ] Performance monitoring strategy
- [ ] Alert channels defined (email, Slack, etc.)

---

## 💰 Cost Management

### Budget Planning
- [ ] Render plan costs understood
  - Free tier: $0/month (with limitations)
  - Starter: ~$24/month (2 web services + Redis)
- [ ] Supabase usage monitored (free tier: 500MB, 2GB bandwidth)
- [ ] OpenRouter credits budget allocated
- [ ] Cost alerts configured in services

### Usage Limits
- [ ] Render free tier limitations understood (750 hrs/month)
- [ ] Supabase free tier limits known
- [ ] OpenRouter rate limits checked
- [ ] Upgrade path planned if needed

---

## 🔄 Deployment Process

### Pre-Deployment
- [ ] All items above checked
- [ ] Backup plan documented
- [ ] Rollback procedure ready
- [ ] Team notified of deployment window
- [ ] Maintenance window scheduled (if needed)

### Deployment Steps
1. [ ] Push code to GitHub
2. [ ] Apply database schema to Supabase
3. [ ] Create Render services (or use Blueprint)
4. [ ] Configure all environment variables
5. [ ] Deploy backend service
6. [ ] Deploy frontend service
7. [ ] Update CORS origins with deployed URLs
8. [ ] Redeploy backend with updated CORS

### Post-Deployment
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test dashboard loads
- [ ] Test bot creation
- [ ] Check all API endpoints
- [ ] Verify database connections
- [ ] Monitor error logs
- [ ] Check service health endpoints

---

## ✅ Final Verification

### Functional Testing
- [ ] User can register new account
- [ ] User can login successfully
- [ ] Dashboard displays correctly
- [ ] Bots page loads with real data
- [ ] Trades page loads with real data
- [ ] Create bot form works
- [ ] Bot detail page accessible
- [ ] Navigation between pages works
- [ ] Mobile responsive design verified
- [ ] No console errors in production

### Performance
- [ ] Page load times acceptable (<3s)
- [ ] API response times good (<1s)
- [ ] No memory leaks observed
- [ ] Database queries optimized
- [ ] Images optimized
- [ ] Bundle size reasonable

### Security Verification
- [ ] HTTPS enabled on all services
- [ ] CORS working correctly
- [ ] Authentication required for protected routes
- [ ] No sensitive data in client-side code
- [ ] API keys not exposed in frontend
- [ ] SQL injection protection verified (via Supabase)

---

## 🎯 Launch Readiness

### MVP Launch Criteria (Minimum)
- [ ] User registration works
- [ ] User authentication works  
- [ ] Dashboard displays user stats
- [ ] Bot CRUD operations work
- [ ] Trading strategies can be selected
- [ ] Real-time data from database
- [ ] No critical bugs
- [ ] Basic error handling in place

### Nice-to-Have (Can add post-launch)
- [ ] AI strategy generation (requires OpenRouter credits)
- [ ] Bot execution workers deployed
- [ ] Payment integration active
- [ ] Email notifications configured
- [ ] Advanced analytics
- [ ] Admin dashboard

---

## 📅 Timeline

### Estimated Deployment Time
- Database setup: **10-15 minutes**
- Render configuration: **20-30 minutes**
- Environment variables: **10-15 minutes**
- Initial deployment: **15-20 minutes**
- Testing & verification: **15-20 minutes**
- **Total: 60-90 minutes** (first time)

### Maintenance Windows
- [ ] Initial deployment: [DATE/TIME]
- [ ] First health check: +1 hour after deploy
- [ ] 24-hour monitoring: [DATE/TIME]
- [ ] Week 1 review: [DATE/TIME]

---

## 🆘 Emergency Contacts

### Key Personnel
- **DevOps Lead**: [Name/Contact]
- **Backend Developer**: [Name/Contact]
- **Frontend Developer**: [Name/Contact]
- **Database Admin**: [Name/Contact]

### Service Support
- **Render Support**: support@render.com
- **Supabase Support**: support@supabase.com
- **OpenRouter Support**: [Check dashboard]

---

## 📈 Success Metrics

### Day 1 Goals
- [ ] All services running without errors
- [ ] At least 1 test user registered successfully
- [ ] All critical paths tested
- [ ] No P0/P1 bugs reported

### Week 1 Goals
- [ ] 95%+ uptime
- [ ] Average response time <1s
- [ ] Zero security incidents
- [ ] User feedback collected

---

**Ready to Deploy?** 

If all critical items are checked, you're ready to proceed with deployment! 🚀

Follow the [RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md) for step-by-step instructions.

---

**Last Updated:** 2025-01-10  
**Version:** 1.0.0 (MVP)

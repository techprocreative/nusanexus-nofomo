# 🚀 NusaNexus NoFOMO — AI-Powered Crypto Trading Bot SaaS
**Platform Trading Bot AI berbasis Freqtrade**  
**Exchange Support:** Binance, Bybit  
**Database:** Supabase  
**Deployment:** Render  
**Billing:** Tripay (Hybrid SaaS)  
**AI Layer:** LLM-based (OpenRouter / Together AI)

---

## 1. High-Level Architecture
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

### 🧱 Komponen:
- **Frontend (Next.js + Tailwind + Shadcn UI)**  
  - User dashboard, bot control panel, live trade feed (Supabase Realtime).  
- **Backend (FastAPI)**  
  - REST & WebSocket API.  
  - Worker scheduler dan orchestrator bot.  
- **Bot Runner (Freqtrade Engine)**  
  - Custom wrapper script untuk menjalankan strategy file per user.  
- **Database (Supabase PostgreSQL)**  
  - Multi-tenant schema + RLS untuk isolasi data user.  
- **Queue System (Redis)**  
  - Menjalankan bot task async dan backtest job.  
- **AI Engine**  
  - Model LLM (Sonnet / GPT / Claude / Llama via OpenRouter).  
  - Digunakan untuk strategi, optimasi, dan signal reasoning.  
- **Billing (Tripay)**  
  - Untuk tier SaaS: free / pro / enterprise.  

---

## 2. Multi-Tenant Design (Supabase)
### Struktur Tabel
| Table | Description |
|-------|--------------|
| users | data pengguna (autentikasi Supabase) |
| bots | bot milik user (exchange, pair, timeframe, strategy, status) |
| strategies | file strategi (custom & AI generated) |
| trades | hasil trading bot |
| logs | log eksekusi dan AI prompt |
| plans | paket langganan SaaS |
| invoices | transaksi pembayaran Tripay |

### Policy RLS Contoh
```sql
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Bots are isolated per user"
  ON bots
  FOR ALL
  USING (auth.uid() = user_id);
```

---

## 3. Bot Lifecycle Flow
1. User login via Supabase Auth.  
2. Connect API key exchange (disimpan terenkripsi di Supabase).  
3. User pilih strategi (atau generate via AI).  
4. User jalankan bot (paper/live).  
5. Bot Runner aktif → ambil parameter & strategi → jalankan Freqtrade engine → catat trade ke DB.  
6. Dashboard menampilkan realtime status bot (PnL, open position, trade log).  

---

## 4. Bot Runner Architecture
- Worker ringan, menggunakan Redis Queue (misalnya `RQ` atau `FastAPI BackgroundTasks`).  
- Setiap user bot dijalankan dalam subprocess terisolasi:
```python
subprocess.Popen([
  "freqtrade", "trade",
  "--config", f"configs/{user_id}_{bot_id}.json",
  "--strategy-path", f"strategies/{strategy_name}.py"
])
```
- Logging dikirim ke Supabase melalui REST endpoint.
- Maksimum 1 bot aktif per market per user (kontrol via DB).

---

## 5. AI Module Design
### (a) Strategy Generator
- Input: prompt user (mis. “Scalping BTC/USDT 5m dengan RSI dan EMA crossover”).
- Output: file `.py` strategy template sesuai format Freqtrade.

### (b) Parameter Optimizer
- Jalankan `freqtrade hyperopt` otomatis dan pilih parameter optimal.
- Simpan hasil hyperopt ke Supabase.

### (c) Supervisor Agent
- Monitor hasil trade per bot.  
- Jika loss streak > N, sarankan perubahan strategi atau auto-pause.  
- Bisa dijalankan sebagai background process dengan akses ke logs.

---

## 6. Security
- API key exchange terenkripsi AES-256 sebelum disimpan di Supabase.
- Token LLM & Tripay disimpan di environment Render.
- Tidak ada akses withdrawal dari platform.
- Sandbox strategy execution:
  - Jalankan bot di container dengan profil permission minimal.

---

## 7. UI & UX Features
- Modern, clean UI (Next.js + Tailwind + Shadcn).
- Realtime update menggunakan Supabase Realtime.
- Pages utama:
  - Dashboard (summary & bot status)
  - My Bots
  - AI Strategy Builder
  - Logs & Performance
  - Settings (API keys, Plan, Profile)

---

## 8. Deployment on Render
| Service | Type | Plan | Purpose |
|----------|------|------|----------|
| Web | Web Service (Next.js build) | Free | Frontend |
| API | Web Service (FastAPI) | Free | Backend |
| Worker | Background Service | Free | Bot runner queue |
| Redis | Data Store | Free | Job queue |
| Supabase | External | Free | DB + Auth + Realtime |

---

## 9. Development Roadmap (MVP)
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

---

## 10. Future Expansion
- Caching OHLCV ke ClickHouse/Timescale.
- Integrasi Telegram alert.
- Auto ML optimization untuk strategi.
- Multi-exchange portfolio.
- Marketplace strategi.

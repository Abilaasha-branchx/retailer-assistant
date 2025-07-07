# Retail Assistant Chat Backend

## Setup

1. Copy your Supabase `DATABASE_URL` into the `.env` file (already present).
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the server:
   ```bash
   npm start
   ```
4. On chat initialization, call `GET /chat/init` to run `daily_summary.sql` and return the summary.

---

This backend is ready to be extended for chat and proactive agent logic.

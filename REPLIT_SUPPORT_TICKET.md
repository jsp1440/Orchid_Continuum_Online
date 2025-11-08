# Replit Support Ticket - Flask Server Won't Start

## Issue Summary
Flask server crashes during startup and won't respond to requests. Server successfully connects to PostgreSQL database but crashes while loading application routes.

## Environment
- **Platform**: Replit
- **Language**: Python 3.11
- **Framework**: Flask with SQLAlchemy
- **Database**: PostgreSQL (Neon)
- **Project**: The Orchid Continuum (large-scale botanical research platform)

## Symptoms
1. Server starts loading (`python main.py` or `gunicorn`)
2. Successfully connects to database
3. Begins loading blueprints/routes
4. Process dies silently during route registration (no error messages)
5. Health endpoint at `/health` never responds
6. No Python process remains running after ~30 seconds

## What We've Tried
1. ✅ Fixed import errors in routes
2. ✅ Killed all existing Python processes before restart
3. ✅ Tried both `python main.py` and `gunicorn` 
4. ✅ Created minimal standalone servers (also fail)
5. ✅ Checked logs - no errors, just stops loading
6. ✅ Verified database connection works
7. ✅ Tested individual AI components (all work)

## Last Known Log Output
```
INFO:root:📊 Connecting to database: postgresql+pg8000://...
INFO:root:Database tables created successfully
INFO:root:Widget manifest endpoints registered
INFO:root:✅ Taxonomy Widget Suite API registered
INFO:root:✅ Replit Auth initialized successfully
INFO:judging_standards:Initializing judging standards...
[PROCESS DIES HERE - NO ERROR MESSAGE]
```

## Suspected Cause
Application has ~400+ routes across many blueprints. Server may be:
- Running out of memory during initialization
- Timing out during heavy route loading
- Hitting some resource limit during startup

## What We Need
1. **Diagnostic Help**: Why is the process dying silently?
2. **Resource Limits**: Are we hitting memory/CPU limits during startup?
3. **Logs Access**: Can we get system-level logs showing why process terminated?
4. **Solution**: How to successfully start a large Flask app on Replit?

## Project Context
This is a production botanical research platform with:
- Multi-AI integration (Google Gemini, Together AI)
- 50+ route blueprints
- Real-time widgets and monitoring dashboards
- PostgreSQL database with 10,534+ orchid records
- Successfully runs on Render.com but won't start on Replit

## Urgency
**HIGH** - Unable to test new features, blocking development progress

## How to Contact Me
[Add your contact information here]

---

## For Replit Team - Technical Details

**App Structure:**
- Main file: `main.py` → imports `app.py`
- `app.py`: Registers 50+ blueprints
- Database: PostgreSQL via `DATABASE_URL` env variable
- Total project files: 300+

**Recent Changes:**
- Added 3 new widget blueprints (properly registered)
- Fixed import error in `routes_botanist.py`
- All code compiles without errors

**Question for Support:**
Is there a recommended way to structure large Flask applications on Replit to avoid startup crashes? Should we be using a different workflow configuration?

# ⚠️ Server Starting Issue - Simple Solution

## The Easy Way (RECOMMENDED)

**Just click the green "Run" button at the top of Replit!**

That will:
1. Start the server automatically using the `.replit` config
2. Show you the server logs in real-time
3. Give you a clickable URL when ready

---

## Why Manual Start is Complicated

The app loads 50+ routes and systems on startup:
- Widget directory
- Taxonomy routes  
- GBIF integration
- AI breeder assistant
- Geographic mapping
- Admin systems
- And many more...

This takes 20-30 seconds to fully initialize!

---

## What's Your URL?

Once the server starts (via Run button):

**Main URL:**
```
https://workspace.fcospresident.repl.co
```

**Key pages:**
- `/widgets` - Widget directory  
- `/manifest` - Widget manifest dashboard
- `/health` - Health check
- `/taxonomy/browser` - Taxonomy browser

---

## If Run Button Doesn't Work

Try this in the Shell tab:

```bash
pkill -f gunicorn; pkill -f python
bash ./init.sh
```

Wait 30 seconds for full initialization!

---

## Start Enriching (Works Independently)

While waiting for the server, you can start collecting images:

```bash
bash validation/collect_images.sh
```

This runs for 5 minutes and collects FREE GBIF images (no server needed!).

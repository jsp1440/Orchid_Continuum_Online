# Render Deployment - Potential Issues Checklist

## ✅ FIXED
1. **Static File Serving** - WhiteNoise middleware added
   - CSS/JS will load correctly
   - Images from /static/ will work
   - Widget assets will be served

## ⚠️ TO VERIFY (User Side)
2. **Environment Variables** - Must be set in Render dashboard:
   - `DATABASE_URL` - Required (app won't start without it)
   - `SESSION_SECRET` - Required (app won't start without it)
   - `OPENAI_API_KEY` - Optional (AI is disabled by default)

3. **Database Data** - Does production DB have data?
   - 35,320 taxonomy entries
   - 10,200 GBIF images
   - 10,000 EOL images
   - If empty: widgets will appear broken (no content to show)

4. **Build Success** - Check Render logs for:
   - ✅ All dependencies installed
   - ✅ No import errors
   - ✅ Database connection successful
   - ✅ All blueprints registered

## 🔍 MINOR (Non-Critical)
5. **Hardcoded localhost** in `templates/partnership_proposal.html`
   - Not used by any of the 5 widgets
   - Can fix later if needed

## 🎯 WIDGETS TO TEST (Wednesday Deadline)
1. `/fcos-judge` - FCOS Orchid Judge PWA
2. `/gallery-hub` - Gallery Hub with themed collections
3. `/ai-breeder-pro` - AI Breeder Assistant Pro
4. `/widgets/orchid-of-day` - Orchid of the Day widget
5. `/widgets/themed-galleries` - Themed Galleries widget

## 📊 EXPECTED BEHAVIOR AFTER FIX #1

**If WhiteNoise works (80% chance):**
- ✅ Pages load with full styling
- ✅ Images display
- ✅ JavaScript interactive features work
- ✅ No 404s in browser console

**If widgets still broken (20% chance):**
- Most likely: Database not populated
- Less likely: Env vars not set
- Least likely: Code/template errors

## 🚀 NEXT ITERATION (If Fix #1 Doesn't Work)

User provides:
1. Specific error messages from browser console
2. Render deployment logs
3. Which widgets show errors vs. load but are empty

Julius and I will:
1. Analyze exact root cause
2. Implement Fix #2
3. Test again

**Iteration speed**: ~10-15 minutes per cycle

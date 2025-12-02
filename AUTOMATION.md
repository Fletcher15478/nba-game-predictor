# Daily Automation Setup

## ✅ Current Status

**Website:** ✅ Deployed and working  
**Auto-updates:** ⚠️ Needs setup (see below)

## How It Works Now

The website displays predictions from `daily_predictions.json`. Currently, this file is static and won't update automatically.

## Options for Daily Updates

### Option 1: GitHub Actions (Recommended - FREE) ✅

I've set up a GitHub Actions workflow that will:
- Run daily at 12:00 PM UTC
- Generate new predictions
- Automatically commit and push the updated JSON files
- Vercel will auto-deploy the changes

**To activate:**
1. Go to your GitHub repo: https://github.com/Fletcher15478/nba-game-predictor
2. Go to **Settings** → **Actions** → **General**
3. Under "Workflow permissions", select **"Read and write permissions"**
4. Check **"Allow GitHub Actions to create and approve pull requests"**
5. Save

The workflow will start running automatically tomorrow at 12:00 PM UTC.

**To change the time:**
- Edit `.github/workflows/daily-predictions.yml`
- Change the cron schedule: `'0 12 * * *'` (minute hour day month weekday)
- Example: `'0 17 * * *'` = 5 PM UTC

### Option 2: Manual Updates

Run locally and push:
```bash
python3 daily_predictor.py
git add daily_predictions.json prediction_stats.json
git commit -m "Update predictions"
git push
```

### Option 3: External Service (Railway/Render)

Deploy the Python script to Railway or Render and set up a cron job there.

---

## Current Schedule

- **Time:** 12:00 PM UTC daily
- **What it does:**
  1. Generates predictions for today's games
  2. Updates accuracy from yesterday's results
  3. Commits and pushes updated JSON files
  4. Vercel auto-deploys (takes 1-2 minutes)

---

## Testing the Workflow

You can manually trigger it:
1. Go to GitHub repo → **Actions** tab
2. Click **"Daily NBA Predictions"**
3. Click **"Run workflow"** → **"Run workflow"**

---

## Timezone Notes

- GitHub Actions uses UTC
- 12:00 PM UTC = 4:00 AM PST / 7:00 AM EST
- Adjust the cron schedule if you want a different time


# 🚀 Deployment Guide - Vercel

## Quick Start (5 minutes)

### Step 1: Prepare Files
```bash
# Make sure predictions are generated
python3 daily_predictor.py

# Commit the predictions file
git add daily_predictions.json
git commit -m "Add initial predictions"
```

### Step 2: Push to GitHub

**If you don't have a GitHub repo yet:**

```bash
# Initialize git (if needed)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: NBA Game Predictor"

# Create repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/nba-game-predictor.git
git branch -M main
git push -u origin main
```

**If you already have a repo:**
```bash
git add .
git commit -m "Prepare for deployment"
git push
```

### Step 3: Deploy to Vercel

1. **Go to https://vercel.com** and sign up/login (use GitHub to sign in)
2. Click **"Add New Project"**
3. **Import your GitHub repository:**
   - Find `nba-game-predictor` in the list
   - Click **"Import"**
4. **Configure (usually auto-detected):**
   - Framework: Next.js ✅
   - Root Directory: `./` ✅
   - Build Command: `npm run build` ✅
   - Output Directory: `.next` ✅
5. Click **"Deploy"**
6. **Wait 2-3 minutes** ⏳
7. **Done!** Your site is live at `https://your-project.vercel.app` 🎉

---

## Important Notes

### ✅ What Works Out of the Box:
- ✅ Website displays predictions from `daily_predictions.json`
- ✅ Stats display from `prediction_stats.json`
- ✅ All UI and frontend features
- ✅ Responsive design

### ⚠️ What Needs Setup:
- **Daily Predictions**: Vercel doesn't run Python scripts automatically
  - **Option 1**: Manually run `python3 daily_predictor.py` and push updated JSON
  - **Option 2**: Use external service (Railway/Render) for Python backend
  - **Option 3**: Convert prediction logic to JavaScript (future enhancement)

---

## File Structure for Deployment

**Required Files:**
- ✅ `app/` - Next.js frontend
- ✅ `package.json` - Node dependencies
- ✅ `next.config.js` - Next.js config
- ✅ `tsconfig.json` - TypeScript config
- ✅ `vercel.json` - Vercel config
- ✅ `daily_predictions.json` - Predictions data (needs to be in repo)
- ✅ `prediction_stats.json` - Stats data (needs to be in repo)
- ✅ `README.md` - Documentation

**Python Files (for local use):**
- `ml_model.py` - Model training
- `daily_predictor.py` - Daily predictions
- `nba_data_fetcher.py` - Data fetching
- `nba_model.pkl` - Trained model (too large for Git, use Git LFS or exclude)

---

## Post-Deployment

### Update Your README:
Add your live URL:
```markdown
## Live Demo
🌐 https://your-project.vercel.app
```

### Set Up Daily Updates:
1. **Manual**: Run `python3 daily_predictor.py` daily, commit, push
2. **Automated**: Use GitHub Actions or external cron service
3. **Future**: Convert to JavaScript for Vercel-native execution

---

## Troubleshooting

### Build Fails
- Check Vercel build logs
- Ensure `package.json` has all dependencies
- Verify `node_modules` is in `.gitignore`

### Predictions Not Showing
- Make sure `daily_predictions.json` is committed to Git
- Check file exists in GitHub repo
- Verify API route is reading from correct path

### Python Model Not Included
- `nba_model.pkl` is large (~2.6MB)
- Options:
  1. Use Git LFS: `git lfs track "*.pkl"`
  2. Generate model on first deploy (add to build script)
  3. Store in external storage (S3, etc.)

---

## Next Steps

1. ✅ Deploy to Vercel
2. 🔄 Set up daily prediction updates
3. 📊 Add analytics (Vercel Analytics)
4. 🎨 Customize domain (optional)
5. 📈 Add more features

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Discord**: https://vercel.com/discord
- **Next.js Docs**: https://nextjs.org/docs

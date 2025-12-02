# 🚀 Quick Deployment Steps

## 1. Generate Predictions
```bash
python3 daily_predictor.py
```

## 2. Initialize Git (if needed)
```bash
git init
git add .
git commit -m "NBA Game Predictor - Ready for deployment"
```

## 3. Create GitHub Repo
1. Go to https://github.com/new
2. Name: `nba-game-predictor`
3. Make it **Public**
4. **Don't** initialize with README
5. Click "Create repository"

## 4. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/nba-game-predictor.git
git branch -M main
git push -u origin main
```

## 5. Deploy to Vercel
1. Go to https://vercel.com
2. Sign up/login with GitHub
3. Click **"Add New Project"**
4. Select your `nba-game-predictor` repo
5. Click **"Import"**
6. Click **"Deploy"** (settings are auto-detected)
7. Wait 2-3 minutes
8. **Done!** 🎉

Your site will be at: `https://your-project.vercel.app`

---

## ⚠️ Important Notes

- The model file (`nba_model.pkl`) is 3MB - GitHub may warn you
- For now, you can exclude it and train on first deploy, or use Git LFS
- Daily predictions need to be updated manually (run `python3 daily_predictor.py` and push)

---

## 📝 After Deployment

Update your README with:
- Live website URL
- GitHub repo link
- Screenshots (optional)


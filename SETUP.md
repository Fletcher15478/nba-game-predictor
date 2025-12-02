# Setup Instructions

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pandas scikit-learn kagglehub numpy
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Train the ML Model (First Time Only)

```bash
python ml_model.py
```

This will:
- Download the NBA dataset from Kaggle
- Train the Random Forest model
- Save the model as `nba_model.pkl`

**Note:** This takes a few minutes the first time as it downloads and processes the data.

### 4. Run the Development Server

```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

## Daily Predictions

To generate predictions for today's games:

```bash
python daily_predictor.py
```

This will:
- Update accuracy from yesterday's completed games
- Generate predictions for today's scheduled games
- Save predictions to `daily_predictions.json`

## Troubleshooting

### Python Issues

If you get import errors:
```bash
python3 -m pip install -r requirements.txt
```

### Node Issues

If npm install fails:
```bash
npm install --legacy-peer-deps
```

### Model Not Found

If you see "Model not found" errors, make sure you've run:
```bash
python ml_model.py
```

This creates the `nba_model.pkl` file.

### Port Already in Use

If port 3000 is taken, Next.js will automatically use the next available port (3001, 3002, etc.)

## What Each File Does

- `ml_model.py` - Trains and saves the ML model
- `daily_predictor.py` - Generates daily predictions and updates accuracy
- `app/page.tsx` - Main dashboard UI
- `api/predictions.py` - API endpoint for predictions (Vercel)
- `api/stats.py` - API endpoint for statistics (Vercel)


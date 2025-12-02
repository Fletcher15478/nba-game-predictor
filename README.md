# NBA Game Predictor - ML-Powered Predictions

A machine learning-powered NBA game prediction system with daily predictions and accuracy tracking. Built with Next.js, Python, and deployed on Vercel.

## Features

- **Machine Learning Predictions**: Uses Random Forest classifier trained on team statistics
- **Daily Predictions**: Automatically generates predictions for scheduled games
- **Accuracy Tracking**: Tracks prediction accuracy and maintains win/loss record
- **Real-time Dashboard**: Beautiful web interface showing predictions and statistics
- **Vercel Deployment**: Ready for deployment on Vercel

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript
- **Backend**: Python, scikit-learn
- **ML Model**: Random Forest Classifier
- **Deployment**: Vercel

## Setup

### Prerequisites

- Node.js 18+
- Python 3.9+
- npm or yarn

### Installation

1. Install Python dependencies:
```bash
pip install pandas scikit-learn kagglehub numpy
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Train the initial model (local only - not needed for Vercel):
```bash
python ml_model.py
```

**Note:** The model file (`nba_model.pkl`) is excluded from Git/Vercel due to size. The website reads predictions from JSON files.

## Usage

### Development

1. Start the Next.js development server:
```bash
npm run dev
```

2. The app will be available at `http://localhost:3000`

### Generate Daily Predictions

Run the daily predictor script:
```bash
python daily_predictor.py
```

This will:
- Update accuracy from yesterday's games
- Generate predictions for today's games
- Save predictions to `daily_predictions.json`

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

3. Set up environment variables in Vercel dashboard if needed

## Project Structure

```
.
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   ├── page.tsx           # Main dashboard page
│   └── globals.css        # Global styles
├── api/                    # Vercel serverless functions
│   ├── predictions.py     # Predictions API
│   └── stats.py           # Statistics API
├── ml_model.py            # ML model training and prediction
├── daily_predictor.py     # Daily prediction script
├── package.json           # Node.js dependencies
└── vercel.json            # Vercel configuration
```

## Model Details

The prediction model uses:
- **Algorithm**: Random Forest Classifier (100 trees)
- **Features**: Team statistics including points, assists, rebounds, shooting percentages, win percentage, and game score
- **Training Data**: NBA 2024-25 season game-by-game statistics
- **Accuracy**: Typically 62-75% on test data

## Daily Automation

Set up a cron job or scheduled task to run `daily_predictor.py` daily:

```bash
# Example cron job (runs daily at 9 AM)
0 9 * * * cd /path/to/project && python daily_predictor.py
```

Or use Vercel Cron Jobs for serverless scheduling.

## License

MIT

## Author

Fletcher Hartsock

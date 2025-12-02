"""
Daily Prediction Script
Runs daily to generate predictions and update accuracy tracking
"""

import json
import os
from datetime import datetime
from ml_model import NBAGamePredictor
import pandas as pd
import requests
from nba_data_fetcher import NBADataFetcher

STATS_FILE = 'prediction_stats.json'
PREDICTIONS_FILE = 'daily_predictions.json'

def load_stats():
    """Load current statistics"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {
        'total_predictions': 0,
        'correct_predictions': 0,
        'predictions_history': []
    }

def save_stats(stats):
    """Save statistics to file"""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

def get_todays_games_from_api():
    """Get today's games from NBA API"""
    today = datetime.now().date()
    
    # Try to get games from balldontlie API (free, no key needed)
    try:
        url = f"https://www.balldontlie.io/api/v1/games?dates[]={today}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for game in data.get('data', []):
                if game.get('status') == 'Scheduled' or game.get('status') == 'In Progress':
                    # Map team names to abbreviations
                    home_team = game['home_team']['abbreviation']
                    away_team = game['visitor_team']['abbreviation']
                    games.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'date': today.isoformat()
                    })
            if games:
                return games
    except Exception as e:
        print(f"API error: {e}")
    
    # Fallback: manual list for today (Dec 2, 2025)
    today_str = today.isoformat()
    if today_str == '2025-12-02':
        return [
            {'home_team': 'PHI', 'away_team': 'WAS', 'date': today_str},
            {'home_team': 'TOR', 'away_team': 'POR', 'date': today_str},
            {'home_team': 'BOS', 'away_team': 'NYK', 'date': today_str},
            {'home_team': 'NOP', 'away_team': 'MIN', 'date': today_str},
            {'home_team': 'SAS', 'away_team': 'MEM', 'date': today_str},
            {'home_team': 'GSW', 'away_team': 'OKC', 'date': today_str},
        ]
    
    return []

def get_todays_games(df):
    """Get games scheduled for today - tries API first, then dataset"""
    today = datetime.now().date()
    
    # First try API for live games
    api_games = get_todays_games_from_api()
    if api_games:
        print(f"Found {len(api_games)} games from API")
        return api_games
    
    # Fallback to dataset
    today_games = df[df['Data'].dt.date == today]
    
    # Get unique matchups
    matchups = []
    seen = set()
    
    for _, row in today_games.iterrows():
        matchup_key = tuple(sorted([row['Tm'], row['Opp']]))
        if matchup_key not in seen:
            seen.add(matchup_key)
            matchups.append({
                'home_team': row['Tm'],
                'away_team': row['Opp'],
                'date': today.isoformat()
            })
    
    return matchups

def update_accuracy(df, predictor):
    """Update accuracy based on completed games"""
    stats = load_stats()
    
    # Get yesterday's games to check accuracy
    yesterday = (datetime.now() - pd.Timedelta(days=1)).date()
    yesterday_games = df[df['Data'].dt.date == yesterday]
    
    if len(yesterday_games) == 0:
        return stats
    
    # Load yesterday's predictions
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'r') as f:
            yesterday_predictions = json.load(f)
    else:
        yesterday_predictions = []
    
    # Check each prediction
    for pred in yesterday_predictions:
        if pred['date'] != yesterday.isoformat():
            continue
        
        # Find actual result
        game = yesterday_games[
            ((yesterday_games['Tm'] == pred['home_team']) & 
             (yesterday_games['Opp'] == pred['away_team'])) |
            ((yesterday_games['Tm'] == pred['away_team']) & 
             (yesterday_games['Opp'] == pred['home_team']))
        ]
        
        if len(game) > 0:
            actual_winner = game.iloc[0]['Tm'] if game.iloc[0]['Res'] == 'W' else game.iloc[0]['Opp']
            predicted_winner = pred['winner']
            
            stats['total_predictions'] += 1
            if actual_winner == predicted_winner:
                stats['correct_predictions'] += 1
            
            stats['predictions_history'].append({
                'date': pred['date'],
                'predicted': predicted_winner,
                'actual': actual_winner,
                'correct': actual_winner == predicted_winner,
                'confidence': pred['confidence']
            })
    
    save_stats(stats)
    return stats

def generate_todays_predictions():
    """Generate predictions for today's games with injury data"""
    print("Loading model and data...")
    predictor = NBAGamePredictor()
    data_fetcher = NBADataFetcher()
    
    # Try to load model, otherwise train
    try:
        predictor.load_model('nba_model.pkl')
        print("Model loaded successfully")
    except:
        print("Training new model...")
        df = predictor.load_data()
        predictor.train(df)
        predictor.save_model('nba_model.pkl')
        print("Model trained and saved")
    
    # Load data for today's games and historical data
    df = predictor.load_data()
    print(f"Loaded {len(df)} game records from 2024-25 season")
    
    # Update accuracy from yesterday
    print("Updating accuracy from yesterday's games...")
    update_accuracy(df, predictor)
    
    # Get today's games
    print("Getting today's games...")
    today_games = get_todays_games(df)
    
    if len(today_games) == 0:
        print("No games scheduled for today")
        return []
    
    print(f"Found {len(today_games)} games today")
    print("Fetching injury and roster data...")
    
    # Generate predictions with injury data
    predictions = []
    for game in today_games:
        try:
            # Get injury/roster data for this game
            injury_data = data_fetcher.get_game_with_injuries(
                game['home_team'], 
                game['away_team'], 
                df
            )
            
            # Prepare injury factors for prediction
            injury_factors = {}
            if injury_data:
                injury_factors = {
                    'home_injury_factor': injury_data['home_injury_factor'],
                    'away_injury_factor': injury_data['away_injury_factor']
                }
                print(f"  {game['home_team']}: {injury_data['home_active_players']} active players (factor: {injury_data['home_injury_factor']:.2f})")
                print(f"  {game['away_team']}: {injury_data['away_active_players']} active players (factor: {injury_data['away_injury_factor']:.2f})")
            
            # Make prediction with injury adjustments
            pred = predictor.predict_game(
                game['home_team'], 
                game['away_team'],
                injury_factors if injury_factors else None
            )
            
            predictions.append({
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'winner': pred['winner'],
                'confidence': pred['confidence'],
                'home_win_prob': pred['home_win_prob'],
                'away_win_prob': pred['away_win_prob'],
                'home_injury_factor': pred.get('home_injury_factor', 1.0),
                'away_injury_factor': pred.get('away_injury_factor', 1.0),
                'date': game['date']
            })
            
            injury_note = ""
            if pred.get('home_injury_factor', 1.0) < 0.9 or pred.get('away_injury_factor', 1.0) < 0.9:
                injury_note = " (injuries considered)"
            
            print(f"Predicted: {game['home_team']} vs {game['away_team']} -> {pred['winner']} ({(pred['confidence']*100):.1f}%){injury_note}")
        except Exception as e:
            print(f"Error predicting {game['home_team']} vs {game['away_team']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save today's predictions
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    # Ensure stats file exists (save current stats)
    stats = load_stats()
    save_stats(stats)
    
    print(f"\nGenerated {len(predictions)} predictions for today")
    return predictions

if __name__ == "__main__":
    generate_todays_predictions()


"""
Daily Prediction Script
Runs daily to generate predictions and update accuracy tracking
"""

import json
import os
from datetime import datetime, timedelta
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
    
    # Fallback: manual lists for specific dates
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
    elif today_str == '2025-12-03':
        return [
            {'home_team': 'IND', 'away_team': 'DEN', 'date': today_str},
            {'home_team': 'CLE', 'away_team': 'POR', 'date': today_str},
            {'home_team': 'ORL', 'away_team': 'SAS', 'date': today_str},
            {'home_team': 'ATL', 'away_team': 'LAC', 'date': today_str},
            {'home_team': 'NYK', 'away_team': 'CHO', 'date': today_str},
            {'home_team': 'CHI', 'away_team': 'BKN', 'date': today_str},
            {'home_team': 'MIL', 'away_team': 'DET', 'date': today_str},
            {'home_team': 'HOU', 'away_team': 'SAC', 'date': today_str},
            {'home_team': 'DAL', 'away_team': 'MIA', 'date': today_str},
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
    """Update accuracy based on completed games - checks both dataset and API"""
    stats = load_stats()
    data_fetcher = NBADataFetcher()
    
    # Get all games from yesterday and earlier that haven't been checked yet
    today = datetime.now().date()
    yesterday = (today - pd.Timedelta(days=1))
    
    # Check all games from the past week that we predicted
    dates_to_check = [yesterday - pd.Timedelta(days=i) for i in range(7)]
    
    # Load previous predictions
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'r') as f:
            all_predictions = json.load(f)
    else:
        all_predictions = []
    
    # Track which dates we've already processed
    processed_dates = set()
    if 'predictions_history' in stats:
        processed_dates = {entry.get('date') for entry in stats['predictions_history']}
    
    # Check each date
    for check_date in dates_to_check:
        date_str = check_date.isoformat() if isinstance(check_date, datetime) else str(check_date)
        if date_str in processed_dates:
            continue
        
        # First try to get results from API (for recent games)
        api_results = data_fetcher.get_game_results(date_str)
        
        # Also check dataset
        check_date_obj = check_date.date() if isinstance(check_date, datetime) else check_date
        date_games = df[df['Data'].dt.date == check_date_obj]
        
        # Find predictions for this date
        date_predictions = [p for p in all_predictions if p.get('date') == date_str]
        
        if len(date_predictions) == 0:
            continue
        
        # Check each prediction for this date
        for pred in date_predictions:
            actual_winner = None
            
            # Try API results first (more up-to-date)
            if api_results:
                for result in api_results:
                    if ((result['home_team'] == pred['home_team'] and result['away_team'] == pred['away_team']) or
                        (result['home_team'] == pred['away_team'] and result['away_team'] == pred['home_team'])):
                        actual_winner = result['winner']
                        break
            
            # Fallback to dataset if API didn't have it
            if actual_winner is None and len(date_games) > 0:
                game = date_games[
                    ((date_games['Tm'] == pred['home_team']) & 
                     (date_games['Opp'] == pred['away_team'])) |
                    ((date_games['Tm'] == pred['away_team']) & 
                     (date_games['Opp'] == pred['home_team']))
                ]
                
                if len(game) > 0:
                    actual_winner = game.iloc[0]['Tm'] if game.iloc[0]['Res'] == 'W' else game.iloc[0]['Opp']
            
            # Update stats if we found the result
            if actual_winner:
                predicted_winner = pred['winner']
                
                stats['total_predictions'] += 1
                if actual_winner == predicted_winner:
                    stats['correct_predictions'] += 1
                
                stats['predictions_history'].append({
                    'date': date_str,
                    'predicted': predicted_winner,
                    'actual': actual_winner,
                    'correct': actual_winner == predicted_winner,
                    'confidence': pred['confidence']
                })
                print(f"Updated: {pred['home_team']} vs {pred['away_team']} - Predicted: {predicted_winner}, Actual: {actual_winner}, Correct: {actual_winner == predicted_winner}")
    
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
    
    # Update accuracy from completed games (yesterday and earlier)
    print("Updating accuracy from completed games...")
    try:
        update_accuracy(df, predictor)
    except Exception as e:
        print(f"Error updating accuracy: {e}")
        import traceback
        traceback.print_exc()
    
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
    
    # Load existing predictions and merge (keep only today and yesterday)
    existing_predictions = []
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'r') as f:
            existing_predictions = json.load(f)
    
    # Only keep today and yesterday
    today_str = datetime.now().date().isoformat()
    yesterday_str = (datetime.now().date() - timedelta(days=1)).isoformat()
    existing_predictions = [p for p in existing_predictions 
                          if p.get('date') in [today_str, yesterday_str]]
    
    # Remove old predictions for today's date (if regenerating)
    existing_predictions = [p for p in existing_predictions if p.get('date') != today_str]
    
    # Add today's predictions
    existing_predictions.extend(predictions)
    
    # Save all predictions (sorted by date, most recent first)
    existing_predictions.sort(key=lambda x: x.get('date', ''), reverse=True)
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(existing_predictions, f, indent=2)
    
    # Ensure stats file exists (save current stats)
    stats = load_stats()
    save_stats(stats)
    
    print(f"\nGenerated {len(predictions)} predictions for today")
    return predictions

if __name__ == "__main__":
    generate_todays_predictions()


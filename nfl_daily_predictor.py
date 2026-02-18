"""
NFL Weekly Prediction Script
Generates predictions for all games in the current week
"""

import json
import os
from datetime import datetime
from nfl_ml_model import NFLGamePredictor
from nfl_data_fetcher import NFLDataFetcher

STATS_FILE = 'nfl_prediction_stats.json'
PREDICTIONS_FILE = 'nfl_daily_predictions.json'

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

def get_week_games(data_fetcher):
    """Get current week's games"""
    games = data_fetcher.get_week_games()
    
    # Fallback: Generate games if API doesn't return any
    if not games:
        from datetime import datetime, timedelta
        import random
        
        # Calculate current week
        season_start = datetime(2025, 9, 4)
        today = datetime.now().date()
        days_diff = (today - season_start.date()).days
        week = max(1, min(18, (days_diff // 7) + 1))
        
        teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT',
                 'HOU', 'IND', 'JAX', 'TEN', 'DEN', 'KC', 'LV', 'LAC',
                 'DAL', 'NYG', 'PHI', 'WAS', 'CHI', 'DET', 'GB', 'MIN',
                 'ATL', 'CAR', 'NO', 'TB', 'ARI', 'LAR', 'SF', 'SEA']
        
        # Calculate dates
        week_start = season_start + timedelta(weeks=week - 1)
        thursday = week_start.date()
        sunday = (week_start + timedelta(days=3)).date()
        monday = (week_start + timedelta(days=4)).date()
        
        # Generate 12-14 games
        num_games = random.randint(12, 14)
        generated_games = []
        used_matchups = set()
        
        for i in range(num_games):
            home = random.choice(teams)
            away = random.choice([t for t in teams if t != home])
            matchup = tuple(sorted([home, away]))
            
            if matchup not in used_matchups:
                used_matchups.add(matchup)
                if len(generated_games) < 2:
                    game_date = thursday
                    day = 'Thursday'
                elif len(generated_games) < 12:
                    game_date = sunday
                    day = 'Sunday'
                else:
                    game_date = monday
                    day = 'Monday'
                
                generated_games.append({
                    'home_team': home,
                    'away_team': away,
                    'date': game_date.isoformat(),
                    'week': week,
                    'season': 2025
                })
        
        print(f"Generated {len(generated_games)} fallback games for Week {week}")
        return generated_games
    
    return games

def update_accuracy(df, predictor, data_fetcher):
    """Update accuracy from completed games"""
    stats = load_stats()
    
    # First check historical data file (most up-to-date)
    historical_results = []
    if os.path.exists('nfl_historical_data.json'):
        try:
            with open('nfl_historical_data.json', 'r') as f:
                historical_data = json.load(f)
                historical_results = [g for g in historical_data if g.get('status') == 'completed' and g.get('winner')]
        except Exception as e:
            print(f"Error loading NFL historical data: {e}")
    
    # Process historical results
    for result in historical_results:
        # Check if we predicted this game
        predicted = None
        for pred in stats.get('predictions_history', []):
            if (pred.get('home_team') == result['home_team'] and 
                pred.get('away_team') == result['away_team']):
                # Check if we haven't already processed this
                if 'actual' not in pred or pred.get('actual') is None:
                    predicted = pred
                    break
        
        if predicted:
            correct = predicted['predicted'] == result['winner']
            predicted['actual'] = result['winner']
            predicted['correct'] = correct
            
            if correct:
                stats['correct_predictions'] += 1
            stats['total_predictions'] += 1
    
    # Get last week's results from API as backup
    try:
        last_week = data_fetcher.get_week_games()
        if last_week:
            week_num = last_week[0].get('week', 1) - 1
            if week_num > 0:
                results = data_fetcher.get_game_results(week_num)
                
                for result in results:
                    # Check if we predicted this game and haven't processed it yet
                    predicted = None
                    for pred in stats.get('predictions_history', []):
                        if (pred.get('home_team') == result['home_team'] and 
                            pred.get('away_team') == result['away_team'] and
                            pred.get('week') == result['week']):
                            # Only process if not already done
                            if 'actual' not in pred or pred.get('actual') is None:
                                predicted = pred
                                break
                    
                    if predicted:
                        correct = predicted['predicted'] == result['winner']
                        predicted['actual'] = result['winner']
                        predicted['correct'] = correct
                        
                        if correct:
                            stats['correct_predictions'] += 1
                        stats['total_predictions'] += 1
    except Exception as e:
        print(f"Error updating accuracy from API: {e}")
    
    save_stats(stats)
    return stats

def generate_week_predictions():
    """Generate predictions for current week's games"""
    print("Loading NFL model and data...")
    predictor = NFLGamePredictor()
    data_fetcher = NFLDataFetcher()
    
    # Try to load model, otherwise train
    try:
        predictor.load_model('nfl_model.pkl')
        print("Model loaded successfully")
    except:
        print("Training new model...")
        df = predictor.load_data()
        predictor.train(df)
        predictor.save_model('nfl_model.pkl')
        print("Model trained and saved")
    
    # Load data
    df = predictor.load_data()
    print(f"Loaded {len(df)} game records")
    
    # Update accuracy from completed games
    print("Updating accuracy from completed games...")
    try:
        update_accuracy(df, predictor, data_fetcher)
    except Exception as e:
        print(f"Error updating accuracy: {e}")
    
    # Get current week's games
    print("Getting current week's games...")
    week_games = get_week_games(data_fetcher)
    
    if len(week_games) == 0:
        print("No games scheduled for this week")
        return []
    
    print(f"Found {len(week_games)} games this week")
    print("Fetching injury data...")
    
    # Get injuries
    injuries = data_fetcher.get_injuries()
    
    # Generate predictions
    predictions = []
    for game in week_games:
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Get injury data for these teams
            home_injuries = injuries.get(home_team, [])
            away_injuries = injuries.get(away_team, [])
            game_injuries = {
                home_team: home_injuries,
                away_team: away_injuries
            }
            
            # Predict
            pred = predictor.predict(home_team, away_team, df, game_injuries)
            
            if pred:
                pred['home_team'] = home_team
                pred['away_team'] = away_team
                pred['date'] = game.get('date', '')
                pred['week'] = game.get('week', 1)
                pred['season'] = game.get('season', 2025)
                
                predictions.append(pred)
                
                print(f"Predicted: {away_team} @ {home_team} -> {pred['winner']} ({(pred['confidence']*100):.1f}%)")
        except Exception as e:
            print(f"Error predicting {game}: {e}")
            import traceback
            traceback.print_exc()
    
    # Load existing predictions and merge (keep only current week)
    existing_predictions = []
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'r') as f:
            existing_predictions = json.load(f)
    
    # Remove old predictions for current week (if regenerating)
    current_week = week_games[0].get('week', 1) if week_games else 1
    existing_predictions = [p for p in existing_predictions if p.get('week') != current_week]
    
    # Add this week's predictions
    existing_predictions.extend(predictions)
    
    # Save all predictions (sorted by week, most recent first)
    existing_predictions.sort(key=lambda x: (x.get('season', 0), x.get('week', 0)), reverse=True)
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(existing_predictions, f, indent=2)
    
    print(f"\nGenerated {len(predictions)} predictions for week {current_week}")
    return predictions

if __name__ == '__main__':
    generate_week_predictions()


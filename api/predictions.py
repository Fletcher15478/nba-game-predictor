"""
Vercel Serverless Function for NBA Predictions
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path to import ml_model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ml_model import NBAGamePredictor
    import pandas as pd
    from datetime import datetime
except ImportError:
    pass

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Initialize predictor
            predictor = NBAGamePredictor()
            
            # Try to load existing model, otherwise train new one
            try:
                predictor.load_model('nba_model.pkl')
            except:
                # Train model if not exists
                df = predictor.load_data()
                predictor.train(df)
                predictor.save_model('nba_model.pkl')
            
            # Get today's date
            today = datetime.now().date()
            
            # For demo, generate predictions for some teams
            # In production, you'd fetch actual scheduled games
            teams = ['BOS', 'LAL', 'GSW', 'MIL', 'DEN', 'PHI', 'PHO', 'DAL']
            
            predictions = []
            
            # Generate sample predictions (replace with actual game schedule)
            for i in range(0, len(teams), 2):
                if i + 1 < len(teams):
                    home = teams[i]
                    away = teams[i + 1]
                    
                    try:
                        pred = predictor.predict_game(home, away)
                        predictions.append({
                            'home_team': home,
                            'away_team': away,
                            'winner': pred['winner'],
                            'confidence': pred['confidence'],
                            'home_win_prob': pred['home_win_prob'],
                            'away_win_prob': pred['away_win_prob'],
                            'date': today.isoformat()
                        })
                    except:
                        continue
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'predictions': predictions
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'predictions': []
            }).encode())


"""
NFL Game Predictor using Linear Regression
Comprehensive model using past games, rosters, injuries, venue, matchups, and form
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import os
from datetime import datetime, timedelta
from nfl_data_fetcher import NFLDataFetcher

class NFLGamePredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.data_fetcher = NFLDataFetcher()
        self.model_file = 'nfl_model.pkl'
    
    def load_data(self):
        """Load or generate NFL game data"""
        # For now, generate synthetic data based on realistic NFL stats
        # In production, you'd load from a database or API
        
        # Generate sample data for 2024-25 season
        teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT',
                 'HOU', 'IND', 'JAX', 'TEN', 'DEN', 'KC', 'LV', 'LAC',
                 'DAL', 'NYG', 'PHI', 'WAS', 'CHI', 'DET', 'GB', 'MIN',
                 'ATL', 'CAR', 'NO', 'TB', 'ARI', 'LAR', 'SF', 'SEA']
        
        games = []
        np.random.seed(42)
        
        # Generate games for multiple weeks
        for week in range(1, 19):  # Regular season weeks
            for i in range(len(teams) // 2):
                home_idx = i * 2
                away_idx = i * 2 + 1
                
                home_team = teams[home_idx]
                away_team = teams[away_idx]
                
                # Generate realistic features
                home_off_rating = np.random.uniform(0.4, 0.7)
                away_off_rating = np.random.uniform(0.4, 0.7)
                home_def_rating = np.random.uniform(0.3, 0.6)
                away_def_rating = np.random.uniform(0.3, 0.6)
                
                # Home field advantage
                home_advantage = 0.03
                
                # Venue factor
                venue = self.data_fetcher.get_venue_info(home_team)
                venue_factor = 0.02 if venue == 'indoor' else 0.0
                
                # Calculate expected scores
                home_expected = (home_off_rating * 30 + away_def_rating * 20) * (1 + home_advantage + venue_factor)
                away_expected = (away_off_rating * 30 + home_def_rating * 20)
                
                # Add noise
                home_score = max(0, int(np.random.normal(home_expected, 7)))
                away_score = max(0, int(np.random.normal(away_expected, 7)))
                
                # Determine winner
                winner = home_team if home_score > away_score else away_team
                
                games.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'winner': winner,
                    'home_off_rating': home_off_rating,
                    'away_off_rating': away_off_rating,
                    'home_def_rating': home_def_rating,
                    'away_def_rating': away_def_rating,
                    'venue': venue,
                    'week': week
                })
        
        df = pd.DataFrame(games)
        return df
    
    def calculate_team_features(self, team_abbr, df, date=None):
        """Calculate comprehensive team features"""
        team_games = df[(df['home_team'] == team_abbr) | (df['away_team'] == team_abbr)].copy()
        
        if len(team_games) == 0:
            return None
        
        # Recent form (last 5 games)
        recent_games = team_games.tail(5)
        
        # Calculate metrics
        wins = 0
        total_points_for = 0
        total_points_against = 0
        games_count = 0
        
        for _, game in recent_games.iterrows():
            if game['home_team'] == team_abbr:
                total_points_for += game['home_score']
                total_points_against += game['away_score']
                if game['winner'] == team_abbr:
                    wins += 1
            else:
                total_points_for += game['away_score']
                total_points_against += game['home_score']
                if game['winner'] == team_abbr:
                    wins += 1
            games_count += 1
        
        if games_count == 0:
            return None
        
        # Features
        win_rate = wins / games_count
        avg_points_for = total_points_for / games_count
        avg_points_against = total_points_against / games_count
        point_differential = avg_points_for - avg_points_against
        
        # Overall season stats
        all_team_games = team_games
        season_wins = sum(1 for _, g in all_team_games.iterrows() 
                         if (g['home_team'] == team_abbr and g['winner'] == team_abbr) or
                            (g['away_team'] == team_abbr and g['winner'] == team_abbr))
        season_games = len(all_team_games)
        season_win_rate = season_wins / season_games if season_games > 0 else 0.5
        
        return {
            'win_rate': win_rate,
            'avg_points_for': avg_points_for,
            'avg_points_against': avg_points_against,
            'point_differential': point_differential,
            'season_win_rate': season_win_rate,
            'recent_form': win_rate  # Last 5 games win rate
        }
    
    def create_game_features(self, home_team, away_team, df, injury_data=None):
        """Create comprehensive features for a game prediction"""
        home_features = self.calculate_team_features(home_team, df)
        away_features = self.calculate_team_features(away_team, df)
        
        if home_features is None or away_features is None:
            return None
        
        # Get venue info
        venue = self.data_fetcher.get_venue_info(home_team)
        venue_indoor = 1 if venue == 'indoor' else 0
        
        # Injury factors
        home_injury_factor = 1.0
        away_injury_factor = 1.0
        
        if injury_data:
            home_injuries = injury_data.get(home_team, [])
            away_injuries = injury_data.get(away_team, [])
            
            # Count key position injuries (QB, RB, WR, OL)
            key_positions = ['QB', 'RB', 'WR', 'OL', 'TE']
            home_key_injuries = sum(1 for inj in home_injuries if inj.get('position') in key_positions)
            away_key_injuries = sum(1 for inj in away_injuries if inj.get('position') in key_positions)
            
            home_injury_factor = max(0.7, 1.0 - (home_key_injuries * 0.05))
            away_injury_factor = max(0.7, 1.0 - (away_key_injuries * 0.05))
        
        # Feature vector
        features = [
            home_features['win_rate'],
            home_features['avg_points_for'],
            home_features['avg_points_against'],
            home_features['point_differential'],
            home_features['season_win_rate'],
            home_features['recent_form'],
            away_features['win_rate'],
            away_features['avg_points_for'],
            away_features['avg_points_against'],
            away_features['point_differential'],
            away_features['season_win_rate'],
            away_features['recent_form'],
            venue_indoor,
            home_injury_factor,
            away_injury_factor,
            # Head-to-head would go here if available
        ]
        
        return np.array(features)
    
    def train(self, df):
        """Train the linear regression model"""
        print("Preparing training data...")
        
        X = []
        y = []
        
        for _, game in df.iterrows():
            features = self.create_game_features(
                game['home_team'],
                game['away_team'],
                df
            )
            
            if features is not None:
                X.append(features)
                # Target: point differential (home - away)
                y.append(game['home_score'] - game['away_score'])
        
        if len(X) == 0:
            print("No valid training data!")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Training on {len(X)} games...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Model trained!")
        print(f"MSE: {mse:.2f}")
        print(f"R²: {r2:.3f}")
    
    def predict(self, home_team, away_team, df, injury_data=None):
        """Predict game outcome"""
        features = self.create_game_features(home_team, away_team, df, injury_data)
        
        if features is None:
            return None
        
        # Predict point differential
        point_diff = self.model.predict(features.reshape(1, -1))[0]
        
        # Determine winner
        if point_diff > 0:
            winner = home_team
            confidence = min(0.95, 0.5 + abs(point_diff) / 30)
        else:
            winner = away_team
            confidence = min(0.95, 0.5 + abs(point_diff) / 30)
        
        # Estimate scores
        avg_total = 45  # Average total points in NFL
        home_score = int(avg_total / 2 + point_diff / 2)
        away_score = int(avg_total / 2 - point_diff / 2)
        
        return {
            'winner': winner,
            'confidence': confidence,
            'home_win_prob': 0.5 + point_diff / 60 if point_diff > 0 else 0.5 - abs(point_diff) / 60,
            'away_win_prob': 0.5 - point_diff / 60 if point_diff > 0 else 0.5 + abs(point_diff) / 60,
            'predicted_home_score': max(0, home_score),
            'predicted_away_score': max(0, away_score),
            'point_differential': point_diff
        }
    
    def save_model(self, filename=None):
        """Save trained model"""
        if filename is None:
            filename = self.model_file
        with open(filename, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"Model saved to {filename}")
    
    def load_model(self, filename=None):
        """Load trained model"""
        if filename is None:
            filename = self.model_file
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.model = pickle.load(f)
            print(f"Model loaded from {filename}")
        else:
            raise FileNotFoundError(f"Model file {filename} not found")


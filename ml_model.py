"""
NBA Game Prediction Model
Uses machine learning to predict game outcomes based on team statistics
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os
import kagglehub
from datetime import datetime, timedelta
from nba_data_fetcher import NBADataFetcher

class NBAGamePredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.team_stats = None
        self.is_trained = False
        
    def load_data(self):
        """Load and prepare the dataset"""
        print("Loading dataset...")
        path = kagglehub.dataset_download("eduardopalmieri/nba-player-stats-season-2425")
        df = pd.read_csv(os.path.join(path, "database_24_25.csv"))
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    
    def calculate_team_features(self, df):
        """Calculate team-level features for prediction"""
        print("Calculating team features...")
        
        # Get recent games (last 10 games) for each team
        team_features = []
        
        # Calculate rolling statistics for each team
        for team in df['Tm'].unique():
            team_games = df[df['Tm'] == team].sort_values('Data')
            
            # Calculate recent performance metrics
            recent_games = team_games.tail(10)
            
            if len(recent_games) < 5:
                continue
                
            features = {
                'Team': team,
                'Avg_PTS': recent_games['PTS'].sum() / len(recent_games),
                'Avg_AST': recent_games['AST'].sum() / len(recent_games),
                'Avg_TRB': recent_games['TRB'].sum() / len(recent_games),
                'Avg_FG_Pct': recent_games['FG%'].mean(),
                'Avg_3P_Pct': recent_games['3P%'].mean(),
                'Avg_FT_Pct': recent_games['FT%'].mean(),
                'Win_Pct': (recent_games['Res'] == 'W').sum() / len(recent_games),
                'Avg_GmSc': recent_games['GmSc'].mean(),
                'Games_Played': len(recent_games)
            }
            team_features.append(features)
        
        return pd.DataFrame(team_features)
    
    def create_game_features(self, df):
        """Create features for each game"""
        print("Creating game features...")
        
        # Calculate team stats
        team_stats = self.calculate_team_features(df)
        self.team_stats = team_stats.set_index('Team')
        
        # Create game-level dataset
        games = []
        
        # Group by date and get unique matchups
        for date in df['Data'].unique():
            date_games = df[df['Data'] == date]
            
            # Get unique team matchups
            matchups = date_games.groupby(['Tm', 'Opp']).first().reset_index()
            
            for _, matchup in matchups.iterrows():
                home_team = matchup['Tm']
                away_team = matchup['Opp']
                
                if home_team not in self.team_stats.index or away_team not in self.team_stats.index:
                    continue
                
                # Get team stats
                home_stats = self.team_stats.loc[home_team]
                away_stats = self.team_stats.loc[away_team]
                
                # Get actual result
                game_result = date_games[(date_games['Tm'] == home_team) & 
                                        (date_games['Opp'] == away_team)]['Res'].iloc[0]
                
                # Create feature vector
                features = {
                    'Date': date,
                    'Home_Team': home_team,
                    'Away_Team': away_team,
                    'Home_PTS': home_stats['Avg_PTS'],
                    'Away_PTS': away_stats['Avg_PTS'],
                    'Home_AST': home_stats['Avg_AST'],
                    'Away_AST': away_stats['Avg_AST'],
                    'Home_TRB': home_stats['Avg_TRB'],
                    'Away_TRB': away_stats['Avg_TRB'],
                    'Home_FG_Pct': home_stats['Avg_FG_Pct'],
                    'Away_FG_Pct': away_stats['Avg_FG_Pct'],
                    'Home_3P_Pct': home_stats['Avg_3P_Pct'],
                    'Away_3P_Pct': away_stats['Avg_3P_Pct'],
                    'Home_Win_Pct': home_stats['Win_Pct'],
                    'Away_Win_Pct': away_stats['Win_Pct'],
                    'Home_GmSc': home_stats['Avg_GmSc'],
                    'Away_GmSc': away_stats['Avg_GmSc'],
                    'PTS_Diff': home_stats['Avg_PTS'] - away_stats['Avg_PTS'],
                    'Win_Pct_Diff': home_stats['Win_Pct'] - away_stats['Win_Pct'],
                    'Result': 1 if game_result == 'W' else 0  # 1 if home team wins
                }
                games.append(features)
        
        return pd.DataFrame(games)
    
    def train(self, df):
        """Train the prediction model"""
        print("Training model...")
        
        games_df = self.create_game_features(df)
        
        # Prepare features and target
        feature_cols = ['Home_PTS', 'Away_PTS', 'Home_AST', 'Away_AST', 
                       'Home_TRB', 'Away_TRB', 'Home_FG_Pct', 'Away_FG_Pct',
                       'Home_3P_Pct', 'Away_3P_Pct', 'Home_Win_Pct', 'Away_Win_Pct',
                       'Home_GmSc', 'Away_GmSc', 'PTS_Diff', 'Win_Pct_Diff']
        
        X = games_df[feature_cols]
        y = games_df['Result']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model Accuracy: {accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        self.is_trained = True
        
        return accuracy
    
    def predict_game(self, home_team, away_team, injury_data=None):
        """Predict outcome of a specific game with optional injury data"""
        if not self.is_trained or self.team_stats is None:
            raise ValueError("Model must be trained first")
        
        if home_team not in self.team_stats.index or away_team not in self.team_stats.index:
            raise ValueError(f"Team data not available for {home_team} or {away_team}")
        
        home_stats = self.team_stats.loc[home_team]
        away_stats = self.team_stats.loc[away_team]
        
        # Apply injury adjustments if provided
        home_injury_factor = 1.0
        away_injury_factor = 1.0
        
        if injury_data:
            home_injury_factor = injury_data.get('home_injury_factor', 1.0)
            away_injury_factor = injury_data.get('away_injury_factor', 1.0)
        
        # Adjust stats based on injuries
        home_pts = home_stats['Avg_PTS'] * home_injury_factor
        away_pts = away_stats['Avg_PTS'] * away_injury_factor
        home_ast = home_stats['Avg_AST'] * home_injury_factor
        away_ast = away_stats['Avg_AST'] * away_injury_factor
        home_trb = home_stats['Avg_TRB'] * home_injury_factor
        away_trb = away_stats['Avg_TRB'] * away_injury_factor
        home_gmsc = home_stats['Avg_GmSc'] * home_injury_factor
        away_gmsc = away_stats['Avg_GmSc'] * away_injury_factor
        
        features = np.array([[
            home_pts,
            away_pts,
            home_ast,
            away_ast,
            home_trb,
            away_trb,
            home_stats['Avg_FG_Pct'],
            away_stats['Avg_FG_Pct'],
            home_stats['Avg_3P_Pct'],
            away_stats['Avg_3P_Pct'],
            home_stats['Win_Pct'],
            away_stats['Win_Pct'],
            home_gmsc,
            away_gmsc,
            home_pts - away_pts,
            home_stats['Win_Pct'] - away_stats['Win_Pct']
        ]])
        
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]
        
        winner = home_team if prediction == 1 else away_team
        confidence = probability[1] if prediction == 1 else probability[0]
        
        return {
            'winner': winner,
            'confidence': float(confidence),
            'home_win_prob': float(probability[1]),
            'away_win_prob': float(probability[0]),
            'home_injury_factor': home_injury_factor,
            'away_injury_factor': away_injury_factor
        }
    
    def save_model(self, filepath='nba_model.pkl'):
        """Save the trained model"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'team_stats': self.team_stats,
                'is_trained': self.is_trained
            }, f)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='nba_model.pkl'):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.team_stats = data['team_stats']
            self.is_trained = data['is_trained']
        print(f"Model loaded from {filepath}")

if __name__ == "__main__":
    # Train and save model
    predictor = NBAGamePredictor()
    df = predictor.load_data()
    accuracy = predictor.train(df)
    predictor.save_model()
    
    # Test prediction
    print("\nTesting prediction...")
    test_prediction = predictor.predict_game('BOS', 'LAL')
    print(f"Prediction: {test_prediction}")


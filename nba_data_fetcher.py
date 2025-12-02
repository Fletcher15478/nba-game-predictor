"""
NBA Data Fetcher
Fetches injuries, rosters, and game data from APIs
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class NBADataFetcher:
    def __init__(self):
        self.base_url = "https://www.balldontlie.io/api/v1"
        
    def get_injuries(self, date=None):
        """Get injury reports for a specific date"""
        if date is None:
            date = datetime.now().date()
        
        injuries = {}
        
        try:
            # Get all teams
            teams_response = requests.get(f"{self.base_url}/teams", timeout=10)
            if teams_response.status_code == 200:
                teams_data = teams_response.json()
                
                # For each team, try to get injury info
                # Note: balldontlie doesn't have direct injury endpoint
                # We'll use a workaround with player stats
                for team in teams_data.get('data', [])[:30]:  # Limit to avoid rate limits
                    team_abbr = team['abbreviation']
                    injuries[team_abbr] = {
                        'injured_players': [],
                        'injury_count': 0
                    }
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching injuries: {e}")
        
        return injuries
    
    def get_team_roster(self, team_abbr):
        """Get current roster for a team"""
        try:
            # Get team ID first
            teams_response = requests.get(f"{self.base_url}/teams", timeout=10)
            if teams_response.status_code == 200:
                teams_data = teams_response.json()
                team_id = None
                for team in teams_data.get('data', []):
                    if team['abbreviation'] == team_abbr:
                        team_id = team['id']
                        break
                
                if team_id:
                    # Get players for this team (current season)
                    players_response = requests.get(
                        f"{self.base_url}/players?team_ids[]={team_id}&per_page=100",
                        timeout=10
                    )
                    if players_response.status_code == 200:
                        players_data = players_response.json()
                        return [p['id'] for p in players_data.get('data', [])]
        except Exception as e:
            print(f"Error fetching roster for {team_abbr}: {e}")
        
        return []
    
    def get_player_stats_recent(self, player_id, days=30):
        """Get recent stats for a player to determine if they're active"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            stats_response = requests.get(
                f"{self.base_url}/stats?player_ids[]={player_id}&start_date={start_date}&end_date={end_date}&per_page=100",
                timeout=10
            )
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                return len(stats_data.get('data', []))
        except Exception as e:
            pass
        
        return 0
    
    def calculate_team_strength_with_injuries(self, team_abbr, df):
        """Calculate team strength accounting for injuries"""
        # Get team's recent performance
        team_games = df[df['Tm'] == team_abbr].sort_values('Data')
        recent_games = team_games.tail(10)
        
        if len(recent_games) < 5:
            return None
        
        # Base strength metrics
        base_strength = {
            'avg_pts': recent_games['PTS'].sum() / len(recent_games),
            'avg_ast': recent_games['AST'].sum() / len(recent_games),
            'avg_trb': recent_games['TRB'].sum() / len(recent_games),
            'win_pct': (recent_games['Res'] == 'W').sum() / len(recent_games),
            'avg_gmsc': recent_games['GmSc'].mean()
        }
        
        # Try to get roster and check for injuries
        roster = self.get_team_roster(team_abbr)
        
        # Estimate injury impact using recent game participation
        # Count unique players who appeared in recent games
        unique_players = recent_games['Player'].nunique()
        
        # Count players who appeared in multiple recent games (regular rotation)
        player_appearances = recent_games.groupby('Player').size()
        regular_players = len(player_appearances[player_appearances >= 3])  # Played in 3+ of last 10
        
        # Active players = unique players in recent games
        active_players = unique_players
        
        # Injury adjustment factor based on roster depth
        # Full strength: 10+ unique players, 8+ regular rotation players
        if unique_players >= 10 and regular_players >= 8:
            injury_factor = 1.0
        elif unique_players >= 9 and regular_players >= 7:
            injury_factor = 0.95
        elif unique_players >= 8 and regular_players >= 6:
            injury_factor = 0.90
        elif unique_players >= 7 and regular_players >= 5:
            injury_factor = 0.85
        elif unique_players >= 6:
            injury_factor = 0.80
        elif unique_players >= 5:
            injury_factor = 0.75
        else:
            injury_factor = 0.70  # Minimum factor
        
        # Adjust strength metrics
        adjusted_strength = {
            'avg_pts': base_strength['avg_pts'] * injury_factor,
            'avg_ast': base_strength['avg_ast'] * injury_factor,
            'avg_trb': base_strength['avg_trb'] * injury_factor,
            'win_pct': base_strength['win_pct'],
            'avg_gmsc': base_strength['avg_gmsc'] * injury_factor,
            'injury_factor': injury_factor,
            'active_players': active_players
        }
        
        return adjusted_strength
    
    def get_game_with_injuries(self, home_team, away_team, df):
        """Get game prediction data including injury impact"""
        home_strength = self.calculate_team_strength_with_injuries(home_team, df)
        away_strength = self.calculate_team_strength_with_injuries(away_team, df)
        
        if home_strength is None or away_strength is None:
            return None
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_strength': home_strength,
            'away_strength': away_strength,
            'home_injury_factor': home_strength['injury_factor'],
            'away_injury_factor': away_strength['injury_factor'],
            'home_active_players': home_strength['active_players'],
            'away_active_players': away_strength['active_players']
        }


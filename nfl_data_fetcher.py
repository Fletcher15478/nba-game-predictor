"""
NFL Data Fetcher
Fetches NFL data from ESPN API including games, rosters, injuries, and stats
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

class NFLDataFetcher:
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.team_abbr_map = {
            'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR',
            'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN',
            'DET': 'DET', 'GB': 'GB', 'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX',
            'KC': 'KC', 'LV': 'LV', 'LAC': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
            'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ',
            'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF', 'SEA': 'SEA', 'TB': 'TB',
            'TEN': 'TEN', 'WAS': 'WAS'
        }
    
    def get_week_games(self, week=None, season=2025):
        """Get all games for a specific week"""
        if week is None:
            # Get current week
            try:
                url = f"{self.base_url}/scoreboard"
                response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    data = response.json()
                    week = data.get('week', {}).get('number', 1)
            except:
                week = 1
        
        try:
            url = f"{self.base_url}/scoreboard?seasontype=2&week={week}"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                data = response.json()
                games = []
                for event in data.get('events', []):
                    competitions = event.get('competitions', [])
                    if competitions:
                        comp = competitions[0]
                        competitors = comp.get('competitors', [])
                        if len(competitors) == 2:
                            home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                            away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                            if home and away:
                                home_team = home.get('team', {}).get('abbreviation', '')
                                away_team = away.get('team', {}).get('abbreviation', '')
                                date_str = comp.get('date', '')
                                
                                games.append({
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'date': date_str[:10] if date_str else None,
                                    'week': week,
                                    'season': season
                                })
                return games
        except Exception as e:
            print(f"Error fetching week games: {e}")
        
        return []
    
    def get_team_stats(self, team_abbr, season=2025):
        """Get team statistics for the season"""
        try:
            # Get team ID first
            url = f"{self.base_url}/teams"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                data = response.json()
                team_id = None
                for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                    if team.get('team', {}).get('abbreviation') == team_abbr:
                        team_id = team.get('team', {}).get('id')
                        break
                
                if team_id:
                    # Get team stats
                    stats_url = f"{self.base_url}/teams/{team_id}/stats"
                    stats_response = requests.get(stats_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                    if stats_response.status_code == 200:
                        return stats_response.json()
        except Exception as e:
            print(f"Error fetching stats for {team_abbr}: {e}")
        
        return None
    
    def get_team_roster(self, team_abbr):
        """Get current roster for a team"""
        try:
            url = f"{self.base_url}/teams"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                data = response.json()
                team_id = None
                for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                    if team.get('team', {}).get('abbreviation') == team_abbr:
                        team_id = team.get('team', {}).get('id')
                        break
                
                if team_id:
                    roster_url = f"{self.base_url}/teams/{team_id}/roster"
                    roster_response = requests.get(roster_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                    if roster_response.status_code == 200:
                        roster_data = roster_response.json()
                        return roster_data.get('athletes', [])
        except Exception as e:
            print(f"Error fetching roster for {team_abbr}: {e}")
        
        return []
    
    def get_injuries(self, team_abbr=None):
        """Get injury reports"""
        try:
            url = f"{self.base_url}/injuries"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                data = response.json()
                injuries = {}
                for injury in data.get('injuries', []):
                    team = injury.get('team', {}).get('abbreviation', '')
                    if team_abbr is None or team == team_abbr:
                        if team not in injuries:
                            injuries[team] = []
                        injuries[team].append({
                            'player': injury.get('athlete', {}).get('displayName', ''),
                            'position': injury.get('position', {}).get('abbreviation', ''),
                            'status': injury.get('status', ''),
                            'injury': injury.get('injury', '')
                        })
                return injuries
        except Exception as e:
            print(f"Error fetching injuries: {e}")
        
        return {}
    
    def get_game_results(self, week=None, season=2025):
        """Get completed game results for a week"""
        games = self.get_week_games(week, season)
        results = []
        
        for game in games:
            try:
                # Get detailed game info
                date_str = game.get('date', '')
                if not date_str:
                    continue
                
                date_formatted = date_str.replace('-', '').replace('T', '').split('+')[0][:8]
                url = f"{self.base_url}/scoreboard?dates={date_formatted}"
                response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                
                if response.status_code == 200:
                    data = response.json()
                    for event in data.get('events', []):
                        competitions = event.get('competitions', [])
                        if competitions:
                            comp = competitions[0]
                            competitors = comp.get('competitors', [])
                            if len(competitors) == 2:
                                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                                
                                if home and away:
                                    home_team = home.get('team', {}).get('abbreviation', '')
                                    away_team = away.get('team', {}).get('abbreviation', '')
                                    
                                    if (home_team == game['home_team'] and away_team == game['away_team']) or \
                                       (home_team == game['away_team'] and away_team == game['home_team']):
                                        
                                        status = event.get('status', {}).get('type', {})
                                        if status.get('completed'):
                                            home_score = int(home.get('score', 0))
                                            away_score = int(away.get('score', 0))
                                            
                                            winner = home_team if home_score > away_score else away_team
                                            
                                            results.append({
                                                'home_team': game['home_team'],
                                                'away_team': game['away_team'],
                                                'home_score': home_score,
                                                'away_score': away_score,
                                                'winner': winner,
                                                'date': game['date'],
                                                'week': week
                                            })
                                            break
            except Exception as e:
                print(f"Error getting result for {game}: {e}")
                continue
        
        return results
    
    def get_historical_matchups(self, team1, team2, limit=5):
        """Get recent matchups between two teams"""
        # This would require historical data - for now return empty
        # In production, you'd query a historical database
        return []
    
    def get_venue_info(self, team_abbr):
        """Get venue information (indoor/outdoor)"""
        venue_map = {
            'ARI': 'indoor', 'ATL': 'indoor', 'BAL': 'outdoor', 'BUF': 'outdoor',
            'CAR': 'outdoor', 'CHI': 'outdoor', 'CIN': 'outdoor', 'CLE': 'outdoor',
            'DAL': 'indoor', 'DEN': 'outdoor', 'DET': 'indoor', 'GB': 'outdoor',
            'HOU': 'indoor', 'IND': 'indoor', 'JAX': 'outdoor', 'KC': 'outdoor',
            'LV': 'indoor', 'LAC': 'indoor', 'LAR': 'indoor', 'MIA': 'outdoor',
            'MIN': 'indoor', 'NE': 'outdoor', 'NO': 'indoor', 'NYG': 'outdoor',
            'NYJ': 'outdoor', 'PHI': 'outdoor', 'PIT': 'outdoor', 'SF': 'outdoor',
            'SEA': 'outdoor', 'TB': 'outdoor', 'TEN': 'outdoor', 'WAS': 'outdoor'
        }
        return venue_map.get(team_abbr, 'outdoor')


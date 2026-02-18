"""
Historical Data Fetcher
Fetches all NBA and NFL game data from Super Bowl (Feb 9, 2025) to All-Star period (Feb 16-18, 2025)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from nba_data_fetcher import NBADataFetcher
from nfl_data_fetcher import NFLDataFetcher

def fetch_nba_historical_data(start_date, end_date):
    """Fetch all NBA games from start_date to end_date"""
    print(f"\n=== Fetching NBA data from {start_date} to {end_date} ===")
    data_fetcher = NBADataFetcher()
    all_games = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Fetching NBA games for {date_str}...")
        
        try:
            # Try ESPN API first (more reliable)
            espn_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str.replace('-', '')}"
            response = requests.get(espn_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            
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
                                
                                status = event.get('status', {}).get('type', {})
                                is_completed = status.get('completed', False)
                                
                                home_score = int(home.get('score', 0)) if is_completed else None
                                away_score = int(away.get('score', 0)) if is_completed else None
                                
                                game_data = {
                                    'date': date_str,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'status': 'completed' if is_completed else 'scheduled',
                                    'home_score': home_score,
                                    'away_score': away_score
                                }
                                
                                if is_completed and home_score is not None and away_score is not None:
                                    game_data['winner'] = home_team if home_score > away_score else away_team
                                
                                all_games.append(game_data)
                                print(f"  Found: {away_team} @ {home_team} ({'Final' if is_completed else 'Scheduled'})")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error fetching {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    print(f"\nTotal NBA games fetched: {len(all_games)}")
    return all_games

def fetch_nfl_historical_data(start_date, end_date):
    """Fetch all NFL games from start_date to end_date"""
    print(f"\n=== Fetching NFL data from {start_date} to {end_date} ===")
    data_fetcher = NFLDataFetcher()
    all_games = []
    
    # NFL games are typically on specific days (Thu, Sun, Mon)
    # But we'll check every day in the range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_formatted = date_str.replace('-', '')
        
        print(f"Fetching NFL games for {date_str}...")
        
        try:
            # Try ESPN API
            espn_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_formatted}"
            response = requests.get(espn_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            
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
                                
                                status = event.get('status', {}).get('type', {})
                                is_completed = status.get('completed', False)
                                
                                home_score = int(home.get('score', 0)) if is_completed else None
                                away_score = int(away.get('score', 0)) if is_completed else None
                                
                                # Get week info
                                week_info = data.get('week', {})
                                week = week_info.get('number', None)
                                
                                game_data = {
                                    'date': date_str,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'status': 'completed' if is_completed else 'scheduled',
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'week': week
                                }
                                
                                if is_completed and home_score is not None and away_score is not None:
                                    game_data['winner'] = home_team if home_score > away_score else away_team
                                
                                all_games.append(game_data)
                                print(f"  Found: {away_team} @ {home_team} ({'Final' if is_completed else 'Scheduled'})")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error fetching {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    print(f"\nTotal NFL games fetched: {len(all_games)}")
    return all_games

def save_nba_data(games, filename='nba_historical_data.json'):
    """Save NBA games to JSON file"""
    with open(filename, 'w') as f:
        json.dump(games, f, indent=2)
    print(f"\nNBA data saved to {filename}")

def save_nfl_data(games, filename='nfl_historical_data.json'):
    """Save NFL games to JSON file"""
    with open(filename, 'w') as f:
        json.dump(games, f, indent=2)
    print(f"\nNFL data saved to {filename}")

def main():
    """Main function to fetch all historical data"""
    # Fetch from beginning of current year (Jan 1) to today
    today = datetime.now().date()
    start_date = datetime(today.year, 1, 1).date()
    end_date = today
    
    print("=" * 60)
    print("Historical Data Fetcher")
    print(f"Fetching data from {start_date} to {end_date}")
    print("=" * 60)
    
    # Fetch NBA data
    nba_games = fetch_nba_historical_data(start_date, end_date)
    if nba_games:
        save_nba_data(nba_games)
    
    # Fetch NFL data
    nfl_games = fetch_nfl_historical_data(start_date, end_date)
    if nfl_games:
        save_nfl_data(nfl_games)
    
    print("\n" + "=" * 60)
    print("Data fetching complete!")
    print(f"NBA games: {len(nba_games)}")
    print(f"NFL games: {len(nfl_games)}")
    print("=" * 60)

if __name__ == "__main__":
    main()

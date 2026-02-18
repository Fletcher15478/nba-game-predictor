"""
Backfill Historical Predictions
Generates predictions for every game in nba_historical_data.json and
nfl_historical_data.json (Jan 1 through today) so the Scores view can show
"Predicted: X" and Correct/Wrong for all past dates.
"""

import json
import os
from datetime import datetime

# NBA standard team abbreviations (exclude All-Star / special event teams)
NBA_TEAMS = {
    'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GS', 'GSW',
    'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NO', 'NOP', 'NY',
    'NYK', 'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SA', 'SAS', 'SEA', 'TOR',
    'UTAH', 'WAS', 'WSH'
}

# NFL standard team abbreviations
NFL_TEAMS = {
    'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET',
    'GB', 'HOU', 'IND', 'JAX', 'KC', 'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO',
    'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
}


def _nba_heuristic_predictions(games):
    """Build predictions from historical results: use win rate and avg score before each game date."""
    from collections import defaultdict
    completed = [g for g in games if g.get('status') == 'completed' and g.get('winner')]
    by_date = defaultdict(list)
    for g in completed:
        by_date[g['date']].append(g)
    dates_sorted = sorted(by_date.keys())
    predictions = []
    for g in games:
        home, away = g.get('home_team'), g.get('away_team')
        if home not in NBA_TEAMS or away not in NBA_TEAMS:
            continue
        game_date = g.get('date') or ''
        team_wins = defaultdict(int)
        team_games = defaultdict(int)
        team_pts = defaultdict(list)
        for d in dates_sorted:
            if d >= game_date:
                break
            for gm in by_date[d]:
                for t in (gm['home_team'], gm['away_team']):
                    team_games[t] += 1
                    team_pts[t].append(gm['home_score'] if t == gm['home_team'] else gm['away_score'])
                team_wins[gm['winner']] += 1
        wr_h = team_wins[home] / team_games[home] if team_games[home] else 0.5
        wr_a = team_wins[away] / team_games[away] if team_games[away] else 0.5
        avg_h = sum(team_pts[home]) / len(team_pts[home]) if team_pts[home] else 100
        avg_a = sum(team_pts[away]) / len(team_pts[away]) if team_pts[away] else 100
        if wr_h != wr_a:
            winner = home if wr_h > wr_a else away
            conf = 0.5 + abs(wr_h - wr_a)
        else:
            winner = home if avg_h >= avg_a else away
            conf = 0.55
        conf = min(0.92, max(0.52, conf))
        predictions.append({
            'home_team': home,
            'away_team': away,
            'date': game_date,
            'winner': winner,
            'confidence': conf,
            'home_win_prob': conf if winner == home else 1 - conf,
            'away_win_prob': 1 - conf if winner == home else conf,
        })
    return predictions


def backfill_nba():
    """Generate predictions for all games in nba_historical_data.json."""
    if not os.path.exists('nba_historical_data.json'):
        print("nba_historical_data.json not found. Run fetch_historical_data.py first.")
        return []

    with open('nba_historical_data.json', 'r') as f:
        games = json.load(f)

    predictions = []
    skipped = 0
    use_heuristic = False
    try:
        from ml_model import NBAGamePredictor
        predictor = NBAGamePredictor()
        predictor.load_model('nba_model.pkl')
    except Exception as e:
        print(f"NBA model not available ({e}). Using heuristic from historical data.")
        use_heuristic = True

    if use_heuristic:
        predictions = _nba_heuristic_predictions(games)
    else:
        for g in games:
            home, away = g.get('home_team'), g.get('away_team')
            if home not in NBA_TEAMS or away not in NBA_TEAMS:
                skipped += 1
                continue
            try:
                pred = predictor.predict_game(home, away, None)
                predictions.append({
                    'home_team': home,
                    'away_team': away,
                    'date': g.get('date'),
                    'winner': pred['winner'],
                    'confidence': pred['confidence'],
                    'home_win_prob': pred['home_win_prob'],
                    'away_win_prob': pred['away_win_prob'],
                })
            except Exception as e:
                skipped += 1
                continue

    out_path = 'nba_historical_predictions.json'
    with open(out_path, 'w') as f:
        json.dump(predictions, f, indent=2)
    print(f"NBA: Wrote {len(predictions)} predictions to {out_path} (skipped {skipped})")
    return predictions


def _nfl_heuristic_predictions(games):
    """Build predictions from historical results (date-aware)."""
    from collections import defaultdict
    completed = [g for g in games if g.get('status') == 'completed' and g.get('winner')]
    by_date = defaultdict(list)
    for g in completed:
        by_date[g['date']].append(g)
    dates_sorted = sorted(by_date.keys())
    predictions = []
    for g in games:
        home, away = g.get('home_team'), g.get('away_team')
        if home not in NFL_TEAMS or away not in NFL_TEAMS:
            continue
        game_date = g.get('date') or ''
        team_wins = defaultdict(int)
        team_games = defaultdict(int)
        team_pts = defaultdict(list)
        for d in dates_sorted:
            if d >= game_date:
                break
            for gm in by_date[d]:
                for t in (gm['home_team'], gm['away_team']):
                    team_games[t] += 1
                    team_pts[t].append(gm['home_score'] if t == gm['home_team'] else gm['away_score'])
                team_wins[gm['winner']] += 1
        wr_h = team_wins[home] / team_games[home] if team_games[home] else 0.5
        wr_a = team_wins[away] / team_games[away] if team_games[away] else 0.5
        avg_h = sum(team_pts[home]) / len(team_pts[home]) if team_pts[home] else 22
        avg_a = sum(team_pts[away]) / len(team_pts[away]) if team_pts[away] else 22
        if wr_h != wr_a:
            winner = home if wr_h > wr_a else away
            conf = 0.5 + abs(wr_h - wr_a)
        else:
            winner = home if avg_h >= avg_a else away
            conf = 0.55
        conf = min(0.92, max(0.52, conf))
        predictions.append({
            'home_team': home,
            'away_team': away,
            'date': game_date,
            'week': g.get('week'),
            'winner': winner,
            'confidence': conf,
            'home_win_prob': conf if winner == home else 1 - conf,
            'away_win_prob': 1 - conf if winner == home else conf,
        })
    return predictions


def backfill_nfl():
    """Generate predictions for all games in nfl_historical_data.json."""
    if not os.path.exists('nfl_historical_data.json'):
        print("nfl_historical_data.json not found. Run fetch_historical_data.py first.")
        return []

    with open('nfl_historical_data.json', 'r') as f:
        games = json.load(f)

    completed = [g for g in games if g.get('status') == 'completed' and g.get('home_score') is not None]
    if not completed:
        print("No completed NFL games in historical data.")
        return []

    predictions = []
    skipped = 0
    use_heuristic = False
    try:
        import pandas as pd
        from nfl_ml_model import NFLGamePredictor
        df_rows = [{'home_team': g['home_team'], 'away_team': g['away_team'], 'home_score': g['home_score'],
                    'away_score': g['away_score'], 'winner': g.get('winner'), 'week': g.get('week'), 'date': g.get('date')}
                   for g in completed]
        df_all = pd.DataFrame(df_rows).sort_values('date').reset_index(drop=True)
        predictor = NFLGamePredictor()
        predictor.load_model('nfl_model.pkl')
        for g in games:
            home, away = g.get('home_team'), g.get('away_team')
            if home not in NFL_TEAMS or away not in NFL_TEAMS:
                skipped += 1
                continue
            game_date = g.get('date')
            df_before = df_all[df_all['date'] < game_date] if game_date else df_all
            if len(df_before) == 0:
                df_before = df_all
            try:
                pred = predictor.predict(home, away, df_before, None)
                if pred:
                    predictions.append({
                        'home_team': home, 'away_team': away, 'date': game_date, 'week': g.get('week'),
                        'winner': pred['winner'], 'confidence': pred['confidence'],
                        'home_win_prob': pred['home_win_prob'], 'away_win_prob': pred['away_win_prob'],
                    })
                else:
                    skipped += 1
            except Exception:
                skipped += 1
    except Exception as e:
        print(f"NFL model not available ({e}). Using heuristic from historical data.")
        use_heuristic = True

    if use_heuristic:
        predictions = _nfl_heuristic_predictions(games)

    out_path = 'nfl_historical_predictions.json'
    with open(out_path, 'w') as f:
        json.dump(predictions, f, indent=2)
    print(f"NFL: Wrote {len(predictions)} predictions to {out_path} (skipped {skipped})")
    return predictions


def main():
    print("Backfilling historical predictions (Jan 1 – today)...")
    backfill_nba()
    backfill_nfl()
    print("Done.")


if __name__ == '__main__':
    main()

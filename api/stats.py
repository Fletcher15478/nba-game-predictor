"""
Vercel Serverless Function for Prediction Statistics
"""

from http.server import BaseHTTPRequestHandler
import json
import os

# In production, use a database or file to store stats
STATS_FILE = 'prediction_stats.json'

def load_stats():
    """Load statistics from file"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {
        'total_predictions': 0,
        'correct_predictions': 0,
        'accuracy': 0,
        'record': '0-0'
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            stats = load_stats()
            
            # Calculate accuracy
            if stats['total_predictions'] > 0:
                stats['accuracy'] = (stats['correct_predictions'] / stats['total_predictions']) * 100
            else:
                stats['accuracy'] = 0
            
            # Format record
            wins = stats['correct_predictions']
            losses = stats['total_predictions'] - stats['correct_predictions']
            stats['record'] = f"{wins}-{losses}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0,
                'record': '0-0'
            }).encode())


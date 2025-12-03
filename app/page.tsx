'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

interface Prediction {
  home_team: string
  away_team: string
  winner: string
  confidence: number
  home_win_prob: number
  away_win_prob: number
  date: string
}

interface BoxScore {
  home: {
    team: string
    abbreviation: string
    score: string
    record?: string
  }
  away: {
    team: string
    abbreviation: string
    score: string
    record?: string
  }
  status?: string
  date?: string
}

interface Stats {
  total_predictions: number
  correct_predictions: number
  accuracy: number
  record: string
}

export default function Home() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedGame, setSelectedGame] = useState<Prediction | null>(null)
  const [boxScore, setBoxScore] = useState<BoxScore | null>(null)
  const [loadingBoxScore, setLoadingBoxScore] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [league, setLeague] = useState<'nba' | 'nfl'>('nba')

  useEffect(() => {
    fetchData()
  }, [league])

  const fetchData = async (date?: string) => {
    try {
      setLoading(true)
      const dateToFetch = date || selectedDate
      const apiPath = league === 'nba' ? '/api/predictions' : '/api/nfl/predictions'
      const statsPath = league === 'nba' ? '/api/stats' : '/api/nfl/stats'
      
      const [predictionsRes, statsRes] = await Promise.all([
        axios.get(apiPath, { params: { date: dateToFetch } }),
        axios.get(statsPath)
      ])
      setPredictions(predictionsRes.data.predictions || [])
      setStats(statsRes.data)
      setSelectedDate(dateToFetch)
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const changeDate = (days: number) => {
    if (league === 'nfl') {
      // For NFL, navigate by week (simplified - just refresh current week)
      fetchData()
      return
    }
    
    const today = new Date().toISOString().split('T')[0]
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const yesterdayStr = yesterday.toISOString().split('T')[0]
    
    const currentDate = new Date(selectedDate + 'T00:00:00')
    currentDate.setDate(currentDate.getDate() + days)
    const newDate = currentDate.toISOString().split('T')[0]
    
    // Only allow today or yesterday
    if (newDate === today || newDate === yesterdayStr) {
      fetchData(newDate)
    }
  }

  const getConfidenceClass = (confidence: number) => {
    if (confidence >= 0.7) return 'high'
    if (confidence >= 0.55) return 'medium'
    return 'low'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString + 'T00:00:00') // Ensure correct date parsing
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  const fetchBoxScore = async (prediction: Prediction) => {
    setLoadingBoxScore(true)
    setSelectedGame(prediction)
    try {
      const apiPath = league === 'nba' ? '/api/boxscore' : '/api/nfl/boxscore'
      const response = await axios.get(apiPath, {
        params: {
          home: prediction.home_team,
          away: prediction.away_team,
          date: prediction.date
        }
      })
      setBoxScore(response.data)
    } catch (err: any) {
      console.error('Error fetching box score:', err)
      setBoxScore(null)
    } finally {
      setLoadingBoxScore(false)
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <p>Loading predictions...</p>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h1>{league === 'nba' ? '🏀 NBA' : '🏈 NFL'} Game Predictor</h1>
            <p>Machine Learning Powered Predictions</p>
          </div>
          <select 
            value={league} 
            onChange={(e) => setLeague(e.target.value as 'nba' | 'nfl')}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '1rem',
              borderRadius: '8px',
              border: '2px solid #667eea',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="nba">NBA</option>
            <option value="nfl">NFL</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Predictions</h3>
            <div className="value">{stats.total_predictions}</div>
          </div>
          <div className="stat-card">
            <h3>Correct Predictions</h3>
            <div className="value">{stats.correct_predictions}</div>
          </div>
          <div className="stat-card">
            <h3>Accuracy</h3>
            <div className="value">{stats.accuracy.toFixed(1)}%</div>
          </div>
          <div className="stat-card">
            <h3>Record</h3>
            <div className="value">{stats.record}</div>
          </div>
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <button 
            onClick={() => changeDate(-1)}
            style={{ 
              background: '#667eea', 
              color: 'white', 
              border: 'none', 
              padding: '0.5rem 1rem', 
              borderRadius: '8px', 
              cursor: 'pointer',
              fontSize: '1.2rem',
              fontWeight: 'bold'
            }}
          >
            ←
          </button>
          <h2 style={{ margin: 0, color: '#333', textAlign: 'center' }}>
            {league === 'nfl' 
              ? `Week ${predictions[0]?.week || 1} Predictions`
              : selectedDate === new Date().toISOString().split('T')[0] 
                ? "Today's Predictions" 
                : `Predictions: ${formatDate(selectedDate)}`}
          </h2>
          <button 
            onClick={() => changeDate(1)}
            disabled={selectedDate >= new Date().toISOString().split('T')[0]}
            style={{ 
              background: selectedDate >= new Date().toISOString().split('T')[0] ? '#ccc' : '#667eea', 
              color: 'white', 
              border: 'none', 
              padding: '0.5rem 1rem', 
              borderRadius: '8px', 
              cursor: selectedDate >= new Date().toISOString().split('T')[0] ? 'not-allowed' : 'pointer',
              fontSize: '1.2rem',
              fontWeight: 'bold'
            }}
          >
            →
          </button>
        </div>
        
        {predictions.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
            No games scheduled for today. Check back tomorrow!
          </p>
        ) : (
          <div className="predictions-grid">
            {predictions.map((pred, idx) => (
              <div
                key={idx}
                className={`prediction-card ${
                  pred.winner === pred.home_team ? 'winner' : ''
                }`}
                onClick={() => fetchBoxScore(pred)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
                  {formatDate(pred.date)}
                </div>
                
                <div style={{ marginBottom: '1rem' }}>
                  <div className="team-name" style={{ color: pred.winner === pred.home_team ? '#4caf50' : '#333' }}>
                    {pred.home_team} {pred.winner === pred.home_team && '🏆'}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666', marginLeft: '1rem' }}>
                    Win Probability: {(pred.home_win_prob * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div style={{ textAlign: 'center', margin: '1rem 0', color: '#999' }}>
                  vs
                </div>
                
                <div>
                  <div className="team-name" style={{ color: pred.winner === pred.away_team ? '#4caf50' : '#333' }}>
                    {pred.away_team} {pred.winner === pred.away_team && '🏆'}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666', marginLeft: '1rem' }}>
                    Win Probability: {(pred.away_win_prob * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div
                  className={`confidence ${getConfidenceClass(pred.confidence)}`}
                >
                  Confidence: {(pred.confidence * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedGame && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, color: '#333' }}>
              Box Score: {selectedGame.away_team} @ {selectedGame.home_team}
            </h2>
            <button 
              onClick={() => { setSelectedGame(null); setBoxScore(null); }}
              style={{ background: '#f44336', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
            >
              Close
            </button>
          </div>
          
          {loadingBoxScore ? (
            <p style={{ textAlign: 'center', padding: '2rem' }}>Loading box score...</p>
          ) : boxScore ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', marginBottom: '1rem', padding: '1rem', background: '#f5f5f5', borderRadius: '8px' }}>
                <div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{boxScore.away.team}</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#667eea' }}>{boxScore.away.score || '--'}</div>
                  {boxScore.away.record && <div style={{ fontSize: '0.9rem', color: '#666' }}>{boxScore.away.record}</div>}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>@</div>
                <div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{boxScore.home.team}</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#667eea' }}>{boxScore.home.score || '--'}</div>
                  {boxScore.home.record && <div style={{ fontSize: '0.9rem', color: '#666' }}>{boxScore.home.record}</div>}
                </div>
              </div>
              {boxScore.status && (
                <div style={{ color: '#666', fontSize: '0.9rem' }}>Status: {boxScore.status}</div>
              )}
              {!boxScore.away.score && !boxScore.home.score && (
                <p style={{ color: '#666', padding: '1rem' }}>Game hasn't started yet or box score not available.</p>
              )}
            </div>
          ) : (
            <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
              Box score not available for this game.
            </p>
          )}
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button className="btn" onClick={() => fetchData()}>
          Refresh Predictions
        </button>
      </div>
    </div>
  )
}


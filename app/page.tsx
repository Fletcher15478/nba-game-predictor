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

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [predictionsRes, statsRes] = await Promise.all([
        axios.get('/api/predictions'),
        axios.get('/api/stats')
      ])
      setPredictions(predictionsRes.data.predictions || [])
      setStats(statsRes.data)
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
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
        <h1>🏀 NBA Game Predictor</h1>
        <p>Machine Learning Powered Predictions</p>
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
        <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>
          Today's Predictions
        </h2>
        
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

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button className="btn" onClick={fetchData}>
          Refresh Predictions
        </button>
      </div>
    </div>
  )
}


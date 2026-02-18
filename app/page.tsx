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
  week?: number
  season?: number
  day?: string
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
  predictions_history?: Array<{
    home_team: string
    away_team: string
    week: number
    actual: string
    predicted: string
    correct: boolean
  }>
}

interface ResultGame {
  date: string
  home_team: string
  away_team: string
  status: string
  home_score: number | null
  away_score: number | null
  winner?: string
  week?: number | null
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
  const [currentWeek, setCurrentWeek] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'predictions' | 'results'>('predictions')
  const [results, setResults] = useState<ResultGame[]>([])
  const [resultsPredictions, setResultsPredictions] = useState<Prediction[]>([])

  useEffect(() => {
    if (viewMode === 'predictions') {
      fetchData()
    } else {
      fetchResults(selectedDate)
    }
  }, [league, viewMode])

  const fetchData = async (date?: string, week?: number) => {
    try {
      setLoading(true)
      const dateToFetch = date || selectedDate
      const apiPath = league === 'nba' ? '/api/predictions' : '/api/nfl/predictions'
      const statsPath = league === 'nba' ? '/api/stats' : '/api/nfl/stats'
      
      const params: any = {}
      if (league === 'nfl' && week) {
        params.week = week
      } else if (league === 'nba') {
        params.date = dateToFetch
      }
      
      const [predictionsRes, statsRes] = await Promise.all([
        axios.get(apiPath, { params }),
        axios.get(statsPath)
      ])
      const preds = predictionsRes.data.predictions || []
      setPredictions(preds)
      setStats(statsRes.data)
      setSelectedDate(dateToFetch)
      
      // Set current week for NFL
      if (league === 'nfl' && preds.length > 0 && preds[0].week) {
        setCurrentWeek(preds[0].week)
      } else if (league === 'nfl' && week) {
        setCurrentWeek(week)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const changeDate = (days: number) => {
    // Results mode: allow full navigation within current year
    if (viewMode === 'results') {
      const today = new Date()
      const currentYear = today.getFullYear()
      const minDate = new Date(`${currentYear}-01-01T00:00:00`)
      const maxDate = today

      const currentDate = new Date(selectedDate + 'T00:00:00')
      currentDate.setDate(currentDate.getDate() + days)

      if (currentDate < minDate || currentDate > maxDate) {
        return
      }

      const newDate = currentDate.toISOString().split('T')[0]
      setSelectedDate(newDate)
      fetchResults(newDate)
      return
    }

    if (league === 'nfl') {
      // For NFL, navigate by week
      const week = currentWeek || predictions[0]?.week || 14
      const newWeek = week + days
      if (newWeek >= 1 && newWeek <= 18) {
        fetchData(undefined, newWeek)
      }
      return
    }

    // NBA: allow full range Jan 1 – today (same as Scores)
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]
    const currentYear = today.getFullYear()
    const minDate = new Date(`${currentYear}-01-01T00:00:00`)

    const currentDate = new Date(selectedDate + 'T00:00:00')
    currentDate.setDate(currentDate.getDate() + days)
    const newDate = currentDate.toISOString().split('T')[0]

    if (currentDate < minDate || currentDate > today) {
      return
    }
    fetchData(newDate)
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

  const fetchResults = async (date: string) => {
    try {
      setLoading(true)
      setError(null)
      const historicalPath = league === 'nba' ? '/api/historical' : '/api/nfl/historical'
      const predictionsPath = league === 'nba' ? '/api/predictions' : '/api/nfl/predictions'
      const [gamesRes, predsRes] = await Promise.all([
        axios.get(historicalPath, { params: { date } }),
        axios.get(predictionsPath, { params: league === 'nfl' ? { date } : { date } })
      ])
      setResults(gamesRes.data.games || [])
      setResultsPredictions(predsRes.data.predictions || [])
      setSelectedDate(date)
    } catch (err: any) {
      setError(err.message || 'Failed to load results')
      setResults([])
      setResultsPredictions([])
    } finally {
      setLoading(false)
    }
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
            <h1>
              {league === 'nba' ? '🏀 NBA' : '🏈 NFL'}{' '}
              {viewMode === 'predictions' ? 'Game Predictor' : 'Scores'}
            </h1>
            <p>
              {viewMode === 'predictions'
                ? 'Machine Learning Powered Predictions'
                : 'Final scores and results'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
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
            <div style={{ display: 'flex', borderRadius: '999px', overflow: 'hidden', border: '1px solid #4b5563' }}>
              <button
                onClick={() => setViewMode('predictions')}
                style={{
                  padding: '0.35rem 0.85rem',
                  fontSize: '0.9rem',
                  border: 'none',
                  cursor: 'pointer',
                  background: viewMode === 'predictions' ? '#4f46e5' : 'transparent',
                  color: viewMode === 'predictions' ? '#fff' : '#e5e7eb'
                }}
              >
                Predictions
              </button>
              <button
                onClick={() => setViewMode('results')}
                style={{
                  padding: '0.35rem 0.85rem',
                  fontSize: '0.9rem',
                  border: 'none',
                  cursor: 'pointer',
                  background: viewMode === 'results' ? '#4f46e5' : 'transparent',
                  color: viewMode === 'results' ? '#fff' : '#e5e7eb'
                }}
              >
                Scores
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {viewMode === 'predictions' && stats && (
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
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ margin: 0, color: '#e2e8f0', fontSize: '1.8rem', fontWeight: '700' }}>
              {viewMode === 'predictions' ? (
                league === 'nfl' 
                  ? `Week ${currentWeek || predictions[0]?.week || 14} Predictions`
                  : selectedDate === new Date().toISOString().split('T')[0] 
                    ? "Today's Predictions" 
                    : `Predictions: ${formatDate(selectedDate)}`
              ) : (
                `Scores: ${formatDate(selectedDate)}`
              )}
            </h2>
            {(viewMode === 'results' || (viewMode === 'predictions' && league === 'nba')) && (
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => {
                  const d = e.target.value
                  if (viewMode === 'results') fetchResults(d)
                  else fetchData(d)
                }}
                max={new Date().toISOString().split('T')[0]}
                min={`${new Date().getFullYear()}-01-01`}
                style={{
                  marginTop: '0.5rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #4b5563',
                  background: '#020617',
                  color: '#e5e7eb'
                }}
              />
            )}
          </div>
          <button 
            onClick={() => changeDate(1)}
            disabled={
              viewMode === 'predictions'
                ? (league === 'nfl'
                    ? (currentWeek || predictions[0]?.week || 14) >= 18
                    : selectedDate >= new Date().toISOString().split('T')[0])
                : selectedDate >= new Date().toISOString().split('T')[0]
            }
            style={{ 
              background:
                viewMode === 'predictions'
                  ? (league === 'nfl'
                      ? (currentWeek || predictions[0]?.week || 14) >= 18
                      : selectedDate >= new Date().toISOString().split('T')[0])
                    ? '#ccc'
                    : '#667eea'
                  : selectedDate >= new Date().toISOString().split('T')[0]
                    ? '#ccc'
                    : '#667eea',
              color: 'white', 
              border: 'none', 
              padding: '0.5rem 1rem', 
              borderRadius: '8px', 
              cursor:
                viewMode === 'predictions'
                  ? (league === 'nfl'
                      ? (currentWeek || predictions[0]?.week || 14) >= 18
                      : selectedDate >= new Date().toISOString().split('T')[0])
                    ? 'not-allowed'
                    : 'pointer'
                  : selectedDate >= new Date().toISOString().split('T')[0]
                    ? 'not-allowed'
                    : 'pointer',
              fontSize: '1.2rem',
              fontWeight: 'bold'
            }}
          >
            →
          </button>
        </div>
        
        {viewMode === 'predictions' ? (
          predictions.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
              {selectedDate >= new Date().toISOString().split('T')[0]
                ? 'No games scheduled for today. Check back tomorrow!'
                : 'No predictions for this date.'}
            </p>
          ) : (
            <div className="predictions-grid">
            {predictions.map((pred, idx) => {
              const gameDate = pred.date ? new Date(pred.date + 'T00:00:00') : null
              const dayLabel = pred.day || (gameDate ? gameDate.toLocaleDateString('en-US', { weekday: 'long' }) : '')
              const isPast = gameDate ? gameDate < new Date() : false
              
              // Get actual winner from stats if past game
              let actualWinner = null
              if (isPast && stats && stats.predictions_history) {
                const result = stats.predictions_history.find((r: any) => 
                  r.home_team === pred.home_team && 
                  r.away_team === pred.away_team &&
                  r.week === pred.week
                )
                if (result) {
                  actualWinner = result.actual
                }
              }
              
              return (
              <div
                key={idx}
                className={`prediction-card ${
                  pred.winner === pred.home_team ? 'winner' : ''
                }`}
                onClick={() => fetchBoxScore(pred)}
                style={{ cursor: 'pointer' }}
              >
                {dayLabel && (
                  <div style={{ 
                    fontSize: '0.85rem', 
                    color: '#00d4ff', 
                    fontWeight: 'bold', 
                    marginBottom: '0.5rem',
                    textAlign: 'center',
                    textShadow: '0 0 10px rgba(0, 212, 255, 0.5)'
                  }}>
                    {dayLabel}
                  </div>
                )}
                <div style={{ marginBottom: '1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                  {formatDate(pred.date)}
                </div>
                
                {isPast && actualWinner && (
                  <div className="winner-badge">
                    Winner: {actualWinner} ✓
                  </div>
                )}
                
                <div style={{ marginBottom: '1rem' }}>
                  <div className="team-name" style={{ 
                    color: pred.winner === pred.home_team ? '#00d4ff' : '#e2e8f0',
                    textShadow: pred.winner === pred.home_team ? '0 0 15px rgba(0, 212, 255, 0.6)' : 'none'
                  }}>
                    {pred.home_team} {pred.winner === pred.home_team && '🏆'}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginLeft: '1rem', marginTop: '0.25rem' }}>
                    Win Probability: {(pred.home_win_prob * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div style={{ textAlign: 'center', margin: '1rem 0', color: '#64748b', fontSize: '0.9rem', fontWeight: '600' }}>
                  vs
                </div>
                
                <div>
                  <div className="team-name" style={{ 
                    color: pred.winner === pred.away_team ? '#00d4ff' : '#e2e8f0',
                    textShadow: pred.winner === pred.away_team ? '0 0 15px rgba(0, 212, 255, 0.6)' : 'none'
                  }}>
                    {pred.away_team} {pred.winner === pred.away_team && '🏆'}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginLeft: '1rem', marginTop: '0.25rem' }}>
                    Win Probability: {(pred.away_win_prob * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div
                  className={`confidence ${getConfidenceClass(pred.confidence)}`}
                >
                  {isPast ? 'Predicted' : 'Confidence'}: {(pred.confidence * 100).toFixed(1)}%
                </div>
              </div>
            )
            })}
            </div>
          )
        ) : (
          <>
            {results.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
                No games found for this date.
              </p>
            ) : (
              <div className="predictions-grid">
                {results.map((game, idx) => {
                  const isCompleted = game.status === 'completed' || game.home_score !== null || game.away_score !== null
                  const winnerLabel =
                    isCompleted && game.winner
                      ? `Winner: ${game.winner}`
                      : !isCompleted
                        ? 'Scheduled'
                        : 'Final'
                  const pred = resultsPredictions.find(
                    (p) =>
                      p.home_team === game.home_team && p.away_team === game.away_team
                  )
                  const predCorrect =
                    isCompleted &&
                    game.winner &&
                    pred &&
                    pred.winner === game.winner

                  return (
                    <div
                      key={idx}
                      className="prediction-card"
                      style={{ cursor: 'default' }}
                    >
                      <div style={{ marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.9rem', textAlign: 'center' }}>
                        {league === 'nfl' && game.week ? `Week ${game.week}` : formatDate(game.date)}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                        <div className="team-name" style={{ color: '#e2e8f0' }}>
                          {game.away_team}
                        </div>
                        <div style={{ fontWeight: 'bold', color: '#f97316' }}>
                          {game.away_score !== null ? game.away_score : '--'}
                        </div>
                      </div>
                      <div style={{ textAlign: 'center', margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem', fontWeight: '600' }}>
                        @
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                        <div className="team-name" style={{ color: '#e2e8f0' }}>
                          {game.home_team}
                        </div>
                        <div style={{ fontWeight: 'bold', color: '#22c55e' }}>
                          {game.home_score !== null ? game.home_score : '--'}
                        </div>
                      </div>
                      <div
                        style={{
                          marginTop: '0.5rem',
                          padding: '0.35rem 0.5rem',
                          borderRadius: '999px',
                          fontSize: '0.8rem',
                          textAlign: 'center',
                          background: '#020617',
                          color: '#e5e7eb',
                          border: '1px solid #1e293b'
                        }}
                      >
                        {winnerLabel}
                      </div>
                      {pred && (
                        <div
                          style={{
                            marginTop: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px',
                            fontSize: '0.85rem',
                            background: 'rgba(30, 41, 59, 0.8)',
                            border: '1px solid #334155',
                            color: '#cbd5e1'
                          }}
                        >
                          <div style={{ marginBottom: '0.25rem' }}>
                            Predicted: <strong>{pred.winner}</strong>{' '}
                            ({(pred.confidence * 100).toFixed(0)}%)
                          </div>
                          {isCompleted && game.winner && (
                            <div
                              style={{
                                fontWeight: '600',
                                color: predCorrect ? '#22c55e' : '#ef4444'
                              }}
                            >
                              {predCorrect ? '✓ Correct' : '✗ Wrong'}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>

      {viewMode === 'predictions' && selectedGame && (
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

      {viewMode === 'predictions' && (
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button className="btn" onClick={() => fetchData()}>
            Refresh Predictions
          </button>
        </div>
      )}
    </div>
  )
}


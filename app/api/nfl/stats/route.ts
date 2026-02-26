import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cwd = process.cwd()
    const predPath = path.join(cwd, 'nfl_historical_predictions.json')
    const gamesPath = path.join(cwd, 'nfl_historical_data.json')

    if (fs.existsSync(predPath) && fs.existsSync(gamesPath)) {
      const preds: Array<{ date: string; home_team: string; away_team: string; winner: string; week?: number }> = JSON.parse(
        fs.readFileSync(predPath, 'utf8')
      )
      const games: Array<{ date: string; home_team: string; away_team: string; winner?: string; status?: string }> = JSON.parse(
        fs.readFileSync(gamesPath, 'utf8')
      )
      const completedByKey = new Map<string, { winner: string }>()
      for (const g of games) {
        if (g.status === 'completed' && g.winner) {
          const key = `${g.date}:${g.home_team}:${g.away_team}`
          completedByKey.set(key, { winner: g.winner })
        }
      }

      let total = 0
      let correct = 0
      const predictions_history: Array<{ date: string; home_team: string; away_team: string; week?: number; actual: string; predicted: string; correct: boolean }> = []

      for (const p of preds) {
        const key = `${p.date}:${p.home_team}:${p.away_team}`
        const result = completedByKey.get(key)
        if (result) {
          total += 1
          const isCorrect = p.winner === result.winner
          if (isCorrect) correct += 1
          predictions_history.push({
            date: p.date,
            home_team: p.home_team,
            away_team: p.away_team,
            week: p.week,
            actual: result.winner,
            predicted: p.winner,
            correct: isCorrect
          })
        }
      }

      const accuracy = total > 0 ? (correct / total) * 100 : 0
      const losses = total - correct

      return NextResponse.json({
        total_predictions: total,
        correct_predictions: correct,
        accuracy,
        record: `${correct}-${losses}`,
        predictions_history
      })
    }

    // Fallback to stored stats if historical files missing
    const filePath = path.join(cwd, 'nfl_prediction_stats.json')
    if (fs.existsSync(filePath)) {
      const stats = JSON.parse(fs.readFileSync(filePath, 'utf8'))
      const total = stats.total_predictions || 0
      const correct = stats.correct_predictions || 0
      const accuracy = total > 0 ? (correct / total) * 100 : 0
      return NextResponse.json({
        total_predictions: total,
        correct_predictions: correct,
        accuracy,
        record: `${correct}-${total - correct}`,
        predictions_history: stats.predictions_history || []
      })
    }

    return NextResponse.json({
      total_predictions: 0,
      correct_predictions: 0,
      accuracy: 0,
      record: '0-0',
      predictions_history: []
    })
  } catch (error) {
    console.error('Error reading NFL stats:', error)
    return NextResponse.json({
      total_predictions: 0,
      correct_predictions: 0,
      accuracy: 0,
      record: '0-0',
      predictions_history: []
    })
  }
}


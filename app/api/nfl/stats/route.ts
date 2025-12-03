import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'nfl_prediction_stats.json')
    
    if (fs.existsSync(filePath)) {
      const fileData = fs.readFileSync(filePath, 'utf8')
      const stats = JSON.parse(fileData)
      
      // Calculate accuracy
      const total = stats.total_predictions || 0
      const correct = stats.correct_predictions || 0
      const accuracy = total > 0 ? (correct / total) * 100 : 0
      
      return NextResponse.json({
        total_predictions: total,
        correct_predictions: correct,
        accuracy: accuracy,
        record: `${correct}-${total - correct}`
      })
    }
    
    // Return default stats if file doesn't exist
    return NextResponse.json({
      total_predictions: 0,
      correct_predictions: 0,
      accuracy: 0,
      record: '0-0'
    })
  } catch (error) {
    console.error('Error reading NFL stats:', error)
    return NextResponse.json({
      total_predictions: 0,
      correct_predictions: 0,
      accuracy: 0,
      record: '0-0'
    })
  }
}


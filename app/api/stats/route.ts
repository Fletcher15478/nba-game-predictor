import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // Read stats from the JSON file
    const filePath = path.join(process.cwd(), 'prediction_stats.json')
    
    if (fs.existsSync(filePath)) {
      const fileData = fs.readFileSync(filePath, 'utf8')
      const stats = JSON.parse(fileData)
      
      // Calculate accuracy and record
      const total = stats.total_predictions || 0
      const correct = stats.correct_predictions || 0
      const accuracy = total > 0 ? (correct / total) * 100 : 0
      const wins = correct
      const losses = total - correct
      
      return NextResponse.json({
        total_predictions: total,
        correct_predictions: correct,
        accuracy: accuracy,
        record: `${wins}-${losses}`
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
    console.error('Error reading stats:', error)
    return NextResponse.json({
      total_predictions: 0,
      correct_predictions: 0,
      accuracy: 0,
      record: '0-0'
    })
  }
}


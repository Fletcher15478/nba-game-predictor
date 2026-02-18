import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const requestedDate = searchParams.get('date')

    if (!requestedDate) {
      return NextResponse.json(
        { games: [], message: 'Missing date parameter' },
        { status: 400 }
      )
    }

    const filePath = path.join(process.cwd(), 'nfl_historical_data.json')

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({
        games: [],
        message: 'No NFL historical data available. Run: python3 fetch_historical_data.py'
      })
    }

    const fileData = fs.readFileSync(filePath, 'utf8')
    const allGames = JSON.parse(fileData)

    const gamesForDate = allGames.filter((g: any) => g.date === requestedDate)

    // Sort by week then by matchup
    gamesForDate.sort((a: any, b: any) => {
      const weekA = a.week || 0
      const weekB = b.week || 0
      if (weekA !== weekB) return weekA - weekB
      const aKey = `${a.home_team}-${a.away_team}`
      const bKey = `${b.home_team}-${b.away_team}`
      return aKey.localeCompare(bKey)
    })

    return NextResponse.json({ games: gamesForDate })
  } catch (error) {
    console.error('Error reading NFL historical data:', error)
    return NextResponse.json({
      games: [],
      message: 'Unable to fetch NFL historical data at this time'
    })
  }
}


import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const homeTeam = searchParams.get('home')
  const awayTeam = searchParams.get('away')
  const date = searchParams.get('date')

  if (!homeTeam || !awayTeam || !date) {
    return NextResponse.json({ error: 'Missing parameters' }, { status: 400 })
  }

  try {
    // Try ESPN API for NFL box score
    const dateFormatted = date.replace(/-/g, '')
    const espnUrl = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=${dateFormatted}`
    
    const response = await fetch(espnUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      cache: 'no-store'
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch box score')
    }
    
    const data = await response.json()
    
    // Find the specific game
    for (const event of data.events || []) {
      const competitions = event.competitions || []
      if (competitions.length > 0) {
        const comp = competitions[0]
        const competitors = comp.competitors || []
        
        if (competitors.length === 2) {
          const home = competitors.find((c: any) => c.homeAway === 'home')
          const away = competitors.find((c: any) => c.homeAway === 'away')
          
          if (home && away) {
            const homeAbbr = home.team?.abbreviation
            const awayAbbr = away.team?.abbreviation
            
            // Check if this is the game we're looking for
            if ((homeAbbr === homeTeam && awayAbbr === awayTeam) ||
                (homeAbbr === awayTeam && awayAbbr === homeTeam)) {
              
              // Get box score data
              const boxscoreUrl = event.links?.find((l: any) => l.rel?.includes('boxscore'))?.href
              
              if (boxscoreUrl) {
                const boxResponse = await fetch(boxscoreUrl, {
                  headers: { 'User-Agent': 'Mozilla/5.0' }
                })
                
                if (boxResponse.ok) {
                  const boxData = await boxResponse.json()
                  return NextResponse.json(boxData)
                }
              }
              
              // Return basic game info if box score not available
              return NextResponse.json({
                home: {
                  team: home.team?.displayName,
                  abbreviation: homeAbbr,
                  score: home.score,
                  record: home.records?.[0]?.summary
                },
                away: {
                  team: away.team?.displayName,
                  abbreviation: awayAbbr,
                  score: away.score,
                  record: away.records?.[0]?.summary
                },
                status: event.status?.type?.description,
                date: event.date
              })
            }
          }
        }
      }
    }
    
    return NextResponse.json({ error: 'Game not found' }, { status: 404 })
  } catch (error: any) {
    console.error('NFL Box score error:', error)
    return NextResponse.json({ 
      error: 'Failed to fetch box score',
      message: error.message 
    }, { status: 500 })
  }
}


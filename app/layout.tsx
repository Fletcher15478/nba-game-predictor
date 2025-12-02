import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NBA Game Predictor | ML-Powered Predictions',
  description: 'Machine learning powered NBA game predictions with daily accuracy tracking',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}


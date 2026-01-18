import type React from "react"
import type { Metadata, Viewport } from "next"
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ErrorHandler } from "@/components/error-handler"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" })
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-nav" })

export const metadata: Metadata = {
  title: "LOGOSYN | Operator-Grade Decision Infrastructure",
  description:
    "Turn incomplete, conflicting telemetry into defensible action—evidence lineage, trust scoring, contradictions, and compliance posture generated at the moment you act.",
}

export const viewport: Viewport = {
  themeColor: "#07080B",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} ${spaceGrotesk.variable}`}>
      <body className="font-sans antialiased">
        <ErrorHandler />
        {children}
        <Analytics />
      </body>
    </html>
  )
}

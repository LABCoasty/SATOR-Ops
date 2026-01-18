import type React from "react"
import type { Metadata, Viewport } from "next"
import { Inter, JetBrains_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ErrorHandler } from "@/components/error-handler"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" })

export const metadata: Metadata = {
  title: "SATOR-Ops | Decisions You Can Defend",
  description:
    "Transform unreliable data into structured decisions with evidence, trust scoring, and audit-ready artifacts.",
}

export const viewport: Viewport = {
  themeColor: "#1a1a1f",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        <ErrorHandler />
        {children}
        <Analytics />
      </body>
    </html>
  )
}

"use client"

import { useEffect } from "react"

/**
 * Global error handler to suppress browser extension errors
 * and improve WebSocket error handling
 */
export function ErrorHandler() {
  useEffect(() => {
    // Suppress browser extension connection errors
    const originalError = console.error
    console.error = (...args: any[]) => {
      const message = args.join(" ")
      
      // Suppress known browser extension errors
      if (
        message.includes("Could not establish connection") ||
        message.includes("Receiving end does not exist") ||
        message.includes("Extension context invalidated")
      ) {
        // Silently ignore browser extension errors
        return
      }
      
      // Log other errors normally
      originalError.apply(console, args)
    }

    // Handle unhandled promise rejections
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason?.toString() || ""
      
      // Suppress browser extension related promise rejections
      if (
        reason.includes("Could not establish connection") ||
        reason.includes("Receiving end does not exist") ||
        reason.includes("Extension context invalidated")
      ) {
        event.preventDefault()
        return
      }
    }

    // Handle WebSocket errors gracefully
    const handleError = (event: ErrorEvent) => {
      const message = event.message || ""
      
      // Suppress browser extension errors
      if (
        message.includes("Could not establish connection") ||
        message.includes("Receiving end does not exist")
      ) {
        event.preventDefault()
        return
      }
    }

    window.addEventListener("unhandledrejection", handleUnhandledRejection)
    window.addEventListener("error", handleError)

    return () => {
      console.error = originalError
      window.removeEventListener("unhandledrejection", handleUnhandledRejection)
      window.removeEventListener("error", handleError)
    }
  }, [])

  return null
}

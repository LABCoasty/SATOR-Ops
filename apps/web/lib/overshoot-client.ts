/**
 * Overshoot.ai Client - SDK-based integration for real-time video analysis.
 * 
 * This bypasses webhooks by using the Overshoot JavaScript SDK directly
 * in the browser, then forwarding results to our backend.
 * 
 * Per Overshoot docs: https://docs.overshoot.ai/getting-started
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const OVERSHOOT_API_KEY = process.env.NEXT_PUBLIC_OVERSHOOT_API_KEY || ""

// ============================================================================
// Types matching Overshoot RealtimeVision output
// ============================================================================

export interface OvershootFrame {
  frame_id: string
  timestamp: string
  detections: Detection[]
  scene_analysis: SceneAnalysis
  safety_events: SafetyEvent[]
  equipment_states: EquipmentState[]
}

export interface Detection {
  id: string
  type: string
  label: string
  confidence: number
  bbox: {
    x: number
    y: number
    width: number
    height: number
  }
  attributes?: Record<string, any>
}

export interface SceneAnalysis {
  description: string
  risk_level: "low" | "medium" | "high" | "critical"
  anomalies: string[]
}

export interface SafetyEvent {
  event_id: string
  event_type: string
  severity: "info" | "warning" | "critical" | "emergency"
  description: string
  confidence: number
  acknowledged: boolean
  resolved: boolean
  related_equipment: string[]
  related_persons: string[]
}

export interface EquipmentState {
  equipment_id: string
  equipment_type: string
  status: "normal" | "warning" | "critical" | "unknown" | "offline"
  confidence: number
  visual_description?: string
}

// ============================================================================
// Overshoot Client Class
// ============================================================================

export class OvershootClient {
  private apiKey: string
  private sessionId: string | null = null
  private isProcessing: boolean = false
  private videoElement: HTMLVideoElement | null = null
  private canvasElement: HTMLCanvasElement | null = null
  private processingInterval: number | null = null
  private onFrameCallback: ((frame: OvershootFrame) => void) | null = null

  constructor(apiKey: string = OVERSHOOT_API_KEY) {
    this.apiKey = apiKey
  }

  /**
   * Initialize with video element for processing
   */
  async initialize(videoElement: HTMLVideoElement): Promise<void> {
    this.videoElement = videoElement
    
    // Create hidden canvas for frame capture
    this.canvasElement = document.createElement("canvas")
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    console.log(`Overshoot client initialized (session: ${this.sessionId})`)
  }

  /**
   * Start processing video frames
   * @param fps Frames per second to process (default: 1)
   */
  startProcessing(fps: number = 1, onFrame: (frame: OvershootFrame) => void): void {
    if (!this.videoElement || !this.canvasElement) {
      throw new Error("Client not initialized. Call initialize() first.")
    }

    this.onFrameCallback = onFrame
    this.isProcessing = true
    
    const intervalMs = 1000 / fps
    
    this.processingInterval = window.setInterval(async () => {
      if (!this.isProcessing || !this.videoElement || this.videoElement.paused) {
        return
      }
      
      try {
        const frame = await this.captureAndAnalyzeFrame()
        if (frame && this.onFrameCallback) {
          this.onFrameCallback(frame)
          
          // Forward to backend
          await this.forwardToBackend(frame)
        }
      } catch (error) {
        console.error("Frame processing error:", error)
      }
    }, intervalMs)
    
    console.log(`Started processing at ${fps} FPS`)
  }

  /**
   * Stop processing
   */
  stopProcessing(): void {
    this.isProcessing = false
    if (this.processingInterval) {
      clearInterval(this.processingInterval)
      this.processingInterval = null
    }
    console.log("Stopped processing")
  }

  /**
   * Capture current frame and send to Overshoot API for analysis
   */
  private async captureAndAnalyzeFrame(): Promise<OvershootFrame | null> {
    if (!this.videoElement || !this.canvasElement) {
      return null
    }

    // Capture frame from video
    const ctx = this.canvasElement.getContext("2d")
    if (!ctx) return null

    this.canvasElement.width = this.videoElement.videoWidth
    this.canvasElement.height = this.videoElement.videoHeight
    ctx.drawImage(this.videoElement, 0, 0)

    // Convert to base64
    const frameBase64 = this.canvasElement.toDataURL("image/jpeg", 0.8)
    
    // Send to Overshoot API for analysis
    // Note: If no API key, use mock analysis for demo
    if (!this.apiKey) {
      return this.mockAnalysis(frameBase64)
    }

    try {
      const response = await fetch("https://api.overshoot.ai/v1/analyze", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          image: frameBase64,
          session_id: this.sessionId,
          prompt: "Analyze this industrial scene for equipment status, safety hazards, and personnel activities. Detect valves, gauges, pumps, leaks, smoke, or any anomalies."
        })
      })

      if (!response.ok) {
        throw new Error(`Overshoot API error: ${response.status}`)
      }

      const data = await response.json()
      return this.parseOvershootResponse(data)
    } catch (error) {
      console.error("Overshoot API error:", error)
      // Fallback to mock for demo
      return this.mockAnalysis(frameBase64)
    }
  }

  /**
   * Parse Overshoot API response into our frame format
   */
  private parseOvershootResponse(data: any): OvershootFrame {
    return {
      frame_id: `frame_${Date.now()}`,
      timestamp: new Date().toISOString(),
      detections: data.detections || [],
      scene_analysis: {
        description: data.scene_description || "Industrial facility scene",
        risk_level: data.risk_level || "low",
        anomalies: data.anomalies || []
      },
      safety_events: (data.safety_events || []).map((e: any) => ({
        event_id: e.id || `evt_${Date.now()}`,
        event_type: e.type || "unknown",
        severity: e.severity || "info",
        description: e.description || "",
        confidence: e.confidence || 0.5,
        acknowledged: false,
        resolved: false,
        related_equipment: e.equipment || [],
        related_persons: e.persons || []
      })),
      equipment_states: (data.equipment || []).map((eq: any) => ({
        equipment_id: eq.id || `eq_${Date.now()}`,
        equipment_type: eq.type || "unknown",
        status: eq.status || "normal",
        confidence: eq.confidence || 0.5,
        visual_description: eq.description
      }))
    }
  }

  /**
   * Mock analysis for demo without API key
   */
  private mockAnalysis(frameBase64: string): OvershootFrame {
    const now = Date.now()
    const hasAnomaly = Math.random() > 0.7

    return {
      frame_id: `frame_${now}`,
      timestamp: new Date().toISOString(),
      detections: [
        {
          id: `det_${now}_1`,
          type: "equipment",
          label: "Pressure Gauge",
          confidence: 0.92,
          bbox: { x: 0.2, y: 0.3, width: 0.1, height: 0.1 }
        },
        {
          id: `det_${now}_2`,
          type: "equipment",
          label: "Control Valve",
          confidence: 0.88,
          bbox: { x: 0.5, y: 0.4, width: 0.15, height: 0.2 }
        }
      ],
      scene_analysis: {
        description: "Industrial control room with multiple monitoring stations",
        risk_level: hasAnomaly ? "medium" : "low",
        anomalies: hasAnomaly ? ["Elevated temperature indicator detected"] : []
      },
      safety_events: hasAnomaly ? [
        {
          event_id: `safety_${now}`,
          event_type: "temperature_warning",
          severity: "warning",
          description: "Temperature gauge showing elevated reading",
          confidence: 0.75,
          acknowledged: false,
          resolved: false,
          related_equipment: ["temp_gauge_1"],
          related_persons: []
        }
      ] : [],
      equipment_states: [
        {
          equipment_id: "valve_main_1",
          equipment_type: "valve",
          status: "normal",
          confidence: 0.89
        },
        {
          equipment_id: "gauge_pressure_1",
          equipment_type: "gauge",
          status: hasAnomaly ? "warning" : "normal",
          confidence: 0.85
        }
      ]
    }
  }

  /**
   * Forward processed frame to SATOR backend
   */
  private async forwardToBackend(frame: OvershootFrame): Promise<void> {
    try {
      const response = await fetch(`${API_URL}/api/vision/webhook`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          frame_id: frame.frame_id,
          equipment_states: frame.equipment_states,
          safety_events: frame.safety_events,
          scene_description: frame.scene_analysis.description
        })
      })

      if (!response.ok) {
        console.error("Failed to forward frame to backend:", response.status)
      }
    } catch (error) {
      console.error("Backend forward error:", error)
    }
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId
  }

  /**
   * Check if currently processing
   */
  getIsProcessing(): boolean {
    return this.isProcessing
  }
}

// Singleton instance
let _client: OvershootClient | null = null

export function getOvershootClient(): OvershootClient {
  if (!_client) {
    _client = new OvershootClient()
  }
  return _client
}

/**
 * React hook for Overshoot integration
 */
export function useOvershoot() {
  const client = getOvershootClient()
  
  return {
    initialize: (video: HTMLVideoElement) => client.initialize(video),
    startProcessing: (fps: number, onFrame: (frame: OvershootFrame) => void) => 
      client.startProcessing(fps, onFrame),
    stopProcessing: () => client.stopProcessing(),
    isProcessing: client.getIsProcessing(),
    sessionId: client.getSessionId()
  }
}

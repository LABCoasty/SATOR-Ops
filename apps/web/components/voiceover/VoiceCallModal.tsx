'use client';

import { Phone, PhoneOff, Mic, MicOff, Volume2 } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

interface VoiceCallModalProps {
    context?: {
        currentPage: string;
        incidentId?: string;
        trustScore?: number;
        trustState?: string;
        contradictions?: string[];
        posture?: string;
    };
    onClose: () => void;
}

type CallStatus = 'connecting' | 'connected' | 'ended' | 'error';

export default function VoiceCallModal({ context, onClose }: VoiceCallModalProps) {
    const [status, setStatus] = useState<CallStatus>('connecting');
    const [isMuted, setIsMuted] = useState(false);
    const [duration, setDuration] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // Simulate connection (replace with actual LiveKit connection)
    useEffect(() => {
        const connectTimeout = setTimeout(() => {
            // TODO: Replace with actual LiveKit room connection
            // For now, simulate connection
            setStatus('connected');
        }, 2000);

        return () => clearTimeout(connectTimeout);
    }, []);

    // Call duration timer
    useEffect(() => {
        if (status !== 'connected') return;

        const timer = setInterval(() => {
            setDuration((prev) => prev + 1);
        }, 1000);

        return () => clearInterval(timer);
    }, [status]);

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleEndCall = useCallback(() => {
        setStatus('ended');
        setTimeout(onClose, 1000);
    }, [onClose]);

    const toggleMute = () => {
        setIsMuted((prev) => !prev);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                {/* Header */}
                <div className="modal-header">
                    <div className="status-indicator">
                        {status === 'connecting' && <span className="pulse" />}
                        {status === 'connected' && <Volume2 className="w-5 h-5 text-green-400" />}
                    </div>
                    <div className="status-text">
                        {status === 'connecting' && 'Calling Supervisor...'}
                        {status === 'connected' && 'Connected to Supervisor'}
                        {status === 'ended' && 'Call Ended'}
                        {status === 'error' && 'Connection Failed'}
                    </div>
                    {status === 'connected' && (
                        <div className="duration">{formatDuration(duration)}</div>
                    )}
                </div>

                {/* Context Display */}
                {context && status === 'connected' && (
                    <div className="context-display">
                        <div className="context-item">
                            <span className="context-label">Page:</span>
                            <span className="context-value">{context.currentPage}</span>
                        </div>
                        {context.incidentId && (
                            <div className="context-item">
                                <span className="context-label">Incident:</span>
                                <span className="context-value">{context.incidentId}</span>
                            </div>
                        )}
                        {context.trustState && (
                            <div className="context-item">
                                <span className="context-label">Trust:</span>
                                <span className={`context-value trust-${context.trustState}`}>
                                    {context.trustState} ({context.trustScore?.toFixed(2)})
                                </span>
                            </div>
                        )}
                    </div>
                )}

                {/* Audio Visualization Placeholder */}
                {status === 'connected' && (
                    <div className="audio-visual">
                        <div className="wave" />
                        <div className="wave" style={{ animationDelay: '0.2s' }} />
                        <div className="wave" style={{ animationDelay: '0.4s' }} />
                        <div className="wave" style={{ animationDelay: '0.6s' }} />
                        <div className="wave" style={{ animationDelay: '0.8s' }} />
                    </div>
                )}

                {/* Controls */}
                <div className="controls">
                    {status === 'connected' && (
                        <button
                            onClick={toggleMute}
                            className={`control-btn ${isMuted ? 'muted' : ''}`}
                            aria-label={isMuted ? 'Unmute' : 'Mute'}
                        >
                            {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                        </button>
                    )}

                    <button
                        onClick={handleEndCall}
                        className="control-btn end-call"
                        aria-label="End Call"
                    >
                        <PhoneOff className="w-6 h-6" />
                    </button>
                </div>

                {/* Error Display */}
                {error && <div className="error-message">{error}</div>}
            </div>

            <style jsx>{`
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: linear-gradient(180deg, #1e293b, #0f172a);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 24px;
          width: 100%;
          max-width: 360px;
          box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        }

        .modal-header {
          text-align: center;
          margin-bottom: 20px;
        }

        .status-indicator {
          display: flex;
          justify-content: center;
          margin-bottom: 12px;
        }

        .pulse {
          width: 20px;
          height: 20px;
          background: #22c55e;
          border-radius: 50%;
          animation: pulse 1.5s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
        }

        .status-text {
          font-size: 18px;
          font-weight: 600;
          color: white;
        }

        .duration {
          font-size: 14px;
          color: #94a3b8;
          margin-top: 4px;
        }

        .context-display {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 20px;
        }

        .context-item {
          display: flex;
          justify-content: space-between;
          font-size: 13px;
          padding: 4px 0;
        }

        .context-label {
          color: #64748b;
        }

        .context-value {
          color: #e2e8f0;
        }

        .trust-degraded { color: #f59e0b; }
        .trust-untrusted { color: #ef4444; }
        .trust-quarantined { color: #dc2626; }
        .trust-trusted { color: #22c55e; }

        .audio-visual {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 4px;
          height: 60px;
          margin-bottom: 20px;
        }

        .wave {
          width: 4px;
          height: 20px;
          background: #3b82f6;
          border-radius: 2px;
          animation: wave 1s ease-in-out infinite;
        }

        @keyframes wave {
          0%, 100% { height: 20px; }
          50% { height: 40px; }
        }

        .controls {
          display: flex;
          justify-content: center;
          gap: 16px;
        }

        .control-btn {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }

        .control-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .control-btn.muted {
          background: #ef4444;
        }

        .control-btn.end-call {
          background: #ef4444;
        }

        .control-btn.end-call:hover {
          background: #dc2626;
        }

        .error-message {
          text-align: center;
          color: #ef4444;
          font-size: 14px;
          margin-top: 12px;
        }
      `}</style>
        </div>
    );
}

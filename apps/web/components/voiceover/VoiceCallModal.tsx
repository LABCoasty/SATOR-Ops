'use client';

import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  DisconnectButton,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { useCallback, useState } from 'react';
import { Phone, PhoneOff, Loader2 } from 'lucide-react';

interface VoiceCallModalProps {
  onClose: () => void;
  context?: {
    currentPage?: string;
    incidentId?: string;
    trustScore?: number;
    trustState?: string;
  };
}

// Agent component that renders inside LiveKitRoom
function VoiceAgent() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="voice-agent-container">
      <div className="agent-status">
        {state === 'connecting' && <span>🔄 Connecting to Supervisor...</span>}
        {state === 'listening' && <span>🎤 Listening...</span>}
        {state === 'thinking' && <span>🤔 Processing...</span>}
        {state === 'speaking' && <span>🔊 Supervisor speaking...</span>}
      </div>

      <div className="visualizer-container">
        <BarVisualizer
          state={state}
          barCount={5}
          trackRef={audioTrack}
          className="agent-visualizer"
        />
      </div>

      <VoiceAssistantControlBar controls={{ leave: false }} />

      <style jsx>{`
        .voice-agent-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }
        .agent-status {
          font-size: 16px;
          color: #e2e8f0;
        }
        .visualizer-container {
          width: 200px;
          height: 100px;
        }
      `}</style>
    </div>
  );
}

export default function VoiceCallModal({ onClose, context }: VoiceCallModalProps) {
  const [token, setToken] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get LiveKit URL from environment
  const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'wss://sator-voice-7zhq4b09.livekit.cloud';

  // Request a token to join the agent room
  const startCall = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // Request token from our backend
      const response = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roomName: `supervisor-${Date.now()}`,
          participantName: 'operator',
          context: context,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get access token');
      }

      const data = await response.json();
      setToken(data.token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  }, [context]);

  const handleDisconnect = useCallback(() => {
    setToken(null);
    onClose();
  }, [onClose]);

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>📞 Supervisor Call</h2>
          {context?.incidentId && (
            <span className="incident-badge">{context.incidentId}</span>
          )}
        </div>

        {!token ? (
          // Pre-call screen
          <div className="pre-call">
            {error && <div className="error">{error}</div>}

            <p>Connect with an AI supervisor for guidance on your current situation.</p>

            {context && (
              <div className="context-preview">
                <div>Page: {context.currentPage}</div>
                {context.trustState && (
                  <div>Trust: {context.trustState} ({context.trustScore?.toFixed(2)})</div>
                )}
              </div>
            )}

            <button
              onClick={startCall}
              disabled={isConnecting}
              className="start-call-btn"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Phone className="w-5 h-5" />
                  Start Call
                </>
              )}
            </button>

            <button onClick={onClose} className="cancel-btn">
              Cancel
            </button>
          </div>
        ) : (
          // Active call screen
          <LiveKitRoom
            token={token}
            serverUrl={livekitUrl}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={handleDisconnect}
            className="livekit-room"
          >
            <VoiceAgent />
            <RoomAudioRenderer />

            <DisconnectButton className="end-call-btn">
              <PhoneOff className="w-5 h-5" />
              End Call
            </DisconnectButton>
          </LiveKitRoom>
        )}
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.8);
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
          max-width: 400px;
          box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        }
        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .modal-header h2 {
          font-size: 18px;
          color: white;
          margin: 0;
        }
        .incident-badge {
          background: #3b82f6;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
        .pre-call {
          display: flex;
          flex-direction: column;
          gap: 16px;
          text-align: center;
        }
        .pre-call p {
          color: #94a3b8;
          font-size: 14px;
        }
        .context-preview {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 12px;
          font-size: 13px;
          color: #e2e8f0;
          text-align: left;
        }
        .error {
          background: rgba(239, 68, 68, 0.2);
          border: 1px solid #ef4444;
          border-radius: 8px;
          padding: 12px;
          color: #ef4444;
          font-size: 14px;
        }
        .start-call-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 24px;
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .start-call-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #16a34a, #15803d);
        }
        .start-call-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .cancel-btn {
          background: transparent;
          color: #94a3b8;
          border: none;
          cursor: pointer;
          font-size: 14px;
        }
        .cancel-btn:hover {
          color: white;
        }
        :global(.livekit-room) {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }
        :global(.end-call-btn) {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: #ef4444;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          cursor: pointer;
        }
        :global(.end-call-btn:hover) {
          background: #dc2626;
        }
        :global(.agent-visualizer) {
          --lk-bar-color: #3b82f6;
        }
      `}</style>
    </div>
  );
}

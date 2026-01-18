'use client';

import { Phone } from 'lucide-react';
import { useState } from 'react';
import VoiceCallModal from './VoiceCallModal';

interface CallSupervisorButtonProps {
    context?: {
        currentPage: string;
        incidentId?: string;
        trustScore?: number;
        trustState?: string;
        contradictions?: string[];
        posture?: string;
    };
}

export default function CallSupervisorButton({ context }: CallSupervisorButtonProps) {
    const [isCallActive, setIsCallActive] = useState(false);

    const handleStartCall = () => {
        setIsCallActive(true);
    };

    const handleEndCall = () => {
        setIsCallActive(false);
    };

    return (
        <>
            <button
                onClick={handleStartCall}
                className="call-supervisor-btn"
                aria-label="Call Supervisor for Help"
            >
                <Phone className="w-4 h-4" />
                <span>Call Supervisor</span>
            </button>

            {isCallActive && (
                <VoiceCallModal
                    context={context}
                    onClose={handleEndCall}
                />
            )}

            <style jsx>{`
        .call-supervisor-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }

        .call-supervisor-btn:hover {
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
          transform: translateY(-1px);
        }

        .call-supervisor-btn:active {
          transform: translateY(0);
        }
      `}</style>
        </>
    );
}

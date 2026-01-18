'use client';

import { useState, useCallback, useEffect } from 'react';

/**
 * Hook to manage LiveKit voice call connection
 * TODO: Replace with actual LiveKit SDK integration when credentials are available
 */

interface VoiceCallState {
    status: 'idle' | 'connecting' | 'connected' | 'error' | 'ended';
    error: string | null;
    isMuted: boolean;
    duration: number;
}

interface VoiceCallActions {
    connect: (roomName: string, context?: Record<string, unknown>) => Promise<void>;
    disconnect: () => void;
    toggleMute: () => void;
}

export function useVoiceCall(): [VoiceCallState, VoiceCallActions] {
    const [state, setState] = useState<VoiceCallState>({
        status: 'idle',
        error: null,
        isMuted: false,
        duration: 0,
    });

    // Duration timer
    useEffect(() => {
        if (state.status !== 'connected') return;

        const timer = setInterval(() => {
            setState((prev) => ({ ...prev, duration: prev.duration + 1 }));
        }, 1000);

        return () => clearInterval(timer);
    }, [state.status]);

    const connect = useCallback(async (roomName: string, context?: Record<string, unknown>) => {
        setState((prev) => ({ ...prev, status: 'connecting', error: null }));

        try {
            // TODO: Implement actual LiveKit connection
            // const room = new Room();
            // await room.connect(LIVEKIT_URL, token);

            // Simulated connection for now
            await new Promise((resolve) => setTimeout(resolve, 2000));

            setState((prev) => ({ ...prev, status: 'connected', duration: 0 }));
        } catch (err) {
            setState((prev) => ({
                ...prev,
                status: 'error',
                error: err instanceof Error ? err.message : 'Connection failed',
            }));
        }
    }, []);

    const disconnect = useCallback(() => {
        // TODO: Disconnect from LiveKit room
        setState((prev) => ({ ...prev, status: 'ended' }));
    }, []);

    const toggleMute = useCallback(() => {
        setState((prev) => ({ ...prev, isMuted: !prev.isMuted }));
        // TODO: Actually mute/unmute the audio track
    }, []);

    return [state, { connect, disconnect, toggleMute }];
}

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
import { Phone, PhoneOff, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface VoiceCallModalProps {
  onClose: () => void;
  context?: {
    currentPage?: string;
    incidentId?: string;
    trustScore?: number;
    trustState?: string;
    scenarioName?: string;
  };
}

// Agent component that renders inside LiveKitRoom
function VoiceAgent() {
  const { state, audioTrack } = useVoiceAssistant();

  const getStatusText = () => {
    switch (state) {
      case 'connecting':
        return 'Connecting to Supervisor...';
      case 'listening':
        return 'Listening...';
      case 'thinking':
        return 'Processing...';
      case 'speaking':
        return 'Supervisor speaking...';
      default:
        return 'Ready';
    }
  };

  const getStatusIcon = () => {
    switch (state) {
      case 'connecting':
        return '🔄';
      case 'listening':
        return '🎤';
      case 'thinking':
        return '🤔';
      case 'speaking':
        return '🔊';
      default:
        return '📞';
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 py-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>{getStatusIcon()}</span>
        <span>{getStatusText()}</span>
      </div>

      <div className="w-[200px] h-[100px] flex items-center justify-center">
        <BarVisualizer
          state={state}
          barCount={5}
          trackRef={audioTrack}
          className="[&_.lk-bar]:bg-primary"
        />
      </div>

      <VoiceAssistantControlBar controls={{ leave: false }} />
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
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md" showCloseButton={false}>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <Phone className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle>Supervisor Call</DialogTitle>
                {context?.incidentId && (
                  <Badge variant="secondary" className="mt-1 text-xs">
                    {context.incidentId}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        {!token ? (
          // Pre-call screen
          <div className="space-y-4">
            {error && (
              <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <DialogDescription className="text-center">
              Connect with an AI supervisor for guidance on your current situation.
            </DialogDescription>

            {context && (
              <Card>
                <CardContent className="pt-6">
                  {/* Supervisor Avatar */}
                  <div className="flex justify-center mb-4">
                    <div className="h-35 w-35 rounded-full overflow-hidden border-2 border-primary/30 shadow-lg">
                      <img
                        src="/morgan.jpg"
                        alt="Supervisor"
                        className="h-full w-full object-cover"
                      />
                    </div>
                  </div>
                  <div className="space-y-3 text-base">
                    {context.scenarioName && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Scenario:</span>
                        <span className="font-semibold">{context.scenarioName}</span>
                      </div>
                    )}
                    {context.trustState && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Trust:</span>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              context.trustState === 'high'
                                ? 'default'
                                : context.trustState === 'medium'
                                  ? 'secondary'
                                  : 'destructive'
                            }
                            className={cn(
                              "text-sm",
                              context.trustState === 'high' && "bg-green-500 hover:bg-green-600",
                              context.trustState === 'medium' && "bg-yellow-500 hover:bg-yellow-600 text-black",
                              context.trustState === 'low' && "bg-red-500 hover:bg-red-600"
                            )}
                          >
                            {context.trustState}
                          </Badge>
                          <span className={cn(
                            "font-mono text-sm font-semibold",
                            context.trustState === 'high' && "text-green-500",
                            context.trustState === 'medium' && "text-yellow-500",
                            context.trustState === 'low' && "text-red-500"
                          )}>
                            {context.trustScore?.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex flex-col gap-2">
              <Button
                onClick={startCall}
                disabled={isConnecting}
                className="w-full gap-2"
                size="lg"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Phone className="h-5 w-5" />
                    Start Call
                  </>
                )}
              </Button>

              <Button
                variant="ghost"
                onClick={onClose}
                className="w-full"
                disabled={isConnecting}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          // Active call screen
          <div className="space-y-4">
            <LiveKitRoom
              token={token}
              serverUrl={livekitUrl}
              connect={true}
              audio={true}
              video={false}
              onDisconnected={handleDisconnect}
            >
              <Card>
                <CardContent className="pt-6">
                  <VoiceAgent />
                  <RoomAudioRenderer />
                </CardContent>
                <div className="border-t border-border p-4">
                  <DisconnectButton>
                    <Button
                      variant="destructive"
                      className="w-full gap-2"
                      onClick={handleDisconnect}
                    >
                      <PhoneOff className="h-4 w-4" />
                      End Call
                    </Button>
                  </DisconnectButton>
                </div>
              </Card>
            </LiveKitRoom>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

import { AccessToken, RoomServiceClient, AgentDispatchClient } from 'livekit-server-sdk';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { roomName, participantName, context } = body;

        // Get credentials from environment
        const apiKey = process.env.LIVEKIT_API_KEY;
        const apiSecret = process.env.LIVEKIT_API_SECRET;
        const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'wss://sator-voice-7zhq4b09.livekit.cloud';

        if (!apiKey || !apiSecret) {
            return NextResponse.json(
                { error: 'LiveKit credentials not configured' },
                { status: 500 }
            );
        }

        // Convert wss:// to https:// for API calls
        const httpUrl = livekitUrl.replace('wss://', 'https://');

        // Create the room first
        const roomService = new RoomServiceClient(httpUrl, apiKey, apiSecret);
        try {
            await roomService.createRoom({
                name: roomName,
                emptyTimeout: 60 * 5, // 5 minutes
                maxParticipants: 2,
            });
        } catch (e) {
            // Room might already exist, that's okay
            console.log('Room may already exist:', e);
        }

        // Dispatch the agent to this room
        const agentDispatch = new AgentDispatchClient(httpUrl, apiKey, apiSecret);
        try {
            await agentDispatch.createDispatch(roomName, 'Morgan-5a9', {
                metadata: context ? JSON.stringify(context) : undefined,
            });
            console.log('Agent dispatched to room:', roomName);
        } catch (e) {
            console.error('Agent dispatch error:', e);
            // Continue anyway - agent might auto-join
        }

        // Create access token for the operator
        const at = new AccessToken(apiKey, apiSecret, {
            identity: participantName || 'operator',
            name: participantName || 'Operator',
            ttl: '1h',
        });

        // Grant permissions to join room
        at.addGrant({
            room: roomName,
            roomJoin: true,
            canPublish: true,
            canPublishData: true,
            canSubscribe: true,
        });

        // Add context as metadata if provided
        if (context) {
            at.metadata = JSON.stringify(context);
        }

        const token = await at.toJwt();

        return NextResponse.json({ token, roomName });
    } catch (error) {
        console.error('Error generating token:', error);
        return NextResponse.json(
            { error: 'Failed to generate token' },
            { status: 500 }
        );
    }
}

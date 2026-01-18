import { AccessToken } from 'livekit-server-sdk';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { roomName, participantName, context } = body;

        // Get credentials from environment
        const apiKey = process.env.LIVEKIT_API_KEY;
        const apiSecret = process.env.LIVEKIT_API_SECRET;

        if (!apiKey || !apiSecret) {
            return NextResponse.json(
                { error: 'LiveKit credentials not configured' },
                { status: 500 }
            );
        }

        // Create access token
        const at = new AccessToken(apiKey, apiSecret, {
            identity: participantName || 'operator',
            name: participantName || 'Operator',
            // Token expires in 1 hour
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

        return NextResponse.json({ token });
    } catch (error) {
        console.error('Error generating token:', error);
        return NextResponse.json(
            { error: 'Failed to generate token' },
            { status: 500 }
        );
    }
}

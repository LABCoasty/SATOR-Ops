# SATOR Virtual Supervisor - Voice Call Integration

AI-powered virtual supervisor that operators can call for real-time voice guidance.

## How It Works

1. Operator clicks **"Call Supervisor"** on the Decision page
2. Voice modal opens and connects to LiveKit Cloud
3. AI supervisor (Morgan-5a9) joins and speaks with the operator
4. Conversation continues until operator ends the call

## Architecture

```
Frontend (Next.js)              LiveKit Cloud
┌─────────────────────┐         ┌─────────────────────┐
│ CallSupervisorButton│         │ Agent: Morgan-5a9   │
│ VoiceCallModal      │ ──────► │ STT → LLM → TTS     │
│ Token API           │         │ Voice Generation    │
└─────────────────────┘         └─────────────────────┘
```

## Components

### Frontend (`apps/web/components/voiceover/`)
- `CallSupervisorButton.tsx` - Button to start voice call
- `VoiceCallModal.tsx` - Modal with LiveKit room connection
- `index.ts` - Exports

### API (`apps/web/app/api/livekit/`)
- `token/route.ts` - Generates access tokens and dispatches agent

### LiveKit Cloud
- Agent deployed at: `cloud.livekit.io`
- Agent name: `Morgan-5a9`
- Agent ID: `CA_mxXPX9scMcCn`

## Environment Variables

Required in `apps/web/.env.local`:
```env
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
NEXT_PUBLIC_LIVEKIT_URL=wss://sator-voice-xxx.livekit.cloud
```

## Dependencies

```bash
pnpm add @livekit/components-react @livekit/components-styles livekit-client livekit-server-sdk
```

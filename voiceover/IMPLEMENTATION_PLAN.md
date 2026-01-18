# SATOR Virtual Supervisor - Voice Call Implementation

## What This Is
When an operator clicks **"Call Supervisor for Help"**, they get connected to an **AI-generated virtual supervisor** that:
- Speaks with a professional voice (LiveKit voice generation)
- Understands the current dashboard context
- Provides supervisor-level guidance via real-time voice conversation
- **NOT a real person** - fully AI-powered using **LiveKit Agents API only**

---

## User Experience

```
[ 📞 Call Supervisor for Help ] → Click

┌─────────────────────────────────────────────────────┐
│ 🎙️ Connected to Supervisor                         │
│                                                      │
│ 🔊 "Hello, this is Supervisor Control. I see        │
│    you're looking at incident INC-2024-001 with     │
│    a degraded trust state. How can I help?"         │
│                                                      │
│ 🎤 [Speaking...] or [Tap to speak]                  │
│                                                      │
│ [ 🔇 Mute ]        [ 📴 End Call ]                  │
└─────────────────────────────────────────────────────┘
```

---

## Architecture (LiveKit Only)

```
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                             │
│  CallSupervisorButton → VoiceCallModal → LiveKit Room           │
│                              ↓                                   │
│                    Audio In/Out + Context Packet                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                   LIVEKIT AGENTS (Python)                        │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │           LIVEKIT VOICE PIPELINE                         │   │
│   │                                                           │   │
│   │   Operator Audio ──► STT ──► LLM ──► TTS ──► Voice Out   │   │
│   │                  (All via LiveKit API)                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Supervisor Persona + Dashboard Context Injection               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Required Credentials (LiveKit Only)

```env
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud
```

---

## File Structure

```
voiceover/
├── IMPLEMENTATION_PLAN.md
├── supervisor_agent.py      ← LiveKit Agent
├── prompts.py               ← Supervisor persona
└── requirements.txt

apps/web/components/voiceover/
├── CallSupervisorButton.tsx
├── VoiceCallModal.tsx
└── useVoiceCall.ts
```

---

## Implementation Phases

### Phase 1: Basic Voice Call ← NOW
- [x] Create folder structure
- [ ] Backend: LiveKit Agent with supervisor persona
- [ ] Frontend: Call button + modal
- [ ] Connect and test basic voice conversation

### Phase 2: Context-Aware
- [ ] Inject dashboard context on call start
- [ ] Supervisor acknowledges current situation

### Phase 3: Polish
- [ ] Call duration limits
- [ ] Feedback after call
